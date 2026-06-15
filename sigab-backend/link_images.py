import pymysql
import os

DB_HOST   = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT   = int(os.getenv("DB_PORT", "3306"))
DB_USER   = os.getenv("DB_USER", "sigab_user")
DB_PASS   = os.environ["DB_PASS"]

def main():
    src = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="dummyequipomedicoimss", cursorclass=pymysql.cursors.DictCursor)
    tgt = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="sigab", cursorclass=pymysql.cursors.DictCursor)

    try:
        with src.cursor() as cur:
            cur.execute("SELECT Serie, ruta_equipo FROM equipomedico WHERE ruta_equipo IS NOT NULL AND ruta_equipo != ''")
            images = cur.fetchall()

        print(f"Found {len(images)} images in source database")

        updated = 0
        with tgt.cursor() as cur:
            for img in images:
                serie = img['Serie'].strip()
                ruta = img['ruta_equipo']
                url = f"/static/uploads/{ruta}"
                
                # Check if equipment exists in target db
                cur.execute("UPDATE equipos SET imagen_url = %s WHERE serie = %s", (url, serie))
                if cur.rowcount > 0:
                    updated += cur.rowcount

        tgt.commit()
        print(f"Updated {updated} equipment records with image_url")
    finally:
        src.close()
        tgt.close()

if __name__ == "__main__":
    main()
