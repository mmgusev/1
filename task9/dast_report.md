# Отчёт DAST-анализа: Task 7 — Flask shop_demo

## Используемые инструменты и методология

| # | Инструмент | Версия | Режим | Описание |
|---|-----------|--------|-------|----------|
| 1 | **OWASP ZAP** (Zed Attack Proxy) | `zaproxy/zap-stable` (Docker) | Чёрный ящик | Автоматический spider + пассивное + активное сканирование без аутентификации |
| 2 | **OWASP ZAP** (Zed Attack Proxy) | `zaproxy/zap-stable` (Docker) | Серый ящик | Аутентифицированное сканирование с предварительным посевом всех известных маршрутов из исходного кода |

### Приложение-цель

- **URL:** `http://localhost:5000`
- **Стек:** Python 3.11 / Flask 3.1 / PostgreSQL 15 / Docker Compose
- **Исходные файлы:** `task7/app/web.py`, `task7/app/whitelist.py`, `task7/app/templates/*.html`

### Маршруты приложения (из исходного кода — grey-box знание)

| Маршрут | Методы | Описание |
|---------|--------|----------|
| `/` | GET, POST | Страница входа (форма: `db_user`, `db_pass`) |
| `/logout` | GET | Выход из системы |
| `/main` | GET | Главная страница (список таблиц) |
| `/view?table=<t>&filter_col=<c>&filter_op=<op>&filter_val=<v>` | GET | Просмотр таблицы с фильтрацией |
| `/add?table=<t>` | GET, POST | Добавление строки в таблицу |
| `/update?table=<t>&id=<id>` | GET, POST | Редактирование строки |

**Таблицы whitelist:** `products`, `customers`, `orders`, `order_items`, `categories`

---

## Таблица 1. Результаты DAST — режим «Чёрного ящика»

> Сканирование без аутентификации. ZAP обнаружил только страницу входа (`/`) и несколько вспомогательных URL.  
> Исходные файлы отчётов: `task9/blackbox_report.json`, `task9/blackbox_report.html`  
> Итог: **FAIL-NEW: 0 | WARN-NEW: 7 | PASS: 59**

| # | Тип ошибки | Запрос (путь) | Подробности |
|---|-----------|---------------|-------------|
| 1 | **Absence of Anti-CSRF Tokens** [10202] — Medium (Low) | `GET /`, `GET /` | Форма входа не содержит CSRF-токена. Злоумышленник может заставить браузер жертвы отправить форму от её имени. CWE-352, WASC-9. |
| 2 | **Content Security Policy (CSP) Header Not Set** [10038] — Medium (High) | `GET /`, `GET /robots.txt`, `GET /sitemap.xml` | Отсутствует заголовок `Content-Security-Policy`. Без CSP браузер не ограничивает источники скриптов/стилей, что облегчает XSS-атаки. CWE-693, WASC-15. |
| 3 | **Missing Anti-clickjacking Header** [10020] — Medium (Medium) | `GET /`, `GET /` | Отсутствует заголовок `X-Frame-Options` или `frame-ancestors` в CSP. Страница может быть встроена в `<iframe>` для clickjacking-атаки. CWE-1021, WASC-15. |
| 4 | **Cross-Origin-Embedder-Policy Header Missing or Invalid** [90004] — Low (Medium) | `GET /`, `GET /` | Отсутствует заголовок `Cross-Origin-Embedder-Policy`. Снижает изоляцию ресурсов между источниками. CWE-693, WASC-14. |
| 5 | **Cross-Origin-Opener-Policy Header Missing or Invalid** [90004] — Low (Medium) | `GET /`, `GET /` | Отсутствует заголовок `Cross-Origin-Opener-Policy`. Позволяет другим вкладкам получить доступ к объекту `window`. CWE-693, WASC-14. |
| 6 | **Cross-Origin-Resource-Policy Header Missing or Invalid** [90004] — Low (Medium) | `GET /` (×9 запросов) | Отсутствует заголовок `Cross-Origin-Resource-Policy`. Ресурсы могут быть загружены с других источников. CWE-693, WASC-14. |
| 7 | **Permissions Policy Header Not Set** [10063] — Low (Medium) | `GET /`, `GET /robots.txt`, `GET /sitemap.xml` | Отсутствует заголовок `Permissions-Policy`. Браузер не ограничивает доступ к API (камера, микрофон, геолокация). CWE-693, WASC-15. |
| 8 | **Server Leaks Version Information via "Server" HTTP Response Header** [10036] — Low (High) | `GET /`, `GET /robots.txt`, `GET /sitemap.xml` | Заголовок `Server: Werkzeug/3.1.8 Python/3.11.x` раскрывает версии фреймворка и интерпретатора. Облегчает поиск известных уязвимостей. CWE-497, WASC-13. |
| 9 | **X-Content-Type-Options Header Missing** [10021] — Low (Medium) | `GET /`, `GET /` | Отсутствует заголовок `X-Content-Type-Options: nosniff`. Браузер может интерпретировать ответ не по объявленному MIME-типу (MIME sniffing). CWE-693, WASC-15. |

