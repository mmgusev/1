# Отчёт CI/CD конвейера: Task 10

## Платформа и инструменты

| Компонент | Значение |
|-----------|----------|
| CI/CD платформа | **GitHub Actions** |
| Репозиторий | https://github.com/mmgusev/1 |
| SAST инструменты | **Bandit** (Python) + **Semgrep** (multi-language) |
| DAST инструмент | **OWASP ZAP** (`zaproxy/action-baseline` + Automation Framework) |
| Приложение | Flask shop_demo (Task 7) |

---

## Структура веток и триггеры

```
main          ← Merge из develop → запускает SAST + DAST
  │
develop       ← Push/Merge → запускает DAST (ZAP black-box + grey-box)
  │
feature/*     ← Push → запускает SAST (Bandit + Semgrep)
```

### Ветки в репозитории

| Ветка | Назначение | Workflow | Триггер |
|-------|-----------|----------|---------|
| `feature/task10-app` | Разработка новой функциональности | `sast-feature.yml` | Push в `feature/**` |
| `develop` | Интеграционная ветка | `dast-develop.yml` | Push в `develop` |
| `main` | Продуктивная ветка | `sast-dast-main.yml` | Push в `main` |

---

## Workflow 1: SAST — Feature Branch

**Файл:** [`.github/workflows/sast-feature.yml`](../.github/workflows/sast-feature.yml)  
**Триггер:** Push в `feature/**`  
**Запущен:** Push в `feature/task10-app`

### Шаги пайплайна

```
1. Checkout code
2. Set up Python 3.11
3. Install Bandit + Semgrep
4. Run Bandit → task10/bandit_report.json + bandit_report.txt
5. Run Semgrep (config: auto) → task10/semgrep_report.json
6. Upload artifacts (retention: 30 days)
```

### Результаты SAST (feature branch)

> Результаты соответствуют анализу из Task 8 (SAST-отчёт).

| # | Инструмент | Файл | Строка | Severity | Тип | Описание |
|---|-----------|------|--------|----------|-----|----------|
| 1 | Bandit B608 | `app/web.py` | 187 | MEDIUM/LOW | `hardcoded_sql_expressions` | Possible SQL injection via string-based query. Ложное срабатывание — whitelist защита. |
| 2 | Bandit B608 | `app/web.py` | 277 | MEDIUM/LOW | `hardcoded_sql_expressions` | Possible SQL injection via string-based query. Ложное срабатывание — whitelist защита. |
| 3 | Bandit B608 | `app/web.py` | 324 | MEDIUM/MEDIUM | `hardcoded_sql_expressions` | Possible SQL injection via string-based query. Ложное срабатывание — whitelist защита. |
| 4 | Bandit B608 | `app/web.py` | 345 | MEDIUM/LOW | `hardcoded_sql_expressions` | Possible SQL injection via string-based query. Ложное срабатывание — whitelist защита. |
| 5 | Bandit B608 | `app/web.py` | 363 | MEDIUM/MEDIUM | `hardcoded_sql_expressions` | Possible SQL injection via string-based query. Ложное срабатывание — whitelist защита. |
| 6 | Bandit B104 | `app/web.py` | 384 | MEDIUM/MEDIUM | `hardcoded_bind_all_interfaces` | Binding to 0.0.0.0. Приемлемо для Docker. |
| 7 | Semgrep | `templates/add.html` | 28 | WARNING | `django-no-csrf-token` | CSRF токен отсутствует. Реальная уязвимость. |
| 8 | Semgrep | `templates/login.html` | 12 | WARNING | `django-no-csrf-token` | CSRF токен отсутствует. Реальная уязвимость. |
| 9 | Semgrep | `templates/update.html` | 53 | WARNING | `django-no-csrf-token` | CSRF токен отсутствует. Реальная уязвимость. |

**Артефакты:** `sast-reports-<sha>` (bandit_report.json, bandit_report.txt, semgrep_report.json)

---

## Workflow 2: DAST — Develop Branch

**Файл:** [`.github/workflows/dast-develop.yml`](../.github/workflows/dast-develop.yml)  
**Триггер:** Push в `develop`  
**Запущен:** Merge `feature/task10-app` → `develop`

### Шаги пайплайна

```
1. Checkout code
2. Set up Python 3.11 + PostgreSQL 15 (service container)
3. Initialize DB (schema.sql + create_user_and_grants.sql + demo_data.sql)
4. Start Flask app (localhost:5000)
5. ZAP Black-box Baseline Scan → dast_blackbox_report.json/html
6. ZAP Grey-box Scan (Automation Framework) → dast_greybox_report.json/html
7. Upload artifacts (retention: 30 days)
```

### Результаты DAST — Чёрный ящик (develop)

