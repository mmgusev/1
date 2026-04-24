"""
Flask web application for shop_demo database management.
Provides login, table viewing, row insertion, and row updating via web UI.
Failed login attempts are logged to a file.
All DB queries use parameterised statements; column/table names are
validated against a whitelist to prevent SQL injection.
"""

import logging
import os
from datetime import datetime

import psycopg2
import psycopg2.extras
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from whitelist import get_allowed_columns

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# ---------------------------------------------------------------------------
# Logging – failed login attempts
# ---------------------------------------------------------------------------
LOG_FILE = os.environ.get("DUPLICATE_LOG_FILE", "/var/log/shop_app.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(levelname)s  %(message)s")
)

logger = logging.getLogger("shop_app")
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
# Also echo to stdout so Docker logs pick it up
logger.addHandler(logging.StreamHandler())

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "shop_demo")

ALLOWED = get_allowed_columns()  # {table: [col, ...]}


def _get_conn(user: str, password: str):
    """Open a new psycopg2 connection with the supplied credentials."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=user,
        password=password,
        connect_timeout=5,
    )


def get_conn():
    """Return a connection using credentials stored in the session."""
    return _get_conn(session["db_user"], session["db_pass"])


def _safe_table(table: str) -> str:
    """Raise ValueError if *table* is not in the whitelist."""
    if table not in ALLOWED:
        raise ValueError(f"Unknown table: {table!r}")
    return table


def _safe_columns(table: str, columns: list[str]) -> list[str]:
    """Return only whitelisted column names for *table*."""
    allowed = ALLOWED[table]
    return [c for c in columns if c in allowed]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def logged_in() -> bool:
    return "db_user" in session and "db_pass" in session


def require_login():
    if not logged_in():
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return None


# ---------------------------------------------------------------------------
# Routes – authentication
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if logged_in():
        return redirect(url_for("index"))

    if request.method == "POST":
        db_user = request.form.get("db_user", "").strip()
        db_pass = request.form.get("db_pass", "")

        if not db_user:
            flash("Username is required.", "danger")
            return render_template("login.html")

        try:
            conn = _get_conn(db_user, db_pass)
            conn.close()
        except psycopg2.OperationalError as exc:
            logger.warning(
                "Failed login attempt | user=%r | ip=%s | reason=%s",
                db_user,
                request.remote_addr,
                str(exc).splitlines()[0],
            )
            flash("Invalid credentials or database unreachable.", "danger")
            return render_template("login.html")

        session["db_user"] = db_user
        session["db_pass"] = db_pass
        flash(f"Welcome, {db_user}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes – main page
# ---------------------------------------------------------------------------
@app.route("/main")
def index():
    redir = require_login()
    if redir:
        return redir
    tables = list(ALLOWED.keys())
    return render_template("index.html", tables=tables, user=session["db_user"])


# ---------------------------------------------------------------------------
# Routes – view tables
# ---------------------------------------------------------------------------
@app.route("/view", methods=["GET"])
def view():
    redir = require_login()
    if redir:
        return redir

    table = request.args.get("table", "products")
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    # Optional filter controls
    filter_col = request.args.get("filter_col", "").strip()
    filter_op  = request.args.get("filter_op", "eq").strip()
    filter_val = request.args.get("filter_val", "").strip()

    allowed_cols = ALLOWED[table]

    # Table and column names come from the whitelist – safe to interpolate with
    # double-quote quoting.  All *values* are always passed via %s placeholders.
    col_list = ", ".join(f'"{c}"' for c in allowed_cols)
    sql = f'SELECT {col_list} FROM "{table}"'
    params: list = []

    op_map = {
        "eq":   "=",
        "ne":   "!=",
        "lt":   "<",
        "le":   "<=",
        "gt":   ">",
        "ge":   ">=",
        "like": "ILIKE",
        "in":   "IN",   # group of values: "1, 2, 3"  →  IN (%s, %s, %s)
    }

    if filter_col and filter_col in allowed_cols and filter_val and filter_op in op_map:
        if filter_op == "in":
            # ----------------------------------------------------------------
            # SAFE handling of a group of homogeneous values (req. 7).
            # The user supplies a comma-separated list, e.g. "1, 2, 3".
            # We split it into individual values and generate one %s
            # placeholder per value.  The list is then passed as the params
            # tuple so psycopg2 binds each value independently – no string
            # interpolation of user data ever touches the SQL text.
            # ----------------------------------------------------------------
            in_values = [v.strip() for v in filter_val.split(",") if v.strip()]
            if in_values:
                placeholders = ", ".join(["%s"] * len(in_values))
                sql += f' WHERE "{filter_col}" IN ({placeholders})'
                params.extend(in_values)
        else:
            sql += f' WHERE "{filter_col}" {op_map[filter_op]} %s'
            params.append(filter_val)

    sql += ' ORDER BY "id" LIMIT 500'

    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or None)
        rows = cur.fetchall()
        conn.close()
    except Exception as exc:
        flash(f"Query error: {exc}", "danger")
        rows = []

    return render_template(
        "view.html",
        table=table,
        tables=list(ALLOWED.keys()),
        columns=allowed_cols,
        rows=rows,
        filter_col=filter_col,
        filter_op=filter_op,
        filter_val=filter_val,
        op_map=op_map,
    )


# ---------------------------------------------------------------------------
# Routes – add rows
# ---------------------------------------------------------------------------
@app.route("/add", methods=["GET", "POST"])
def add():
    redir = require_login()
    if redir:
        return redir

    table = request.args.get("table") or request.form.get("table") or "products"
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    allowed_cols = [c for c in ALLOWED[table] if c != "id"]  # skip PK

    if request.method == "POST":
        # Collect only whitelisted columns from the form
        data = {
            col: request.form.get(col, "").strip()
            for col in allowed_cols
            if request.form.get(col, "").strip() != ""
        }

        if not data:
            flash("No data provided.", "warning")
        else:
            # Column names come from whitelist – safe to interpolate
            cols_sql = ", ".join(f'"{k}"' for k in data)
            placeholders = ", ".join(["%s"] * len(data))
            sql = f'INSERT INTO "{table}" ({cols_sql}) VALUES ({placeholders})'
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(sql, list(data.values()))
                conn.commit()
                conn.close()
                flash("Row added successfully.", "success")
                return redirect(url_for("add", table=table))
            except Exception as exc:
                flash(f"Insert error: {exc}", "danger")

    return render_template(
        "add.html",
        table=table,
        tables=list(ALLOWED.keys()),
        columns=allowed_cols,
    )


# ---------------------------------------------------------------------------
# Routes – update rows
# ---------------------------------------------------------------------------
@app.route("/update", methods=["GET", "POST"])
def update():
    redir = require_login()
    if redir:
        return redir

    table = request.args.get("table") or request.form.get("table") or "products"
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    allowed_cols = ALLOWED[table]
    editable_cols = [c for c in allowed_cols if c != "id"]

    row_id = request.args.get("id") or request.form.get("row_id")
    row = None

    # ---- Load existing row for editing ----
    if row_id:
        try:
            conn = get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f'SELECT * FROM "{table}" WHERE id = %s', (row_id,))
            row = cur.fetchone()
            conn.close()
        except Exception as exc:
            flash(f"Fetch error: {exc}", "danger")

    # ---- Handle form submission ----
    if request.method == "POST" and request.form.get("row_id"):
        data = {
            col: request.form.get(col, "").strip()
            for col in editable_cols
            if request.form.get(col) is not None
        }
        # Remove empty strings so we don't overwrite with blank
        data = {k: v for k, v in data.items() if v != ""}

        if not data:
            flash("Nothing to update.", "warning")
        else:
            # SET clause: column names from whitelist – safe to interpolate
            set_clause = ", ".join(f'"{k}" = %s' for k in data)
            sql = f'UPDATE "{table}" SET {set_clause} WHERE id = %s'
            params = list(data.values()) + [row_id]
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(sql, params)
                conn.commit()
                conn.close()
                flash("Row updated successfully.", "success")
                return redirect(url_for("update", table=table, id=row_id))
            except Exception as exc:
                flash(f"Update error: {exc}", "danger")

    # ---- List rows for selection ----
    rows = []
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f'SELECT id FROM "{table}" ORDER BY id LIMIT 200')
        rows = cur.fetchall()
        conn.close()
    except Exception as exc:
        flash(f"List error: {exc}", "danger")

    return render_template(
        "update.html",
        table=table,
        tables=list(ALLOWED.keys()),
        editable_cols=editable_cols,
        rows=rows,
        row=row,
        row_id=row_id,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