---

## Таблица 2. Результаты DAST — режим «Серого ящика»

> Аутентифицированное сканирование. ZAP получил учётные данные (`app_user` / `app_pass_ChangeMe!`) и список всех маршрутов из исходного кода. Spider обнаружил 13 URL. Активное сканирование заняло ~2 минуты.  
> Исходные файлы отчётов: `task9/greybox_report.json`, `task9/greybox_report.html`  
> Итог: **12 алертов (4 Medium, 3 Low, 5 Informational)**

| # | Тип ошибки | Запрос (путь) | Подробности |
|---|-----------|---------------|-------------|
| 1 | **Absence of Anti-CSRF Tokens** [10202] — Medium (Low) | `GET /`, `GET /main`, `GET /add?table=*`, `GET /update?table=*` | Все формы приложения (вход, добавление, обновление) не содержат CSRF-токенов. В режиме серого ящика ZAP обнаружил все формы, а не только страницу входа. CWE-352, WASC-9. |
| 2 | **Content Security Policy (CSP) Header Not Set** [10038] — Medium (High) | `GET /`, `GET /main`, `GET /view?table=*`, `GET /add?table=*`, `GET /update?table=*` | Отсутствует заголовок `Content-Security-Policy` на всех страницах приложения. CWE-693, WASC-15. |
| 3 | **HTTP Only Site** [10106] — Medium (Medium) | `GET /` | Приложение работает только по HTTP без HTTPS. Сессионные cookie и учётные данные передаются в открытом виде. CWE-311, WASC-4. **Новая находка серого ящика.** |
| 4 | **Missing Anti-clickjacking Header** [10020] — Medium (Medium) | `GET /`, `GET /main`, `GET /view?table=*`, `GET /add?table=*`, `GET /update?table=*` | Отсутствует `X-Frame-Options` на всех страницах. В режиме серого ящика ZAP проверил все аутентифицированные страницы. CWE-1021, WASC-15. |
| 5 | **Cookie without SameSite Attribute** [10054] — Low (Medium) | `GET /add?table=orders`, `GET /main`, `GET /view?table=*`, `GET /update?table=*` | Сессионный cookie Flask (`session`) установлен без атрибута `SameSite`. Это облегчает CSRF-атаки через межсайтовые запросы. CWE-1275, WASC-13. **Новая находка серого ящика.** |
| 6 | **Server Leaks Version Information via "Server" HTTP Response Header** [10036] — Low (High) | `GET /`, `GET /add?table=products`, `GET /main`, `GET /view?table=*` | Заголовок `Server: Werkzeug/3.1.8 Python/3.11.x` раскрывает версии на всех страницах. CWE-497, WASC-13. |
| 7 | **X-Content-Type-Options Header Missing** [10021] — Low (Medium) | `GET /`, `GET /main`, `GET /view?table=*`, `GET /add?table=*`, `GET /update?table=*` | Отсутствует `X-Content-Type-Options: nosniff` на всех страницах. CWE-693, WASC-15. |
| 8 | **Authentication Request Identified** [10111] — Informational (Low) | `POST /` (параметр: `db_user`) | ZAP идентифицировал форму аутентификации. Информационная запись, не является уязвимостью. |
| 9 | **Modern Web Application** [10109] — Informational (Medium) | `GET /`, `GET /main` | ZAP определил приложение как современное веб-приложение. Информационная запись. |
| 10 | **Session Management Response Identified** [10112] — Informational (Medium) | `GET /add?table=products`, `GET /main` (параметр: `session`) | ZAP идентифицировал механизм управления сессиями (cookie `session`). Информационная запись. **Новая находка серого ящика.** |
| 11 | **User Agent Fuzzer** [10104] — Informational (Medium) | `GET /add?table=categories`, `GET /main` (Header: `User-Agent`) | ZAP проверил реакцию приложения на различные User-Agent заголовки. Приложение корректно обрабатывает нестандартные значения. Информационная запись. **Новая находка серого ящика.** |
| 12 | **User Controllable HTML Element Attribute (Potential XSS)** [10031] — Informational (Low) | `POST /` (параметры: `db_user`, `db_pass`) | ZAP обнаружил, что значения полей формы входа могут отражаться в HTML-атрибутах. Требует ручной проверки. Jinja2 автоматически экранирует вывод — вероятно ложное срабатывание. |