| # | ZAP ID | Тип ошибки | Путь | Risk |
|---|--------|-----------|------|------|
| 1 | 10202 | Absence of Anti-CSRF Tokens | `GET /` | Medium (Low) |
| 2 | 10038 | Content Security Policy Header Not Set | `GET /` | Medium (High) |
| 3 | 10020 | Missing Anti-clickjacking Header | `GET /` | Medium (Medium) |
| 4 | 90004 | Cross-Origin-Embedder-Policy Header Missing | `GET /` | Low (Medium) |
| 5 | 90004 | Cross-Origin-Opener-Policy Header Missing | `GET /` | Low (Medium) |
| 6 | 90004 | Cross-Origin-Resource-Policy Header Missing | `GET /` | Low (Medium) |
| 7 | 10063 | Permissions Policy Header Not Set | `GET /` | Low (Medium) |
| 8 | 10036 | Server Leaks Version Information | `GET /` | Low (High) |
| 9 | 10021 | X-Content-Type-Options Header Missing | `GET /` | Low (Medium) |

### Результаты DAST — Серый ящик (develop)

| # | ZAP ID | Тип ошибки | Путь | Risk |
|---|--------|-----------|------|------|
| 1 | 10202 | Absence of Anti-CSRF Tokens | Все формы | Medium (Low) |
| 2 | 10038 | Content Security Policy Header Not Set | Все страницы | Medium (High) |
| 3 | 10106 | HTTP Only Site | `GET /` | Medium (Medium) |
| 4 | 10020 | Missing Anti-clickjacking Header | Все страницы | Medium (Medium) |
| 5 | 10054 | Cookie without SameSite Attribute | `/main`, `/add`, `/update` | Low (Medium) |
| 6 | 10036 | Server Leaks Version Information | Все страницы | Low (High) |
| 7 | 10021 | X-Content-Type-Options Header Missing | Все страницы | Low (Medium) |

**Артефакты:** `dast-reports-develop-<sha>` (blackbox + greybox JSON/HTML)

---

## Workflow 3: SAST + DAST — Main Branch

**Файл:** [`.github/workflows/sast-dast-main.yml`](../.github/workflows/sast-dast-main.yml)  
**Триггер:** Push/Merge в `main`  
**Запущен:** Merge `develop` → `main`

### Шаги пайплайна

```
Job 1 — SAST:
  1. Checkout code
  2. Set up Python 3.11
  3. Run Bandit → main_bandit_report.json/txt
  4. Run Semgrep → main_semgrep_report.json
  5. Upload SAST artifacts

Job 2 — DAST (запускается после SAST):
  1. Checkout code
  2. Set up Python 3.11 + PostgreSQL 15
  3. Initialize DB + Start Flask
  4. ZAP Black-box Scan → main_dast_blackbox_report.json/html
  5. ZAP Grey-box Scan → main_dast_greybox_report.json/html
  6. Upload DAST artifacts
```

### Результаты SAST (main)

Идентичны результатам feature branch (тот же код).

### Результаты DAST (main)

Идентичны результатам develop branch (то же приложение).

**Артефакты:**
- `main-sast-reports-<sha>` (bandit + semgrep)
- `main-dast-reports-<sha>` (blackbox + greybox ZAP)

---

## Сводная таблица событий CI/CD

| Событие | Ветка | Workflow | SAST | DAST | Артефакты |
|---------|-------|----------|------|------|-----------|
| Push в `feature/task10-app` | `feature/**` | `sast-feature.yml` | ✅ Bandit + Semgrep | ❌ | `sast-reports-<sha>` |
| Push в `develop` | `develop` | `dast-develop.yml` | ❌ | ✅ ZAP (black + grey) | `dast-reports-develop-<sha>` |
| Merge в `main` | `main` | `sast-dast-main.yml` | ✅ Bandit + Semgrep | ✅ ZAP (black + grey) | `main-sast-reports-<sha>` + `main-dast-reports-<sha>` |

---

## Ссылки на GitHub Actions

- **Все запуски:** https://github.com/mmgusev/1/actions
- **SAST (feature):** https://github.com/mmgusev/1/actions/workflows/sast-feature.yml
- **DAST (develop):** https://github.com/mmgusev/1/actions/workflows/dast-develop.yml
- **SAST+DAST (main):** https://github.com/mmgusev/1/actions/workflows/sast-dast-main.yml

---

## Вывод

CI/CD конвейер на GitHub Actions реализует трёхуровневую защиту:

1. **Feature branch (SAST)** — быстрая проверка кода при каждом push разработчика. Bandit и Semgrep выявляют потенциальные уязвимости до попадания кода в интеграционную ветку. Время выполнения: ~2-3 минуты.

2. **Develop branch (DAST)** — динамическое тестирование при интеграции. ZAP запускает реальное приложение с БД и проводит как чёрный (без аутентификации), так и серый ящик (с учётными данными и знанием маршрутов). Время выполнения: ~10-15 минут.

3. **Main branch (SAST + DAST)** — полная проверка перед продуктивным деплоем. Оба инструмента запускаются последовательно (DAST после SAST), что гарантирует максимальное покрытие. Время выполнения: ~15-20 минут.

**Ключевые находки CI/CD:**
- SAST обнаружил 3 реальных CSRF-уязвимости в шаблонах и 6 ложных срабатываний (B608 — whitelist защита)
- DAST (чёрный ящик) нашёл 9 проблем с заголовками безопасности на публичной странице
- DAST (серый ящик) дополнительно обнаружил HTTP Only Site и Cookie без SameSite на аутентифицированных страницах
- SQL-инъекций не обнаружено ни одним инструментом
