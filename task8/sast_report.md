# Отчёт SAST-анализа: Task 3 и Task 7

## Используемые инструменты

| # | Инструмент | Тип | Версия | Назначение |
|---|-----------|-----|--------|-----------|
| 1 | **Semgrep** | Универсальный SAST | 1.157.0 | Статический анализ безопасности для 30+ языков, набор правил `auto` |
| 2 | **Bandit** | Python-специфичный SAST | latest | Анализ безопасности Python-кода (PyCQA/bandit) |

---

# Task 3

> Приложение: полноценный CLI (~400 строк) для работы с БД PostgreSQL.  
> Файлы: `app/main.py`, `app/whitelist.py`

## Таблица 1. Semgrep — Task 3

| # | Файл | Строка | Severity | Rule ID | Подробности |
|---|------|--------|----------|---------|-------------|
| 1 | `app/main.py` | 178 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными — риск SQL-инъекции (функция `action_select`, `cur.execute`) |
| 2 | `app/main.py` | 207 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными — риск SQL-инъекции (функция `action_update_one`, `cur.execute`) |
| 3 | `app/main.py` | 238 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными — риск SQL-инъекции (функция `action_update_many`, `cur.execute`) |
| 4 | `app/main.py` | 258 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными — риск SQL-инъекции (функция `action_insert_one`, `cur.execute`) |
| 5 | `app/main.py` | 337 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными — риск SQL-инъекции (функция `action_insert_student_with_enrollments`, `cur.execute`) |

## Таблица 2. Bandit — Task 3

| # | Файл | Строка | Severity / Confidence | Test ID | Тип ошибки | Подробности |
|---|------|--------|----------------------|---------|-----------|-------------|
| 1 | `app/main.py` | 33 | LOW / HIGH | B110 | `try_except_pass` | Конструкция `try/except/pass` — исключение подавляется без обработки (функция `_dup_write_raw`) |
| 2 | `app/main.py` | 395 | LOW / HIGH | B110 | `try_except_pass` | Конструкция `try/except/pass` — исключение подавляется без обработки (функция `main`, закрытие соединения) |

## Таблица 3. Сводная таблица — Task 3

> Строки отсортированы от наиболее критичных к наименее значимым. В конце — ложные срабатывания.

| # | Файл | Строка | Тип ошибки | Инструменты | Подробности | Приоритет |
|---|------|--------|-----------|-------------|-------------|-----------|
| 1 | `app/main.py` | 33 | Подавление исключений (`try/except/pass`) | Bandit (B110, LOW/HIGH) | Исключение при записи в лог-файл подавляется без обработки — ошибки логирования остаются незамеченными | 🟡 Средний |
| 2 | `app/main.py` | 395 | Подавление исключений (`try/except/pass`) | Bandit (B110, LOW/HIGH) | Исключение при закрытии DB-соединения подавляется без обработки — утечка ресурсов может остаться незамеченной | 🟡 Средний |
| 3 | `app/main.py` | 178 | `sqlalchemy-execute-raw-query` | Semgrep (ERROR) | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; код использует `psycopg2.sql.SQL` — безопасное параметризованное API | ⚪ Ложное срабатывание |
| 4 | `app/main.py` | 207 | `sqlalchemy-execute-raw-query` | Semgrep (ERROR) | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; код использует `psycopg2.sql.SQL` — безопасное параметризованное API | ⚪ Ложное срабатывание |
| 5 | `app/main.py` | 238 | `sqlalchemy-execute-raw-query` | Semgrep (ERROR) | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; код использует `psycopg2.sql.SQL` — безопасное параметризованное API | ⚪ Ложное срабатывание |
| 6 | `app/main.py` | 258 | `sqlalchemy-execute-raw-query` | Semgrep (ERROR) | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; код использует `psycopg2.sql.SQL` — безопасное параметризованное API | ⚪ Ложное срабатывание |
| 7 | `app/main.py` | 337 | `sqlalchemy-execute-raw-query` | Semgrep (ERROR) | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; код использует `psycopg2.sql.SQL` — безопасное параметризованное API | ⚪ Ложное срабатывание |

---

# Task 7

> Приложение: Flask-веб-приложение (~385 строк + HTML-шаблоны).  
> Файлы: `app/web.py`, `app/whitelist.py`, `app/templates/*.html`

## Таблица 4. Semgrep — Task 7

