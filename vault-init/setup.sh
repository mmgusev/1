#!/bin/bash

# Скрипт для инициализации Vault с AppRole и секретами

set -e

echo "=== Инициализация Vault ==="

# Ждем, пока Vault станет доступен
echo "Ожидание запуска Vault..."
sleep 5

export VAULT_ADDR='http://vault:8200'
export VAULT_TOKEN='root'

# 1. Включаем метод авторизации AppRole
echo "1. Включение метода авторизации AppRole..."
vault auth enable approle || echo "AppRole уже включен"

# 2. Создаем политику для чтения секретов БД
echo "2. Создание политики для чтения секретов..."
vault policy write pinger-policy - <<EOF
path "secret/data/database" {
  capabilities = ["read"]
}
EOF

# 3. Создаем секрет с учетными данными БД
echo "3. Создание секрета с учетными данными БД..."
vault kv put secret/database \
  username=app_user \
  password=secure_password_123

# 4. Создаем AppRole для сервиса pinger
echo "4. Создание AppRole 'pinger-role'..."
vault write auth/approle/role/pinger-role \
  token_policies="pinger-policy" \
  token_ttl=1h \
  token_max_ttl=4h

# 5. Получаем role-id
echo "5. Получение role-id..."
ROLE_ID=$(vault read -field=role_id auth/approle/role/pinger-role/role-id)
echo "Role ID: ${ROLE_ID:0:8}... (скрыт для безопасности)"

# 6. Генерируем secret-id
echo "6. Генерация secret-id..."
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/pinger-role/secret-id)
echo "Secret ID: ******** (скрыт для безопасности)"

# Сохраняем role-id и secret-id
echo "7. Сохранение учетных данных..."

# Сохраняем в /vault/file для доступа с хоста и из контейнеров
cat > /vault/file/approle-credentials.txt <<EOF
VAULT_ROLE_ID=$ROLE_ID
VAULT_SECRET_ID=$SECRET_ID
EOF

# Сохраняем отдельные файлы для удобства
echo "$ROLE_ID" > /vault/file/role-id
echo "$SECRET_ID" > /vault/file/secret-id

echo ""
echo "=== Vault успешно инициализирован ==="
echo "Role ID: ${ROLE_ID:0:8}... (полный ID сохранен в /vault/file/role-id)"
echo "Secret ID: ******** (сохранен в /vault/file/secret-id)"
echo ""
echo "Учетные данные сохранены в /vault/file/"
