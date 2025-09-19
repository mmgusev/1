#!/usr/bin/env python3

import os
import time
import sys
import logging
from datetime import datetime
import psycopg2

# ========================
# Конфигурация через env
# ========================

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSLMODE = os.getenv("DB_SSLMODE", "disable")

INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "300"))  # 5 минут по умолчанию

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "")

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
# Функция пинга
# ========================

def ping_database():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
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
    logger.info("=== Запуск PostgreSQL Pinger Service ===")
    logger.info(f"Цикл проверки каждые {INTERVAL_SECONDS} секунд")
    logger.info(f"Подключение к {DB_HOST}:{DB_PORT}/{DB_NAME} как {DB_USER}")

    while True:
        try:
            ping_database()
        except Exception as e:
            logger.error(f"[КРИТИЧЕСКАЯ ОШИБКА ВНЕ ПОДКЛЮЧЕНИЯ] {e}")
        finally:
            time.sleep(INTERVAL_SECONDS)