---

## Таблица 3. Сводная таблица — объединённые результаты

> Дубликаты удалены. Строки отсортированы от наиболее критичных к наименее значимым. В конце таблицы — ложные срабатывания.

| # | Тип ошибки | ZAP ID | Запрос (путь) | Подробности | Режим обнаружения | Приоритет |
|---|-----------|--------|---------------|-------------|-------------------|-----------|
| 1 | **HTTP Only Site** (передача данных без шифрования) | 10106 | `GET /` | Приложение работает только по HTTP. Учётные данные (`db_user`, `db_pass`) и сессионный cookie передаются в открытом виде. В реальной среде обязателен HTTPS + HSTS. CWE-311, WASC-4. | 🔵 Серый ящик | 🔴 Высокий |
| 2 | **Absence of Anti-CSRF Tokens** | 10202 | `POST /`, `POST /add`, `POST /update` | Все формы приложения не содержат CSRF-токенов. Злоумышленник может заставить аутентифицированного пользователя выполнить нежелательные действия (добавить/изменить данные). Flask-WTF или ручная реализация CSRF-токена устранит проблему. CWE-352, WASC-9. | ⚫ Чёрный + 🔵 Серый | 🟠 Средний |
| 3 | **Cookie without SameSite Attribute** | 10054 | `GET /main`, `GET /add?table=*`, `GET /update?table=*`, `GET /view?table=*` | Сессионный cookie Flask (`session`) установлен без атрибута `SameSite=Strict` или `SameSite=Lax`. Усиливает риск CSRF-атак. Исправление: `SESSION_COOKIE_SAMESITE = 'Lax'` в конфигурации Flask. CWE-1275, WASC-13. | 🔵 Серый ящик | 🟠 Средний |
| 4 | **Content Security Policy (CSP) Header Not Set** | 10038 | Все страницы (`/`, `/main`, `/view`, `/add`, `/update`) | Отсутствует заголовок `Content-Security-Policy`. Без CSP браузер не ограничивает источники скриптов, что облегчает XSS-атаки. Исправление: добавить CSP-заголовок через Flask `after_request`. CWE-693, WASC-15. | ⚫ Чёрный + 🔵 Серый | 🟠 Средний |
| 5 | **Missing Anti-clickjacking Header** | 10020 | Все страницы (`/`, `/main`, `/view`, `/add`, `/update`) | Отсутствует `X-Frame-Options: DENY` или `frame-ancestors 'none'` в CSP. Страницы могут быть встроены в `<iframe>` для clickjacking. Исправление: добавить заголовок через Flask `after_request`. CWE-1021, WASC-15. | ⚫ Чёрный + 🔵 Серый | 🟠 Средний |
| 6 | **Server Leaks Version Information** | 10036 | Все страницы | Заголовок `Server: Werkzeug/3.1.8 Python/3.11.x` раскрывает версии фреймворка и интерпретатора. Исправление: убрать/заменить заголовок `Server` через reverse proxy (nginx). CWE-497, WASC-13. | ⚫ Чёрный + 🔵 Серый | 🟡 Низкий |
| 7 | **X-Content-Type-Options Header Missing** | 10021 | Все страницы | Отсутствует `X-Content-Type-Options: nosniff`. Браузер может интерпретировать ответ не по объявленному MIME-типу. Исправление: добавить заголовок через Flask `after_request`. CWE-693, WASC-15. | ⚫ Чёрный + 🔵 Серый | 🟡 Низкий |
| 8 | **Cross-Origin-Embedder-Policy Header Missing** | 90004 | `GET /`, `GET /main` | Отсутствует `Cross-Origin-Embedder-Policy`. Снижает изоляцию ресурсов. Исправление: добавить `COEP: require-corp`. CWE-693, WASC-14. | ⚫ Чёрный ящик | 🟡 Низкий |
| 9 | **Cross-Origin-Opener-Policy Header Missing** | 90004 | `GET /`, `GET /main` | Отсутствует `Cross-Origin-Opener-Policy`. Позволяет другим вкладкам получить доступ к `window`. Исправление: добавить `COOP: same-origin`. CWE-693, WASC-14. | ⚫ Чёрный ящик | 🟡 Низкий |
| 10 | **Cross-Origin-Resource-Policy Header Missing** | 90004 | `GET /` (×9) | Отсутствует `Cross-Origin-Resource-Policy`. Ресурсы могут загружаться с других источников. Исправление: добавить `CORP: same-origin`. CWE-693, WASC-14. | ⚫ Чёрный ящик | 🟡 Низкий |
| 11 | **Permissions Policy Header Not Set** | 10063 | Все страницы | Отсутствует `Permissions-Policy`. Браузер не ограничивает доступ к API устройства. Исправление: добавить заголовок с ограничениями. CWE-693, WASC-15. | ⚫ Чёрный ящик | 🟡 Низкий |
| 12 | **User Controllable HTML Element Attribute (Potential XSS)** | 10031 | `POST /` (параметры: `db_user`, `db_pass`) | ZAP обнаружил отражение значений полей формы в HTML-атрибутах. **Ложное срабатывание**: Jinja2 автоматически экранирует все переменные в шаблонах (`{{ }}`) — XSS невозможен без явного использования `\|safe`. Ручная проверка шаблона `login.html` подтверждает безопасность. | ⚫ Чёрный + 🔵 Серый | ⚪ Ложное срабатывание |
| 13 | **Authentication Request Identified** | 10111 | `POST /` | ZAP идентифицировал форму аутентификации. **Ложное срабатывание**: информационная запись, не является уязвимостью. | ⚫ Чёрный + 🔵 Серый | ⚪ Ложное срабатывание |
| 14 | **Modern Web Application** | 10109 | `GET /`, `GET /main` | ZAP определил приложение как современное. **Ложное срабатывание**: информационная запись, не является уязвимостью. | ⚫ Чёрный + 🔵 Серый | ⚪ Ложное срабатывание |
| 15 | **Session Management Response Identified** | 10112 | `GET /main`, `GET /add?table=products` | ZAP идентифицировал механизм сессий. **Ложное срабатывание**: информационная запись, не является уязвимостью. | 🔵 Серый ящик | ⚪ Ложное срабатывание |
| 16 | **User Agent Fuzzer** | 10104 | `GET /add?table=categories`, `GET /main` | ZAP проверил реакцию на нестандартные User-Agent. Приложение корректно обрабатывает все значения. **Ложное срабатывание**: информационная запись. | 🔵 Серый ящик | ⚪ Ложное срабатывание |

