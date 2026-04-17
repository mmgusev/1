#!/usr/bin/env python3

import os
import time
import sys
import logging
from datetime import datetime
import psycopg2
import hvac

# ========================
# Конфигурация через env
# ========================

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_SSLMODE = os.getenv("DB_SSLMODE", "disable")

INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "300"))  # 5 минут по умолчанию

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "")

# Vault configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "secret/database")
VAULT_ROLE_ID_FILE = "/vault/file/role-id"
VAULT_SECRET_ID_FILE = "/vault/file/secret-id"

# ========================
# Настройка логирования
# ========================

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# файл, если указан
if LOG_FILE_PATH:
    # Создаём папку, если не существует
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# ========================
# Vault клиент
# ========================

def get_vault_client():
    """Создает и возвращает клиент Vault с AppRole аутентификацией"""
    try:
        # Читаем role-id и secret-id из файлов
        if not os.path.exists(VAULT_ROLE_ID_FILE):
            logger.error(f"[VAULT] Файл role-id не найден: {VAULT_ROLE_ID_FILE}")
            return None
            
        if not os.path.exists(VAULT_SECRET_ID_FILE):
            logger.error(f"[VAULT] Файл secret-id не найден: {VAULT_SECRET_ID_FILE}")
            return None
        
        with open(VAULT_ROLE_ID_FILE, 'r') as f:
            role_id = f.read().strip()
            
        with open(VAULT_SECRET_ID_FILE, 'r') as f:
            secret_id = f.read().strip()
        
        logger.info(f"[VAULT] Role ID: {role_id[:8]}...")
        
        # Создаем клиент Vault
        client = hvac.Client(url=VAULT_ADDR)
        
        # Аутентификация через AppRole
        auth_response = client.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id
        )
        
        if not client.is_authenticated():
            logger.error("[VAULT] Не удалось аутентифицироваться через AppRole")
            return None
            
        logger.info("[VAULT] Успешная аутентификация через AppRole")
        return client
        
    except FileNotFoundError as e:
        logger.error(f"[VAULT] Файл не найден: {e}")
        return None
    except Exception as e:
        logger.error(f"[VAULT] Ошибка подключения к Vault: {e}")
        return None

def get_db_credentials_from_vault(client):
    """Получает учетные данные БД из Vault"""
    try:
        # Читаем секрет из Vault
        secret_response = client.secrets.kv.v2.read_secret_version(
            path='database',
            mount_point='secret',
            raise_on_deleted_version=False
        )
        
        data = secret_response['data']['data']
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            logger.error("[VAULT] Секрет не содержит username или password")
            return None, None
            
        logger.info(f"[VAULT] Успешно получены учетные данные для пользователя: {username}")
        return username, password
        
    except Exception as e:
        logger.error(f"[VAULT] Ошибка при получении секрета: {e}")
        return None, None

# ========================
# Функция пинга
# ========================

def ping_database():
    try:
        # Получаем клиент Vault с AppRole аутентификацией
        vault_client = get_vault_client()
        
        if not vault_client:
            logger.error("[ОШИБКА] Не удалось подключиться к Vault")
            return
        
        # Получаем учетные данные из Vault
        db_user, db_password = get_db_credentials_from_vault(vault_client)
        
        if not db_user or not db_password:
            logger.error("[ОШИБКА] Не удалось получить учетные данные из Vault")
            return
        
        # Подключаемся к БД с учетными данными из Vault
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=db_user,
            password=db_password,
            sslmode=DB_SSLMODE
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if "PostgreSQL" not in version:
            logger.info(f"[НЕТИПИЧНЫЙ ОТВЕТ] Версия БД: {version}")
        else:
            logger.info(f"[УСПЕХ] Подключение успешно. Версия: {version}")

    except psycopg2.OperationalError as e:
        logger.error(f"[ОШИБКА ПОДКЛЮЧЕНИЯ] {e}")
    except Exception as e:
        logger.error(f"[НЕИЗВЕСТНАЯ ОШИБКА] {e}")


# ========================
# Главный цикл
# ========================

if __name__ == "__main__":
    logger.info("=== Запуск PostgreSQL Pinger Service с Vault (AppRole) ===")
    logger.info(f"Цикл проверки каждые {INTERVAL_SECONDS} секунд")
    logger.info(f"Подключение к {DB_HOST}:{DB_PORT}/{DB_NAME}")
    logger.info(f"Vault адрес: {VAULT_ADDR}")
    logger.info(f"Vault секрет: {VAULT_SECRET_PATH}")
    logger.info(f"AppRole credentials: {VAULT_ROLE_ID_FILE}, {VAULT_SECRET_ID_FILE}")

    while True:
        try:
            ping_database()
        except Exception as e:
            logger.error(f"[КРИТИЧЕСКАЯ ОШИБКА ВНЕ ПОДКЛЮЧЕНИЯ] {e}")
        finally:
            time.sleep(INTERVAL_SECONDS)
