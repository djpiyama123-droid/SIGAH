#!/usr/bin/env python3
import pymysql
import os
import json

DB_HOST   = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT   = int(os.getenv("DB_PORT", "3306"))
DB_USER   = os.getenv("DB_USER", "sigab_user")
DB_PASS   = os.environ["DB_PASS"]

def main():
    src = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="dummyequipomedicoimss", cursorclass=pymysql.cursors.DictCursor)
    tgt = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="sigab", cursorclass=pymysql.cursors.DictCursor)

    try:
        with src.cursor() as cur:
            cur.execute("""
                SELECT Serie, ruta_equipo, ruta_serie, ruta_inventario 
                FROM equipomedico 
                WHERE ruta_equipo IS NOT NULL 
                   OR ruta_serie IS NOT NULL 
                   OR ruta_inventario IS NOT NULL
            """)
            images = cur.fetchall()

        print(f"Found {len(images)} equipment with images in source")

        updated = 0
        with tgt.cursor() as cur:
            for row in images:
                serie = row['Serie'].strip()
                paths = []
                for k in ['ruta_equipo', 'ruta_serie', 'ruta_inventario']:
                    if row[k]:
                        paths.append(f"/static/uploads/{row[k].replace('//', '/')}")
                
                if paths:
                    fotos_json = json.dumps(paths)
                    # We can store the first image in imagen_url and all in fotos
                    cur.execute("UPDATE equipos SET imagen_url = %s, fotos = %s WHERE serie = %s", (paths[0], fotos_json, serie))
                    if cur.rowcount > 0:
                        updated += cur.rowcount

        tgt.commit()
        print(f"Updated {updated} equipment records with fotos json")
    finally:
        src.close()
        tgt.close()

if __name__ == "__main__":
    main()