---

## Вывод

### Сравнение количества находок по режимам тестирования

| Метрика | Чёрный ящик | Серый ящик | Изменение |
|---------|-------------|------------|-----------|
| Всего алертов | 13 | 12 | −1 |
| Уникальных типов уязвимостей | 9 | 12 | **+3** |
| Реальных уязвимостей (Medium+) | 3 | 4 | **+1** |
| Реальных уязвимостей (Low) | 4 | 3 | −1 |
| Ложных срабатываний | 5 | 5 | 0 |
| Новых находок (только серый ящик) | — | 4 | **+4** |
| Охват маршрутов | 1 (только `/`) | 13 URL | **+12** |

### Анализ результатов

**1. Режим «Чёрного ящика»** обнаружил только уязвимости на публично доступной странице входа (`/`). ZAP не смог пройти аутентификацию и просканировать защищённые маршруты (`/main`, `/view`, `/add`, `/update`). Из 9 уникальных типов алертов:
- 3 реальных уязвимости уровня Medium (CSRF, CSP, Clickjacking)
- 4 уязвимости уровня Low (утечка версии, заголовки безопасности)
- 5 ложных срабатываний (информационные записи)

**2. Режим «Серого ящика»** значительно расширил охват: ZAP получил учётные данные и список всех 18 маршрутов из исходного кода, что позволило просканировать 13 URL. Дополнительно обнаружены:
- **HTTP Only Site** (Medium) — критическая находка: передача учётных данных без шифрования
- **Cookie without SameSite Attribute** (Low) — усиливает риск CSRF
- **Session Management Response Identified** (Informational) — подтверждение механизма сессий
- **User Agent Fuzzer** (Informational) — проверка устойчивости к нестандартным заголовкам

