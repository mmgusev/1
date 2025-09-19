#!/usr/bin/env python3


import yaml
import getpass
import psycopg2


def load_db_config(config_path="db_config.yaml"):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Файл конфигурации {config_path} не найден!")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Ошибка чтения YAML: {e}")
        exit(1)


def test_connection(host, port, database, user, password, sslmode):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print("\n Успешное подключение!")
        print(f" Версия PostgreSQL: {version}")
        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"\nОшибка подключения: {e}")
        print("Проверьте логин, пароль и доступность базы данных.")
    except Exception as e:
        print(f"\nНеизвестная ошибка: {e}")


def main():
    print("=== PostgreSQL Подключение ===\n")

    config = load_db_config()

    print(f"Используется конфигурация из: db_config.yaml")
    print(f"Хост: {config['host']}")
    print(f"База: {config['database']}")
    print(f"Пользователь: {config['username']}")
    print("-" * 40)

    password = getpass.getpass("Введите пароль для пользователя '{}': ".format(config['username']))

    test_connection(
        host=config['host'],
        port=int(config['port']),           
        database=config['database'],
        user=config['username'],
        password=password,
        sslmode=config.get('sslmode', 'disable')
    )


if __name__ == "__main__":
    main()