#!/usr/bin/env python3
"""
Безопасное приложение для подключения к PostgreSQL.
Считывает настройки из YAML-файла, запрашивает логин/пароль у пользователя,
и формирует DSN без возможности SQL-инъекции или внедрения опций.
"""

import yaml
import getpass
import psycopg2
from urllib.parse import quote_plus


def load_db_config(config_path="db_config.yaml"):
    """Безопасно загружает конфигурацию из YAML."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Файл конфигурации {config_path} не найден!")
        exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Ошибка чтения YAML: {e}")
        exit(1)


def build_dsn(config, user_input_password):
    """
    Безопасно собирает DSN из конфига и введённого пароля.
    Использует urllib.parse.quote_plus для экранирования специальных символов.
    Никаких строковых конкатенаций — только параметризация.
    """
    required_keys = ['host', 'port', 'database']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Отсутствует обязательный параметр: {key}")

    # Экранируем все значения, чтобы предотвратить инъекции
    host = quote_plus(config['host'])
    port = quote_plus(str(config['port']))
    database = quote_plus(config['database'])
    username = quote_plus(config['username'])
    password = quote_plus(user_input_password)  # Пароль от пользователя
    sslmode = quote_plus(config.get('sslmode', 'disable'))

    dsn = f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
    return dsn


def test_connection(dsn):
    """Подключается к БД и выполняет SELECT VERSION()"""
    try:
        conn = psycopg2.connect(dsn)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print("\n✅ Успешное подключение!")
        print(f"📊 Версия PostgreSQL: {version}")
        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"\n❌ Ошибка подключения: {e}")
        print("Проверьте логин, пароль и доступность базы данных.")
    except Exception as e:
        print(f"\n❌ Неизвестная ошибка: {e}")


def main():
    print("=== PostgreSQL Подключение ===\n")

    # 1. Загрузка конфига из файла
    config = load_db_config()

    print(f"Используется конфигурация из: db_config.yaml")
    print(f"Хост: {config['host']}")
    print(f"База: {config['database']}")
    print(f"Пользователь: {config['username']}")
    print("-" * 40)

    # 2. Безопасный ввод пароля (не отображается в терминале)
    password = getpass.getpass("Введите пароль для пользователя '{}': ".format(config['username']))

    # 3. Безопасная сборка DSN — никаких ручных конкатенаций!
    dsn = build_dsn(config, password)

    # 4. Подключение и выполнение запроса
    test_connection(dsn)


if __name__ == "__main__":
    main()