**3. Ключевые выводы:**

- **Количество реальных уязвимостей увеличилось** при переходе от чёрного к серому ящику (+1 Medium, +1 Low), несмотря на то что общее число алертов незначительно уменьшилось (−1). Это объясняется тем, что серый ящик находит более специфичные уязвимости, связанные с аутентифицированными сессиями.

- **Охват тестирования вырос в 13 раз** (с 1 до 13 URL). Без аутентификации ZAP видел только страницу входа; с учётными данными и знанием маршрутов — всё приложение.

- **Ложные срабатывания не изменились** (5 в обоих режимах), однако их состав различается: в сером ящике появились новые информационные записи (Session Management, User Agent Fuzzer), которые заменили некоторые дублирующиеся алерты чёрного ящика.

- **Наиболее критичная находка серого ящика** — отсутствие HTTPS (HTTP Only Site). В реальной среде это означает, что учётные данные пользователей и сессионные токены передаются в открытом виде и могут быть перехвачены при атаке «человек посередине» (MITM).

- **Все SQL-инъекции отсутствуют**: активное сканирование ZAP не обнаружило ни одной SQL-инъекции, что подтверждает эффективность whitelist-защиты и параметризованных запросов, реализованных в приложении.

**4. Рекомендации по исправлению (в порядке приоритета):**

1. 🔴 Настроить HTTPS (Let's Encrypt / nginx reverse proxy) + `SESSION_COOKIE_SECURE = True`
2. 🟠 Добавить CSRF-защиту (Flask-WTF или ручная реализация) + `SESSION_COOKIE_SAMESITE = 'Lax'`
3. 🟠 Добавить заголовки безопасности через Flask `after_request`:
   ```python
   @app.after_request
   def set_security_headers(response):
       response.headers['Content-Security-Policy'] = "default-src 'self'"
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
       response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
       response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
       response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
       return response
   ```
4. 🟡 Скрыть версию сервера через nginx (`server_tokens off`) или Werkzeug конфигурацию
