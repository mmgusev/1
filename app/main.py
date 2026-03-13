import getpass
import os
import sys
import traceback
from typing import Any, Iterable

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_values

from whitelist import get_allowed_columns


_ALLOWED: dict[str, list[str]] = get_allowed_columns()
_ALLOWED_TABLES: list[str] = sorted(_ALLOWED.keys())


def _duplicate_log_path() -> str | None:
    p = (os.getenv("DUPLICATE_LOG_FILE") or "").strip()
    return p or None


def _dup_write_raw(text: str) -> None:
    path = _duplicate_log_path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    except Exception:
        # Never crash the app because of logging duplication.
        pass


def _user_info(msg: str) -> None:
    print(msg, file=sys.stdout)
    _dup_write_raw(f"INFO: {msg}")


def _user_error(msg: str, exc: BaseException | None = None) -> None:
    print(msg, file=sys.stderr)
    _dup_write_raw(f"ERROR: {msg}")
    if exc is not None:
        _dup_write_raw("TRACEBACK:\n" + traceback.format_exc())


def _prompt(text: str, default: str | None = None) -> str:
    if default:
        value = input(f"{text} [{default}]: ").strip()
        return value if value else default
    return input(f"{text}: ").strip()


def _prompt_secret(text: str, default: str | None = None) -> str:
    # Requirement: login/password should be obtained from the user.
    # We still allow pressing Enter to use env defaults if present (for demos).
    if default:
        value = getpass.getpass(f"{text} (Enter to use default): ").strip()
        return value if value else default
    return getpass.getpass(f"{text}: ").strip()


def _parse_scalar(value: str) -> Any:
    v = value.strip()
    if v.lower() in {"null", "none"}:
        return None
    return v  # Let PostgreSQL cast text to the target type when needed.


def _choose_from_list(title: str, options: list[str]) -> str:
    while True:
        _user_info(title)
        for i, opt in enumerate(options, start=1):
            _user_info(f"  {i}) {opt}")
        raw = input("Choose number: ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass
        _user_error("Invalid choice. Please enter a valid number.")


def _choose_table() -> str:
    return _choose_from_list("Choose table:", _ALLOWED_TABLES)


def _allowed_columns_for(table: str, *, include_id: bool = True) -> list[str]:
    cols = _ALLOWED.get(table, [])
    if include_id:
        return cols
    return [c for c in cols if c != "id"]


def _choose_column(table: str, *, include_id: bool = True, title: str = "Choose column:") -> str:
    cols = _allowed_columns_for(table, include_id=include_id)
    return _choose_from_list(title, cols)


def _choose_columns_multi(table: str, *, include_id: bool) -> list[str]:
    allowed = set(_allowed_columns_for(table, include_id=include_id))
    _user_info("Enter columns separated by commas (from the allowed list).")
    _user_info("Allowed: " + ", ".join(sorted(allowed)))
    while True:
        raw = input("Columns: ").strip()
        cols = [c.strip() for c in raw.split(",") if c.strip()]
        if cols and all(c in allowed for c in cols) and len(set(cols)) == len(cols):
            return cols
        _user_error("Invalid columns. Use only allowed column names, without duplicates.")


def _print_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        _user_info("(no rows)")
        return
    for r in rows:
        _user_info(str(r))


def _connect_interactive() -> psycopg2.extensions.connection:
    host = os.getenv("DB_HOST", "db")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "shop_demo")

    default_user = (os.getenv("DB_USER") or "").strip() or None
    default_pass = (os.getenv("DB_PASS") or "").strip() or None

    user = _prompt("DB user", default=default_user)
    pwd = _prompt_secret("DB password", default=default_pass)

    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=pwd)
        _user_info("Connected to DB successfully.")
        return conn
    except Exception as e:
        _user_error("Failed to connect to DB. Check host/port/db name and credentials.", e)
        raise


