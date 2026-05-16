"""
Flask веб-приложение для управления базой данных shop_demo.
Предоставляет: вход в систему, просмотр таблиц, добавление и обновление строк.
Неудачные попытки входа записываются в лог-файл.
Все SQL-запросы используют параметризованные выражения;
имена колонок и таблиц проверяются по whitelist для предотвращения SQL-инъекций.
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
# Настройка приложения
# ---------------------------------------------------------------------------
app = Flask(__name__)
# ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД НЕ ИСПОЛЬЗУЕТСЯ: секретный ключ берётся из переменной
# окружения SECRET_KEY. Если переменная не задана — используется небезопасный
# fallback "change-me-in-production". В продакшене SECRET_KEY обязателен.
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# ---------------------------------------------------------------------------
# Логирование неудачных попыток входа
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
# Дублируем вывод в stdout, чтобы Docker logs подхватывал записи
logger.addHandler(logging.StreamHandler())

# ---------------------------------------------------------------------------
# Вспомогательные функции для работы с БД
# ---------------------------------------------------------------------------
# Параметры подключения берутся из переменных окружения, не из пользовательского ввода
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "shop_demo")

# Whitelist разрешённых таблиц и колонок — загружается один раз при старте.
# Используется для валидации пользовательского ввода перед подстановкой
# имён таблиц/колонок в SQL-запросы.
ALLOWED = get_allowed_columns()  # {table: [col, ...]}


def _get_conn(user: str, password: str):
    """Открывает новое соединение psycopg2 с переданными учётными данными.

    ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: user и password приходят из формы входа.
    Они передаются в psycopg2.connect() как параметры подключения (не в SQL),
    поэтому SQL-инъекция через эти поля невозможна — libpq передаёт их
    напрямую в PostgreSQL по протоколу, минуя SQL-парсер.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=user,
        password=password,
        connect_timeout=5,
    )


def get_conn():
    """Возвращает соединение, используя учётные данные из сессии."""
    return _get_conn(session["db_user"], session["db_pass"])


def _safe_table(table: str) -> str:
    """Проверяет имя таблицы по whitelist. Выбрасывает ValueError если не найдено.

    ЗАЩИТА ОТ SQL-ИНЪЕКЦИИ: имена таблиц нельзя передать через %s-плейсхолдер
    (psycopg2 обернёт их в строку с кавычками). Поэтому они интерполируются
    через f-string, но ТОЛЬКО после проверки по whitelist — пользовательский
    ввод никогда не попадает в SQL напрямую.
    """
    if table not in ALLOWED:
        raise ValueError(f"Unknown table: {table!r}")
    return table


def _safe_columns(table: str, columns: list[str]) -> list[str]:
    """Возвращает только те колонки из списка, которые есть в whitelist таблицы.

    ЗАЩИТА ОТ SQL-ИНЪЕКЦИИ: аналогично _safe_table — имена колонок
    интерполируются в SQL только после проверки по whitelist.
    """
    allowed = ALLOWED[table]
    return [c for c in columns if c in allowed]


# ---------------------------------------------------------------------------
# Вспомогательные функции аутентификации
# ---------------------------------------------------------------------------
def logged_in() -> bool:
    """Проверяет, авторизован ли пользователь (наличие данных в сессии)."""
    return "db_user" in session and "db_pass" in session


def require_login():
    """Перенаправляет на страницу входа, если пользователь не авторизован."""
    if not logged_in():
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return None


# ---------------------------------------------------------------------------
# Маршруты — аутентификация
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if logged_in():
        return redirect(url_for("index"))

    if request.method == "POST":
        # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: логин и пароль из HTML-формы.
        # .strip() убирает пробелы по краям логина (пароль не трогаем).
        db_user = request.form.get("db_user", "").strip()
        db_pass = request.form.get("db_pass", "")

        if not db_user:
            flash("Username is required.", "danger")
            return render_template("login.html")

        try:
            # ЗАЩИТА: db_user и db_pass передаются в psycopg2.connect() как
            # параметры подключения, а не подставляются в SQL-строку.
            # PostgreSQL сам проверяет аутентификацию через протокол libpq.
            # SQL-инъекция через поля логина/пароля невозможна.
            conn = _get_conn(db_user, db_pass)
            conn.close()
        except psycopg2.OperationalError as exc:
            # Логируем неудачную попытку входа: логин и IP-адрес клиента.
            # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: db_user и request.remote_addr попадают
            # только в лог-файл, не в SQL-запросы.
            logger.warning(
                "Failed login attempt | user=%r | ip=%s | reason=%s",
                db_user,
                request.remote_addr,
                str(exc).splitlines()[0],
            )
            flash("Invalid credentials or database unreachable.", "danger")
            return render_template("login.html")

        # Сохраняем учётные данные в зашифрованной сессии Flask.
        # Они будут использоваться для последующих запросов к БД.
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
# Маршруты — главная страница
# ---------------------------------------------------------------------------
@app.route("/main")
def index():
    redir = require_login()
    if redir:
        return redir
    tables = list(ALLOWED.keys())
    return render_template("index.html", tables=tables, user=session["db_user"])


