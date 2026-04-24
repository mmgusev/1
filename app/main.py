# основной CLI-пример, сокращённо
import os, sys, getpass, psycopg2
from psycopg2.extras import RealDictCursor
from whitelist import get_allowed_columns

host = os.getenv('DB_HOST','postgres')
port = int(os.getenv('DB_PORT','5432'))
dbname = os.getenv('DB_NAME','shop_demo')
user = input('DB user: ')
pwd = getpass.getpass('DB password: ')
conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=pwd)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT * FROM products LIMIT 10;")
print(cur.fetchall())
conn.close()