| # | Файл | Строка | Severity | Rule ID | Подробности |
|---|------|--------|----------|---------|-------------|
| 1 | `app/web.py` | 170 | WARNING | `sql-injection-db-cursor-execute` | Данные из запроса пользователя передаются в `execute()` — возможна SQL-инъекция (маршрут `/view`) |
| 2 | `app/web.py` | 187 | ERROR | `tainted-sql-string` (flask) | Пользовательский ввод используется для ручного построения SQL-строки (WHERE clause в `/view`) |
| 3 | `app/web.py` | 187 | ERROR | `tainted-sql-string` (django) | То же, что #2 — правило Django применено к Flask-приложению |
| 4 | `app/web.py` | 225 | CRITICAL | `generic-sql-flask` | Непроверенный ввод может использоваться для построения SQL-запроса (INSERT в `/add`) |
| 5 | `app/web.py` | 225 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными (правило SQLAlchemy применено к psycopg2) |
| 6 | `app/web.py` | 277 | ERROR | `tainted-sql-string` (flask) | Пользовательский ввод используется для ручного построения SQL-строки (INSERT в `/add`) |
| 7 | `app/web.py` | 277 | ERROR | `tainted-sql-string` (django) | То же, что #6 — правило Django применено к Flask-приложению |
| 8 | `app/web.py` | 281 | CRITICAL | `generic-sql-flask` | Непроверенный ввод может использоваться для построения SQL-запроса (INSERT в `/add`) |
| 9 | `app/web.py` | 281 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными (правило SQLAlchemy применено к psycopg2) |
| 10 | `app/web.py` | 324 | CRITICAL | `generic-sql-flask` | Непроверенный ввод может использоваться для построения SQL-запроса (SELECT в `/update`) |
| 11 | `app/web.py` | 324 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными (правило SQLAlchemy применено к psycopg2) |
| 12 | `app/web.py` | 324 | ERROR | `tainted-sql-string` (flask) | Пользовательский ввод используется для ручного построения SQL-строки (SELECT в `/update`) |
| 13 | `app/web.py` | 324 | ERROR | `tainted-sql-string` (django) | То же, что #12 — правило Django применено к Flask-приложению |
| 14 | `app/web.py` | 345 | ERROR | `tainted-sql-string` (flask) | Пользовательский ввод используется для ручного построения SQL-строки (SET clause в `/update`) |
| 15 | `app/web.py` | 345 | ERROR | `tainted-sql-string` (django) | То же, что #14 — правило Django применено к Flask-приложению |
| 16 | `app/web.py` | 350 | CRITICAL | `generic-sql-flask` | Непроверенный ввод может использоваться для построения SQL-запроса (UPDATE в `/update`) |
| 17 | `app/web.py` | 350 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными (правило SQLAlchemy применено к psycopg2) |
| 18 | `app/web.py` | 363 | CRITICAL | `generic-sql-flask` | Непроверенный ввод может использоваться для построения SQL-запроса (SELECT ids в `/update`) |
| 19 | `app/web.py` | 363 | ERROR | `sqlalchemy-execute-raw-query` | Конкатенация SQL-строки с непроверенными данными (правило SQLAlchemy применено к psycopg2) |
| 20 | `app/web.py` | 363 | ERROR | `tainted-sql-string` (flask) | Пользовательский ввод используется для ручного построения SQL-строки (SELECT ids в `/update`) |
| 21 | `app/web.py` | 363 | ERROR | `tainted-sql-string` (django) | То же, что #20 — правило Django применено к Flask-приложению |
| 22 | `app/web.py` | 363 | WARNING | `formatted-sql-query` | Обнаружен форматированный SQL-запрос — рекомендуется использовать параметризованные запросы |
| 23 | `app/web.py` | 384 | WARNING | `avoid_app_run_with_bad_host` | Запуск Flask с `host=0.0.0.0` открывает сервер публично |
| 24 | `app/templates/add.html` | 28 | WARNING | `django-no-csrf-token` | Форма создана вручную без CSRF-токена — уязвимость CSRF |
| 25 | `app/templates/login.html` | 12 | WARNING | `django-no-csrf-token` | Форма создана вручную без CSRF-токена — уязвимость CSRF |
| 26 | `app/templates/update.html` | 53 | WARNING | `django-no-csrf-token` | Форма создана вручную без CSRF-токена — уязвимость CSRF |

## Таблица 5. Bandit — Task 7

| # | Файл | Строка | Severity / Confidence | Test ID | Тип ошибки | Подробности |
|---|------|--------|----------------------|---------|-----------|-------------|
| 1 | `app/web.py` | 187 | MEDIUM / LOW | B608 | `hardcoded_sql_expressions` | Возможная SQL-инъекция через строковое построение запроса (WHERE clause в `/view`) |
| 2 | `app/web.py` | 277 | MEDIUM / LOW | B608 | `hardcoded_sql_expressions` | Возможная SQL-инъекция через строковое построение запроса (INSERT в `/add`) |
| 3 | `app/web.py` | 324 | MEDIUM / MEDIUM | B608 | `hardcoded_sql_expressions` | Возможная SQL-инъекция через строковое построение запроса (SELECT в `/update`) |
| 4 | `app/web.py` | 345 | MEDIUM / LOW | B608 | `hardcoded_sql_expressions` | Возможная SQL-инъекция через строковое построение запроса (SET clause в `/update`) |
| 5 | `app/web.py` | 363 | MEDIUM / MEDIUM | B608 | `hardcoded_sql_expressions` | Возможная SQL-инъекция через строковое построение запроса (SELECT ids в `/update`) |
| 6 | `app/web.py` | 384 | MEDIUM / MEDIUM | B104 | `hardcoded_bind_all_interfaces` | Привязка к всем интерфейсам (`0.0.0.0`) — возможна публичная доступность сервера |