def action_select(conn: psycopg2.extensions.connection, *, mode: str) -> None:
    table = _choose_table()
    cols = _allowed_columns_for(table, include_id=True)

    where_parts: list[sql.Composed] = []
    params: list[Any] = []

    if mode == "one":
        col = _choose_column(table, include_id=True, title="Filter column:")
        val = _parse_scalar(_prompt("Filter value"))
        where_parts.append(sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder()))
        params.append(val)
    elif mode == "many":
        n_raw = _prompt("How many filters (AND)?", default="2")
        try:
            n = max(1, int(n_raw))
        except ValueError:
            _user_error("Invalid number of filters.")
            return
        for i in range(1, n + 1):
            col = _choose_column(table, include_id=True, title=f"Filter column #{i}:")
            val = _parse_scalar(_prompt(f"Filter value #{i}"))
            where_parts.append(sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder()))
            params.append(val)

    query = sql.SQL("SELECT {cols} FROM {table}").format(
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
        table=sql.Identifier(table),
    )
    if where_parts:
        query = query + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_parts)

    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        _user_info("Query executed successfully.")
        _print_rows(rows)
    except Exception as e:
        _user_error("Failed to execute SELECT. Please check input values.", e)


def action_update_one(conn: psycopg2.extensions.connection) -> None:
    table = _choose_table()
    id_val = _parse_scalar(_prompt("Record id to update"))
    cols = _choose_columns_multi(table, include_id=False)

    set_parts: list[sql.Composed] = []
    params: list[Any] = []
    for c in cols:
        v = _parse_scalar(_prompt(f"New value for {c}"))
        set_parts.append(sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder()))
        params.append(v)
    params.append(id_val)

    query = sql.SQL("UPDATE {table} SET {setters} WHERE id = {id_ph}").format(
        table=sql.Identifier(table),
        setters=sql.SQL(", ").join(set_parts),
        id_ph=sql.Placeholder(),
    )

    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, params)
            affected = cur.rowcount
        _user_info(f"Update executed successfully. Rows affected: {affected}.")
    except Exception as e:
        _user_error("Failed to execute UPDATE. Please check input values.", e)


def action_update_many(conn: psycopg2.extensions.connection) -> None:
    table = _choose_table()
    set_col = _choose_column(table, include_id=False, title="Column to set (new common value):")
    set_val = _parse_scalar(_prompt(f"New value for {set_col}"))

    where_col = _choose_column(table, include_id=True, title="Column for IN (...) filter:")
    raw_vals = _prompt("Filter values (comma-separated, e.g. 1,2,3)")
    values = [_parse_scalar(v) for v in raw_vals.split(",") if v.strip()]
    if not values:
        _user_error("No filter values provided.")
        return

    in_placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(values))

    query = sql.SQL("UPDATE {table} SET {set_col} = {set_ph} WHERE {where_col} IN ({vals})").format(
        table=sql.Identifier(table),
        set_col=sql.Identifier(set_col),
        set_ph=sql.Placeholder(),
        where_col=sql.Identifier(where_col),
        vals=in_placeholders,
    )

    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, [set_val, *values])
            affected = cur.rowcount
        _user_info(f"Bulk update executed successfully. Rows affected: {affected}.")
    except Exception as e:
        _user_error("Failed to execute bulk UPDATE. Please check input values.", e)


def action_insert_one(conn: psycopg2.extensions.connection) -> None:
    table = _choose_table()
    cols = _choose_columns_multi(table, include_id=False)
    params = [_parse_scalar(_prompt(f"Value for {c}")) for c in cols]

    query = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING id").format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
        vals=sql.SQL(", ").join([sql.Placeholder()] * len(cols)),
    )

    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, params)
            new_id = cur.fetchone()[0]
        _user_info(f"Insert executed successfully. New id: {new_id}.")
    except Exception as e:
        _user_error("Failed to execute INSERT. Please check input values.", e)