# ---------------------------------------------------------------------------
# Маршруты — просмотр таблиц
# ---------------------------------------------------------------------------
@app.route("/view", methods=["GET"])
def view():
    redir = require_login()
    if redir:
        return redir

    # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: имя таблицы из параметра URL (?table=products).
    # ЗАЩИТА: _safe_table() проверяет значение по whitelist.
    # Если таблица не в whitelist — выбрасывается ValueError и показывается ошибка.
    table = request.args.get("table", "products")
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: параметры фильтрации из URL-строки запроса.
    # filter_col — имя колонки для фильтра
    # filter_op  — оператор сравнения (eq, ne, lt, le, gt, ge, like, in)
    # filter_val — значение фильтра (одно или список через запятую для IN)
    filter_col = request.args.get("filter_col", "").strip()
    filter_op  = request.args.get("filter_op", "eq").strip()
    filter_val = request.args.get("filter_val", "").strip()

    allowed_cols = ALLOWED[table]

    # ЗАЩИТА: имена таблицы и колонок берутся из whitelist, а не из
    # пользовательского ввода напрямую. Они безопасно интерполируются
    # в SQL через f-string с двойными кавычками (стандарт SQL для идентификаторов).
    # Все значения фильтров передаются через %s-плейсхолдеры.
    col_list = ", ".join(f'"{c}"' for c in allowed_cols)
    sql = f'SELECT {col_list} FROM "{table}"'
    params: list = []

    # Словарь разрешённых операторов сравнения.
    # ЗАЩИТА: оператор берётся из этого словаря по ключу — пользователь
    # может передать только ключ (eq, like и т.д.), а в SQL попадает
    # значение из словаря (=, ILIKE и т.д.). Произвольный SQL-оператор
    # передать невозможно.
    op_map = {
        "eq":   "=",
        "ne":   "!=",
        "lt":   "<",
        "le":   "<=",
        "gt":   ">",
        "ge":   ">=",
        "like": "ILIKE",
        "in":   "IN",   # группа значений: "1, 2, 3" → IN (%s, %s, %s)
    }

    # Добавляем WHERE-clause только если все условия выполнены:
    # - колонка не пустая И есть в whitelist
    # - значение фильтра не пустое
    # - оператор из разрешённого словаря
    if filter_col and filter_col in allowed_cols and filter_val and filter_op in op_map:
        if filter_op == "in":
            # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: filter_val содержит список значений через запятую.
            # ЗАЩИТА ОТ SQL-ИНЪЕКЦИИ для группы однотипных значений:
            # 1. Разбиваем строку "1, 2, 3" на список ["1", "2", "3"]
            # 2. Генерируем строку плейсхолдеров "%s, %s, %s" — по одному на значение
            # 3. Добавляем все значения в params
            # 4. psycopg2 биндит каждое значение независимо через протокол PostgreSQL
            # Даже если пользователь введёт "1, 2); DROP TABLE products; --",
            # второй элемент будет передан как строковый параметр $2, а не как SQL-код.
            in_values = [v.strip() for v in filter_val.split(",") if v.strip()]
            if in_values:
                placeholders = ", ".join(["%s"] * len(in_values))
                sql += f' WHERE "{filter_col}" IN ({placeholders})'
                params.extend(in_values)
        else:
            # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: filter_val — одиночное значение фильтра.
            # ЗАЩИТА: значение передаётся через %s-плейсхолдер, никогда не
            # вставляется в SQL-строку напрямую.
            sql += f' WHERE "{filter_col}" {op_map[filter_op]} %s'
            params.append(filter_val)

    sql += ' ORDER BY "id" LIMIT 500'

    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ЗАЩИТА: cur.execute() передаёт SQL-шаблон и params раздельно.
        # psycopg2 отправляет их в PostgreSQL как подготовленный запрос —
        # значения из params никогда не конкатенируются со строкой SQL.
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
# Маршруты — добавление строк
# ---------------------------------------------------------------------------
@app.route("/add", methods=["GET", "POST"])
def add():
    redir = require_login()
    if redir:
        return redir

    # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: имя таблицы из URL или формы.
    # ЗАЩИТА: _safe_table() проверяет по whitelist.
    table = request.args.get("table") or request.form.get("table") or "products"
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    # Исключаем колонку id — она генерируется БД автоматически (SERIAL/SEQUENCE)
    allowed_cols = [c for c in ALLOWED[table] if c != "id"]

    if request.method == "POST":
        # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: значения полей формы для вставки новой строки.
        # ЗАЩИТА: собираем только те колонки, которые есть в whitelist.
        # Пустые значения пропускаем — не вставляем NULL без явного указания.
        data = {
            col: request.form.get(col, "").strip()
            for col in allowed_cols
            if request.form.get(col, "").strip() != ""
        }

        if not data:
            flash("No data provided.", "warning")
        else:
            # ЗАЩИТА: имена колонок берутся из whitelist (ключи data),
            # значения передаются через %s-плейсхолдеры.
            # Итоговый SQL: INSERT INTO "products" ("name", "price") VALUES (%s, %s)
            cols_sql = ", ".join(f'"{k}"' for k in data)
            placeholders = ", ".join(["%s"] * len(data))
            sql = f'INSERT INTO "{table}" ({cols_sql}) VALUES ({placeholders})'
            try:
                conn = get_conn()
                cur = conn.cursor()
                # ЗАЩИТА: значения из формы передаются как параметры,
                # не конкатенируются в SQL-строку.
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
# Маршруты — обновление строк
# ---------------------------------------------------------------------------
@app.route("/update", methods=["GET", "POST"])
def update():
    redir = require_login()
    if redir:
        return redir

    # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: имя таблицы из URL или формы.
    # ЗАЩИТА: _safe_table() проверяет по whitelist.
    table = request.args.get("table") or request.form.get("table") or "products"
    try:
        _safe_table(table)
    except ValueError:
        flash("Unknown table.", "danger")
        return redirect(url_for("index"))

    allowed_cols = ALLOWED[table]
    editable_cols = [c for c in allowed_cols if c != "id"]

    # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: id строки для редактирования из URL или формы.
    row_id = request.args.get("id") or request.form.get("row_id")
    row = None

    # ---- Загрузка существующей строки для редактирования ----
    if row_id:
        try:
            conn = get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            # ЗАЩИТА: имя таблицы из whitelist интерполируется через f-string,
            # row_id передаётся через %s-плейсхолдер.
            cur.execute(f'SELECT * FROM "{table}" WHERE id = %s', (row_id,))
            row = cur.fetchone()
            conn.close()
        except Exception as exc:
            flash(f"Fetch error: {exc}", "danger")

    # ---- Обработка отправки формы ----
    if request.method == "POST" and request.form.get("row_id"):
        # ПОЛЬЗОВАТЕЛЬСКИЙ ВВОД: новые значения полей из формы.
        # ЗАЩИТА: собираем только whitelisted колонки, пустые значения пропускаем.
        data = {
            col: request.form.get(col, "").strip()
            for col in editable_cols
            if request.form.get(col) is not None
        }
        # Не перезаписываем поля пустыми строками
        data = {k: v for k, v in data.items() if v != ""}

        if not data:
            flash("Nothing to update.", "warning")
        else:
            # ЗАЩИТА: имена колонок из whitelist интерполируются через f-string,
            # значения и row_id передаются через %s-плейсхолдеры.
            # Итоговый SQL: UPDATE "products" SET "name" = %s, "price" = %s WHERE id = %s
            set_clause = ", ".join(f'"{k}" = %s' for k in data)
            sql = f'UPDATE "{table}" SET {set_clause} WHERE id = %s'
            params = list(data.values()) + [row_id]
            try:
                conn = get_conn()
                cur = conn.cursor()
                # ЗАЩИТА: все пользовательские значения передаются как параметры.
                cur.execute(sql, params)
                conn.commit()
                conn.close()
                flash("Row updated successfully.", "success")
                return redirect(url_for("update", table=table, id=row_id))
            except Exception as exc:
                flash(f"Update error: {exc}", "danger")

    # ---- Список строк для выбора ----
    rows = []
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ЗАЩИТА: имя таблицы из whitelist, пользовательский ввод не используется.
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
# Точка входа
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # ЗАМЕЧАНИЕ: host="0.0.0.0" открывает сервер на всех сетевых интерфейсах.
    # Это необходимо для работы внутри Docker-контейнера, но требует
    # сетевой изоляции на уровне инфраструктуры (docker network, firewall).
    # debug=False — обязательно в продакшене, иначе Werkzeug debugger
    # позволяет выполнять произвольный Python-код через браузер.
    app.run(host="0.0.0.0", port=5000, debug=False)
