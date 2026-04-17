# PostgreSQL Pinger с HashiCorp Vault

Проект демонстрирует интеграцию PostgreSQL, Python-приложения и HashiCorp Vault для безопасного хранения секретов.

## Архитектура

Проект состоит из трех сервисов:

1. **PostgreSQL** - база данных с пользователем `app_user`
2. **HashiCorp Vault** - хранилище секретов в режиме разработки
3. **Python Pinger** - приложение, которое получает учетные данные из Vault и подключается к БД

## Особенности реализации

### ✅ Vault в режиме разработки
- Запускается с root token: `root`
- Доступен на порту `8200`
- Volume `/vault/file` смонтирован в `./vault-data` для доступа к файлам вне контейнера

### ✅ AppRole авторизация
- Включен метод авторизации AppRole
- Создана роль `pinger-role` с политикой `pinger-policy`
- Role ID и Secret ID сохраняются в `./vault-data/approle-credentials.txt`

### ✅ Политика безопасности
Политика `pinger-policy` разрешает только чтение секрета:
```hcl
path "secret/data/database" {
  capabilities = ["read"]
}
```

### ✅ Секреты БД
Секрет хранится по пути `secret/database` и содержит:
- `username`: app_user
- `password`: secure_password_123

### ✅ Python клиент
Приложение использует библиотеку `hvac` для:
- Аутентификации в Vault с помощью root token
- Получения учетных данных БД перед каждым запросом
- Подключения к PostgreSQL с полученными учетными данными

## Быстрый старт

### 1. Запуск проекта

```bash
cd 2
docker-compose up -d
```

### 2. Инициализация Vault

```bash
docker exec -i vault_dev sh < vault-init.sh
```

Скрипт выполнит:
- Включение AppRole
- Создание политики `pinger-policy`
- Создание секрета с учетными данными БД
- Создание AppRole `pinger-role`
- Генерацию Role ID и Secret ID

### 3. Перезапуск приложения

```bash
docker-compose restart app
```

### 4. Проверка логов

```bash
docker-compose logs -f app
```

Вы должны увидеть:
```
[VAULT] Успешная аутентификация в Vault
[VAULT] Успешно получены учетные данные для пользователя: app_user
[УСПЕХ] Подключение успешно. Версия: PostgreSQL 17.9
```

## Тестирование

### Тест с правильными учетными данными

Приложение успешно подключается к БД:
```bash
docker-compose logs app | grep "УСПЕХ"
```

### Тест с неверными учетными данными

1. Измените пароль в Vault:
```bash
docker exec vault_dev vault kv put secret/database username=app_user password=wrong_password
```

2. Перезапустите приложение:
```bash
docker-compose restart app
```

3. Проверьте логи:
```bash
docker-compose logs app | grep "ОШИБКА"
```

Вы увидите ошибку аутентификации PostgreSQL.

4. Верните правильный пароль:
```bash
docker exec vault_dev vault kv put secret/database username=app_user password=secure_password_123
docker-compose restart app
```

## Структура проекта

```
2/
├── docker-compose.yaml       # Конфигурация всех сервисов
├── .env                       # Переменные окружения
├── vault-init.sh             # Скрипт инициализации Vault
├── vault-data/               # Volume для Vault (создается автоматически)
│   └── approle-credentials.txt
├── app/
│   ├── Dockerfile
│   ├── main.py               # Python приложение с интеграцией Vault
│   ├── requirements.txt      # Зависимости (psycopg2, hvac, PyYAML)
│   └── logs/                 # Логи приложения
├── postgres-init/
│   └── Dockerfile            # Кастомный образ PostgreSQL
└── postgres-sql/
    └── init.sql              # SQL скрипт инициализации БД
```

## Переменные окружения

### Для приложения (.env)

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=mydb
DB_SSLMODE=disable

# Application
PING_INTERVAL_SECONDS=300
LOG_FILE_PATH=/app/logs/pinger.log

# Vault
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=root
VAULT_ROLE_ID=
VAULT_SECRET_PATH=secret/database
```

## Vault CLI команды

### Просмотр секрета
```bash
docker exec vault_dev vault kv get secret/database
```

### Обновление секрета
```bash
docker exec vault_dev vault kv put secret/database username=app_user password=new_password
```

### Просмотр политики
```bash
docker exec vault_dev vault policy read pinger-policy
```

### Просмотр AppRole
```bash
docker exec vault_dev vault read auth/approle/role/pinger-role
```

### Получение Role ID
```bash
docker exec vault_dev vault read auth/approle/role/pinger-role/role-id
```

## Остановка проекта

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
rm -rf vault-data app/logs
```


cd 2
docker-compose up -d
docker exec -i vault_dev sh < vault-init.sh
docker-compose restart app
docker-compose logs -f app