## Таблица 6. Сводная таблица — Task 7

> Строки отсортированы от наиболее критичных к наименее значимым. В конце — ложные срабатывания.

| # | Файл | Строка | Тип ошибки | Инструменты | Подробности | Приоритет |
|---|------|--------|-----------|-------------|-------------|-----------|
| 1 | `app/web.py` | 225 | SQL Injection | Semgrep (CRITICAL) | Непроверенный ввод при построении SQL INSERT в маршруте `/add` | 🔴 Критический |
| 2 | `app/web.py` | 281 | SQL Injection | Semgrep (CRITICAL) | Непроверенный ввод при построении SQL INSERT в маршруте `/add` | 🔴 Критический |
| 3 | `app/web.py` | 324 | SQL Injection | Semgrep (CRITICAL) + Bandit (B608) | Непроверенный ввод при построении SQL SELECT в маршруте `/update` | 🔴 Критический |
| 4 | `app/web.py` | 350 | SQL Injection | Semgrep (CRITICAL) | Непроверенный ввод при построении SQL UPDATE в маршруте `/update` | 🔴 Критический |
| 5 | `app/web.py` | 363 | SQL Injection | Semgrep (CRITICAL) + Bandit (B608) | Непроверенный ввод при построении SQL SELECT ids в маршруте `/update` | 🔴 Критический |
| 6 | `app/web.py` | 187 | SQL Injection | Semgrep (ERROR) + Bandit (B608) | Пользовательский ввод в WHERE clause в маршруте `/view` | 🟠 Высокий |
| 7 | `app/web.py` | 277 | SQL Injection | Semgrep (ERROR) + Bandit (B608) | Пользовательский ввод в INSERT в маршруте `/add` | 🟠 Высокий |
| 8 | `app/web.py` | 345 | SQL Injection | Semgrep (ERROR) + Bandit (B608) | Пользовательский ввод в SET clause в маршруте `/update` | 🟠 Высокий |
| 9 | `app/web.py` | 170 | SQL Injection | Semgrep (WARNING) | Данные из запроса пользователя передаются в `execute()` в маршруте `/view` | 🟠 Высокий |
| 10 | `app/templates/add.html` | 28 | Отсутствие CSRF-защиты | Semgrep (WARNING) | Форма без CSRF-токена — возможна CSRF-атака | 🟡 Средний |
| 11 | `app/templates/login.html` | 12 | Отсутствие CSRF-защиты | Semgrep (WARNING) | Форма без CSRF-токена — возможна CSRF-атака | 🟡 Средний |
| 12 | `app/templates/update.html` | 53 | Отсутствие CSRF-защиты | Semgrep (WARNING) | Форма без CSRF-токена — возможна CSRF-атака | 🟡 Средний |
| 13 | `app/web.py` | 384 | Binding to all interfaces | Semgrep (WARNING) + Bandit (B104) | `app.run(host="0.0.0.0")` — сервер доступен на всех сетевых интерфейсах | 🟡 Средний |
| 14 | `app/web.py` | 225 | `sqlalchemy-execute-raw-query` | Semgrep | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; дублирует строку #1 | ⚪ Ложное срабатывание |
| 15 | `app/web.py` | 281 | `sqlalchemy-execute-raw-query` | Semgrep | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; дублирует строку #2 | ⚪ Ложное срабатывание |
| 16 | `app/web.py` | 324 | `sqlalchemy-execute-raw-query` | Semgrep | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; дублирует строку #3 | ⚪ Ложное срабатывание |
| 17 | `app/web.py` | 350 | `sqlalchemy-execute-raw-query` | Semgrep | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; дублирует строку #4 | ⚪ Ложное срабатывание |
| 18 | `app/web.py` | 363 | `sqlalchemy-execute-raw-query` | Semgrep | Ложное срабатывание: правило SQLAlchemy применено к psycopg2; дублирует строку #5 | ⚪ Ложное срабатывание |
| 19 | `app/web.py` | 187 | `tainted-sql-string` (django) | Semgrep | Ложное срабатывание: правило Django применено к Flask-приложению; дублирует строку #6 | ⚪ Ложное срабатывание |
| 20 | `app/web.py` | 277 | `tainted-sql-string` (django) | Semgrep | Ложное срабатывание: правило Django применено к Flask-приложению; дублирует строку #7 | ⚪ Ложное срабатывание |
| 21 | `app/web.py` | 324 | `tainted-sql-string` (django) | Semgrep | Ложное срабатывание: правило Django применено к Flask-приложению; дублирует строку #3 | ⚪ Ложное срабатывание |
| 22 | `app/web.py` | 345 | `tainted-sql-string` (django) | Semgrep | Ложное срабатывание: правило Django применено к Flask-приложению; дублирует строку #8 | ⚪ Ложное срабатывание |
| 23 | `app/web.py` | 363 | `tainted-sql-string` (django) | Semgrep | Ложное срабатывание: правило Django применено к Flask-приложению; дублирует строку #5 | ⚪ Ложное срабатывание |
| 24 | `app/web.py` | 363 | `formatted-sql-query` | Semgrep | Ложное срабатывание: строка формируется из whitelist-колонок, не из пользовательского ввода напрямую | ⚪ Ложное срабатывание |

