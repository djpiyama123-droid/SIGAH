import pymysql
import os

DB_HOST   = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT   = int(os.getenv("DB_PORT", "3306"))
DB_USER   = os.getenv("DB_USER", "sigab_user")
DB_PASS   = os.environ["DB_PASS"]

try:
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS)
    with conn.cursor() as cur:
        cur.execute("SHOW DATABASES")
        dbs = cur.fetchall()
        for db in dbs:
            print(db[0])
            
        cur.execute("USE dummyequipomedicoimss;")
        cur.execute("SHOW TABLES;")
        tables = cur.fetchall()
        for t in tables:
            print("Table:", t[0])
            if t[0] == "equipomedico":
                cur.execute("SHOW COLUMNS FROM equipomedico")
                cols = cur.fetchall()
                print("Columns:", [c[0] for c in cols])
except Exception as e:
    print(e)
