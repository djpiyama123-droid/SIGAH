#!/usr/8bin/env python3
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
        # ── 1. MIGRAR REPORTES (CORRECTIVOS) ─────────────────────
        with src.cursor() as cur:
            cur.execute("""
                SELECT r.*, e.Nombre as equipo_nombre, e.Marca, e.Modelo, e.Area, e.Piso 
                FROM reportes r 
                JOIN equipomedico e ON r.Serie = e.Serie
            """)
            reportes = cur.fetchall()

        orden_counter = 1000  # Start higher to avoid conflicts
        inserted_reportes = 0

        with tgt.cursor() as cur:
            for r in reportes:
                cur.execute("SELECT id FROM equipos WHERE serie = %s", (r["Serie"],))
                eq_row = cur.fetchone()
                if not eq_row:
                    continue
                equipo_id = eq_row["id"]
                
                numero_orden = f"OS-HGR1-R{orden_counter:04d}"
                estado = "cerrada" if r.get("EstadoRep") in ("Resuelto", "Cerrado", "Cerrada", None) else "abierta"

                falla = r.get("FallaReportada") or "Sin descripción"
                fecha = r.get("FechaReporte") or "2025-01-01"
                
                # Check if it already exists to avoid duplicates
                cur.execute("SELECT id FROM ordenes_servicio WHERE falla_reportada = %s AND fecha = %s AND equipo_id = %s", (falla, fecha, equipo_id))
                if cur.fetchone():
                    continue

                cur.execute("""
                    INSERT INTO ordenes_servicio (
                        numero_orden, tipo_formato, equipo_id, equipo_nombre, equipo_marca, equipo_modelo,
                        equipo_serie, area, piso, tipo_mantenimiento,
                        falla_reportada, estado, prioridad, fecha, origen
                    ) VALUES (
                        %s, 'correctivo_corto', %s, %s, %s, %s,
                        %s, %s, %s, 'correctivo',
                        %s, %s, 'media', %s, 'manual'
                    )
                """, (
                    numero_orden, equipo_id,
                    r.get("equipo_nombre"), r.get("Marca"), r.get("Modelo"),
                    r["Serie"], r.get("Area"), r.get("Piso"),
                    falla, estado, fecha
                ))
                orden_counter += 1
                inserted_reportes += 1

        # ── 2. MIGRAR MANTENIMIENTOS (PREVENTIVOS) Y ORDENESIMSS ───
        with src.cursor() as cur:
            cur.execute("""
                SELECT m.*, e.Nombre as equipo_nombre, e.Marca, e.Modelo, e.Area, e.Piso 
                FROM mantenimientos m 
                JOIN equipomedico e ON m.Serie = e.Serie
            """)
            mantenimientos = cur.fetchall()

        inserted_mants = 0
        evidencias_creadas = 0

        with tgt.cursor() as cur:
            for m in mantenimientos:
                cur.execute("SELECT id FROM equipos WHERE serie = %s", (m["Serie"],))
                eq_row = cur.fetchone()
                if not eq_row:
                    continue
                equipo_id = eq_row["id"]
                
                numero_orden = f"OS-HGR1-P{orden_counter:04d}"
                estado = "cerrada" if m.get("estado_postmant") in ("Operativo", "Ok", None) else "cerrada"
                
                fecha = m.get("FechaServicio") or "2025-01-01"
                falla = m.get("falla_reparada") or "Mantenimiento Preventivo"

                # Check if it already exists
                cur.execute("SELECT id FROM ordenes_servicio WHERE falla_reportada = %s AND fecha = %s AND equipo_id = %s AND tipo_mantenimiento = 'preventivo'", (falla, fecha, equipo_id))
                exist_row = cur.fetchone()
                if exist_row:
                    orden_id = exist_row["id"]
                else:
                    cur.execute("""
                        INSERT INTO ordenes_servicio (
                            numero_orden, tipo_formato, equipo_id, equipo_nombre, equipo_marca, equipo_modelo,
                            equipo_serie, area, piso, tipo_mantenimiento,
                            falla_reportada, estado, prioridad, fecha, origen
                        ) VALUES (
                            %s, 'correctivo_corto', %s, %s, %s, %s,
                            %s, %s, %s, 'preventivo',
                            %s, %s, 'media', %s, 'manual'
                        )
                    """, (
                        numero_orden, equipo_id,
                        m.get("equipo_nombre"), m.get("Marca"), m.get("Modelo"),
                        m["Serie"], m.get("Area"), m.get("Piso"),
                        falla, estado, fecha
                    ))
                    orden_id = cur.lastrowid
                    orden_counter += 1
                    inserted_mants += 1

                # Asociar PDF (ruta_orden)
                ruta_orden = m.get("ruta_orden")
                if ruta_orden:
                    # Fix backslashes if any and ensure it starts with /static/uploads
                    ruta_pdf = f"/static/uploads/{ruta_orden.replace('//', '/')}"
                    
                    # Check if evidence already exists for this order
                    cur.execute("SELECT id FROM os_evidencias WHERE orden_id = %s AND ruta_archivo = %s", (orden_id, ruta_pdf))
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO os_evidencias (orden_id, ruta_archivo, tipo, descripcion)
                            VALUES (%s, %s, 'documento', 'Orden de Servicio Legada (IMSS)')
                        """, (orden_id, ruta_pdf))
                        evidencias_creadas += 1

        tgt.commit()
        print(f"Migración Completada:")
        print(f"- Reportes importados: {inserted_reportes}")
        print(f"- Mantenimientos (Preventivos) importados: {inserted_mants}")
        print(f"- Evidencias (PDFs) enlazadas: {evidencias_creadas}")

    finally:
        src.close()
        tgt.close()

if __name__ == "__main__":
    main()
