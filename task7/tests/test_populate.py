import os, psycopg2
conn = psycopg2.connect(host=os.getenv('DB_HOST','postgres'), port=5432, dbname=os.getenv('DB_NAME','shop_demo'), user=os.getenv('DB_USER','app_user'), password=os.getenv('DB_PASS','app_pass_ChangeMe!'))
cur = conn.cursor()
cur.execute(open('schema.sql').read())
cur.execute(open('demo_data.sql').read())
conn.commit()
cur.close()
conn.close()