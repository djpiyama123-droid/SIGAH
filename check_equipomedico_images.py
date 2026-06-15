import pymysql
import os

DB_HOST   = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT   = int(os.getenv("DB_PORT", "3306"))
DB_USER   = os.getenv("DB_USER", "sigab_user")
DB_PASS   = os.environ["DB_PASS"]

try:
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="dummyequipomedicoimss")
    with conn.cursor() as cur:
        cur.execute("SELECT Serie, Nombre, ruta_equipo FROM equipomedico WHERE ruta_equipo IS NOT NULL AND ruta_equipo != '' LIMIT 10")
        rows = cur.fetchall()
        for r in rows:
            print(r)
        
        cur.execute("SELECT COUNT(*) FROM equipomedico WHERE ruta_equipo IS NOT NULL AND ruta_equipo != ''")
        print(f"Total with images: {cur.fetchone()[0]}")
except Exception as e:
    print(e)