def action_insert_many(conn: psycopg2.extensions.connection) -> None:
    table = _choose_table()
    cols = _choose_columns_multi(table, include_id=False)

    n_raw = _prompt("How many rows to insert?", default="2")
    try:
        n = max(1, int(n_raw))
    except ValueError:
        _user_error("Invalid number of rows.")
        return

    rows: list[list[Any]] = []
    for i in range(1, n + 1):
        _user_info(f"Row #{i}:")
        row = [_parse_scalar(_prompt(f"  Value for {c}")) for c in cols]
        rows.append(row)

    base = sql.SQL("INSERT INTO {table} ({cols}) VALUES %s").format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
    )

    try:
        with conn, conn.cursor() as cur:
            execute_values(cur, base.as_string(cur), rows)
            affected = cur.rowcount
        _user_info(f"Insert-many executed successfully. Rows affected: {affected}.")
    except Exception as e:
        _user_error("Failed to insert many rows. Please check input values.", e)


def action_insert_student_with_enrollments(conn: psycopg2.extensions.connection) -> None:
    """
    Insert into related tables (students + enrollments):
    - Insert 1 student -> get student id
    - Insert N enrollments linked to that student
    """
    _user_info("Creating a new student and related enrollments...")

    group_id = _parse_scalar(_prompt("Student.group_id"))
    full_name = _parse_scalar(_prompt("Student.full_name"))
    email = _parse_scalar(_prompt("Student.email"))

    student_q = sql.SQL("INSERT INTO {t} (group_id, full_name, email) VALUES ({g}, {n}, {e}) RETURNING id").format(
        t=sql.Identifier("students"),
        g=sql.Placeholder(),
        n=sql.Placeholder(),
        e=sql.Placeholder(),
    )

    n_raw = _prompt("How many enrollments to add for this student?", default="1")
    try:
        n = max(1, int(n_raw))
    except ValueError:
        _user_error("Invalid number of enrollments.")
        return

    semester_default = "2024-FALL"
    enrollments: list[tuple[Any, Any, Any]] = []
    for i in range(1, n + 1):
        _user_info(f"Enrollment #{i}:")
        course_id = _parse_scalar(_prompt("  course_id"))
        semester = _parse_scalar(_prompt("  semester", default=semester_default))
        grade_raw = _prompt("  grade (0..100 or NULL)", default="NULL")
        grade = _parse_scalar(grade_raw)
        enrollments.append((course_id, semester, grade))

    enroll_base = "INSERT INTO enrollments (student_id, course_id, semester, grade) VALUES %s"

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(student_q, [group_id, full_name, email])
                student_id = cur.fetchone()[0]

                rows = [(student_id, c, s, g) for (c, s, g) in enrollments]
                execute_values(cur, enroll_base, rows)
        _user_info(f"Inserted student successfully. New student id: {student_id}. Enrollments added: {n}.")
    except Exception as e:
        _user_error("Failed to insert student with enrollments. Please check input values.", e)


def main() -> int:
    _user_info("University DB CLI started.")
    _user_info("If DUPLICATE_LOG_FILE is set, raw logs are duplicated there.")

    try:
        conn = _connect_interactive()
    except Exception:
        return 1

    try:
        while True:
            _user_info("")
            _user_info("Menu:")
            _user_info("  1) View table (no filters)")
            _user_info("  2) View table (one filter)")
            _user_info("  3) View table (multiple filters)")
            _user_info("  4) Update one record by id")
            _user_info("  5) Update multiple records (set common value, filter by IN)")
            _user_info("  6) Insert one row into a table")
            _user_info("  7) Insert into related tables (student + enrollments)")
            _user_info("  8) Insert many rows into one table")
            _user_info("  0) Exit")
            choice = input("Choose: ").strip()

            if choice == "1":
                action_select(conn, mode="none")
            elif choice == "2":
                action_select(conn, mode="one")
            elif choice == "3":
                action_select(conn, mode="many")
            elif choice == "4":
                action_update_one(conn)
            elif choice == "5":
                action_update_many(conn)
            elif choice == "6":
                action_insert_one(conn)
            elif choice == "7":
                action_insert_student_with_enrollments(conn)
            elif choice == "8":
                action_insert_many(conn)
            elif choice == "0":
                _user_info("Bye.")
                break
            else:
                _user_error("Unknown menu option.")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        _user_info("Disconnected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())