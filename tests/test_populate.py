import os

import psycopg2


def test_populate_scripts_run():
    """
    Population scripts (schema + demo data) are DDL-heavy (DROP/CREATE/TRUNCATE).
    They must be executed by a DB admin / object owner. In our Docker setup,
    objects are created by the `postgres` user during DB init, so we use
    postgres credentials here by default.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "university_demo"),
        user=os.getenv("DB_ADMIN_USER", "postgres"),
        password=os.getenv("DB_ADMIN_PASS", "postgres"),
    )

    # Our SQL scripts include explicit BEGIN/COMMIT blocks, so we must disable
    # psycopg2 implicit transaction management for this test.
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute(open("schema.sql", encoding="utf-8").read())
            cur.execute(open("demo_data.sql", encoding="utf-8").read())
    finally:
        conn.close()