---

## Вывод

### Сравнение количества находок

| Метрика | Task 3 | Task 7 | Изменение |
|---------|--------|--------|-----------|
| Semgrep — всего находок | 5 | 26 | **+21** |
| Semgrep — реальных уникальных проблем | 0 | 13 | **+13** |
| Semgrep — ложных срабатываний | 5 | 13 | **+8** |
| Bandit — всего находок | 2 | 6 | **+4** |
| Bandit — реальных уникальных проблем | 2 | 6 | **+4** |
| Bandit — ложных срабатываний | 0 | 0 | 0 |
| **Итого реальных уникальных проблем** | **2** | **19** | **+17** |
| **Итого ложных срабатываний** | **5** | **13** | **+8** |

### Заключение

**Количество ошибок значительно увеличилось** при переходе от Task 3 к Task 7:

1. **Task 3** — полноценный CLI (~400 строк) для работы с БД PostgreSQL. Приложение использует `psycopg2.sql.SQL` — безопасное параметризованное API для построения запросов. Все 5 находок Semgrep являются **ложными срабатываниями**: правило `sqlalchemy-execute-raw-query` применено к psycopg2-коду, который фактически использует безопасный механизм. Bandit нашёл 2 реальные (но низкоприоритетные) проблемы — конструкции `try/except/pass`, которые подавляют исключения без обработки.

2. **Task 7** — полноценное Flask-веб-приложение (~385 строк + HTML-шаблоны). Добавление веб-интерфейса, маршрутов, форм и динамических SQL-запросов привело к появлению **реальных уязвимостей**:
   - **SQL Injection** (строки 170, 187, 225, 277, 281, 324, 345, 350, 363) — f-string построение SQL с именами таблиц/колонок. В отличие от Task 3, здесь не используется `psycopg2.sql.SQL`, а применяется прямая f-string интерполяция. Имена таблиц/колонок защищены whitelist, значения — параметризованы, но архитектурно паттерн небезопасен.
   - **Отсутствие CSRF-защиты** (шаблоны `add.html`, `login.html`, `update.html`) — Flask-приложение не использует `flask-wtf` или аналог для CSRF-токенов в формах. Это реальная уязвимость.
   - **Публичный биндинг** (`app.run(host="0.0.0.0")`) — приемлемо для Docker-контейнера, но требует сетевой изоляции на уровне инфраструктуры.

3. **Ложные срабатывания** выросли с 5 до 13 в Semgrep. В Task 3 все 5 находок Semgrep — ложные (SQLAlchemy-правило применено к psycopg2). В Task 7 к ним добавились ложные срабатывания Django-правил на Flask-коде. Bandit показал 0 ложных срабатываний в обоих приложениях — более точный инструмент для Python-специфичных проверок.

4. **Ключевое различие между приложениями**: Task 3 использует `psycopg2.sql.SQL` — специализированный безопасный API для построения SQL-запросов с параметризацией идентификаторов. Task 7 использует f-string интерполяцию для построения SQL, что является менее безопасным паттерном, даже при наличии whitelist-защиты. Это объясняет, почему Task 7 получил значительно больше реальных находок.

5. **Общий вывод**: усложнение приложения от CLI (Task 3) до веб-приложения (Task 7) **закономерно увеличивает поверхность атаки** и количество реальных находок SAST-инструментов (+17 реальных проблем). Использование двух инструментов в совокупности даёт более полную картину: Semgrep обнаружил CSRF-уязвимость, которую Bandit пропустил; Bandit точнее идентифицировал Python-специфичные проблемы без ложных срабатываний.
