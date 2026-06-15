#!/usr/bin/env python3
"""Run seed data for SIGAB HGR No.1 zones and equipment."""
import os
import pymysql

conn = pymysql.connect(
    host='127.0.0.1', port=3306, user='sigab_user',
    password=os.environ["DB_PASS"], db='sigab', autocommit=True, charset='utf8mb4'
)
cur = conn.cursor()

# ============================
# ZONAS DEL MAPA HOSPITALARIO
# ============================
zonas = [
    (1, 'Quirófano Central', 'QUIROFANO', '2do Piso', '#0a1f12', '#16a34a20', 1),
    (2, 'UCI Adultos', 'UCI_ADULTOS', '2do Piso', '#0a1829', '#2563eb20', 2),
    (3, 'UCIN', 'UCIN', '2do Piso', '#0a1829', '#0891b220', 3),
    (4, 'Imagenología (TAC/X-Ray)', 'IMAGENOLOGIA', '1er Piso', '#1c1400', '#d9770620', 4),
    (5, 'Urgencias', 'URGENCIAS', '1er Piso', '#1c0000', '#dc262620', 5),
    (6, 'Laboratorio Clínico', 'LABORATORIO', '1er Piso', '#0f0f1a', '#7c3aed20', 6),
    (7, 'CEYE (Esterilización)', 'CEYE', '1er Piso', '#0f1a15', '#05966920', 7),
    (8, 'Hospitalización Piso 2', 'HOSPITALIZACION', '2do Piso', '#0f0f0f', '#47556920', 8),
    (9, 'Anestesiología', 'ANESTESIA', '2do Piso', '#12100a', '#b4530020', 9),
]

for z in zonas:
    cur.execute(
        'INSERT IGNORE INTO zonas_mapa (id, nombre, codigo, piso, color_bg, color_borde, orden) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)', z
    )
print(f'Zonas insertadas: {len(zonas)}')

# ================================================
# UPDATE existing equipos
# ================================================
updates = [
    ('82-0751', 1, 18, 28, 'arco_c', 'III', 'alta', 'operativo', '2025-11-15', '2026-05-15'),
    ('82-0745', 1, 42, 28, 'arco_c', 'III', 'alta', 'operativo', '2025-10-20', '2026-04-20'),
    ('82-0744', 1, 68, 28, 'arco_c', 'III', 'alta', 'operativo', '2025-12-01', '2026-06-01'),
    ('SK416381232HA', 1, 28, 68, 'monitor', 'III', 'alta', 'operativo', '2026-03-24', '2026-09-24'),
    ('STF244011695A', 1, 58, 68, 'monitor', 'III', 'alta', 'operativo', '2025-09-10', '2026-03-10'),
]
for serie, zona_id, px, py, tipo, clase, crit, estado, ult, prox in updates:
    cur.execute(
        'UPDATE equipos SET zona_id=%s, pos_x=%s, pos_y=%s, '
        'tipo_equipo=%s, clase_cofepris=%s, criticidad=%s, estado=%s, '
        'fecha_ultimo_mantenimiento=%s, fecha_proximo_mantenimiento=%s '
        'WHERE serie=%s',
        (zona_id, px, py, tipo, clase, crit, estado, ult, prox, serie)
    )
    print(f'  Updated {serie}: {cur.rowcount} rows')

# Update UCIN ventilador
cur.execute(
    'UPDATE equipos SET zona_id=3, pos_x=38, pos_y=35, '
    "tipo_equipo='ventilador', clase_cofepris='III', criticidad='alta', "
    "estado='en_mantenimiento', "
    "numero_contrato_servicio='050GYR019N09125-019-00', "
    "proveedor_servicio='Servicios de Ingeniería en Medicina S.A. de C.V.' "
    "WHERE serie='MB203775'"
)
print(f'  Updated MB203775: {cur.rowcount} rows')

# ================================================
# INSERT new equipos
# ================================================
INSERT_SQL = (
    'INSERT IGNORE INTO equipos '
    '(serie, inventario, nombre, marca, modelo, ubicacion, piso, area, estado, '
    'criticidad, zona_id, pos_x, pos_y, tipo_equipo, clase_cofepris, '
    'fecha_compra, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento) '
    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
)

new_equipos = [
    # Quirófano
    ('DRG-2022-1012','1012','Máquina de Anestesia','Dräger','Fabius GS','Hospital General Regional No.1','Segundo','Quirófano Central','operativo','alta',1,82,68,'anestesia','III','2022-11-30','2023-12-14','2026-06-14'),
    ('ZOL-AED-QX01','1021','Desfibrilador Bifásico','Zoll','R Series','Hospital General Regional No.1','Segundo','Quirófano Central','operativo','alta',1,15,68,'desfibrilador','III','2020-05-10','2025-11-10','2026-05-10'),
    ('BAX-INF-QX01','1035','Bomba de Infusión','Baxter','Sigma Spectrum','Hospital General Regional No.1','Segundo','Quirófano Central','operativo','media',1,48,68,'bomba_infusion','II','2020-08-15','2025-08-15','2026-02-15'),
    # UCI
    ('GE-UCI-B650-A1','2010','Monitor de Signos Vitales','GE','CARESCAPE B650','Hospital General Regional No.1','Segundo','UCI Adultos','operativo','alta',2,18,25,'monitor','III','2019-03-01','2025-09-01','2026-03-01'),
    ('GE-UCI-B650-A2','2011','Monitor de Signos Vitales','GE','CARESCAPE B650','Hospital General Regional No.1','Segundo','UCI Adultos','operativo','alta',2,50,25,'monitor','III','2019-03-01','2025-09-01','2026-03-01'),
    ('GE-UCI-B650-A3','2012','Monitor de Signos Vitales','GE','CARESCAPE B650','Hospital General Regional No.1','Segundo','UCI Adultos','en_mantenimiento','alta',2,82,25,'monitor','III','2019-03-01','2025-07-15','2026-01-15'),
    ('VYR-UCI-VNT-01','2020','Ventilador Mecánico','Vyaire Medical','Bellavista 1000','Hospital General Regional No.1','Segundo','UCI Adultos','operativo','alta',2,25,68,'ventilador','III','2020-01-15','2025-07-15','2026-01-15'),
    ('VYR-UCI-VNT-02','2021','Ventilador Mecánico','Vyaire Medical','Bellavista 1000','Hospital General Regional No.1','Segundo','UCI Adultos','operativo','alta',2,60,68,'ventilador','III','2020-01-15','2025-07-15','2026-01-15'),
    ('BAX-UCI-INF-01','2031','Bomba de Infusión','Baxter','Sigma Spectrum','Hospital General Regional No.1','Segundo','UCI Adultos','operativo','media',2,42,82,'bomba_infusion','II','2021-06-10','2025-12-10','2026-06-10'),
    # UCIN
    ('ATM-INC-UCIN-01','3001','Incubadora Dual','Atom Medical','Omnibred IV','Hospital General Regional No.1','Segundo','UCIN','operativo','alta',3,18,65,'incubadora','III','2018-04-20','2026-03-26','2026-09-26'),
    ('GE-GIR-UCIN-02','3002','Incubadora Neonatal','GE Healthcare','Giraffe OmniBed','Hospital General Regional No.1','Segundo','UCIN','operativo','alta',3,62,65,'incubadora','III','2019-06-15','2025-12-15','2026-06-15'),
    ('GE-UCIN-MON-01','3010','Monitor Neonatal','GE','CARESCAPE B650','Hospital General Regional No.1','Segundo','UCIN','operativo','alta',3,82,25,'monitor','III','2020-02-10','2025-08-10','2026-02-10'),
    # Imagenología
    ('GE-TAC-IMG-001','4001','Tomógrafo Computarizado','GE Healthcare','Revolution EVO','Hospital General Regional No.1','Primero','Imagenología','operativo','alta',4,30,40,'rayos_x','III','2017-09-01','2025-09-01','2026-03-01'),
    ('PHL-RX-IMG-001','4002','Equipo de Rayos X Digital','Philips','DigitalDiagnost C90','Hospital General Regional No.1','Primero','Imagenología','operativo','alta',4,65,40,'rayos_x','III','2018-11-15','2025-11-15','2026-05-15'),
    ('SIE-US-IMG-001','4010','Ultrasonido','Siemens','ACUSON P500','Hospital General Regional No.1','Primero','Imagenología','operativo','media',4,48,78,'ultrasonido','II','2020-04-05','2025-10-05','2026-04-05'),
    # Urgencias
    ('PHL-URG-MON-01','7001','Monitor de Signos Vitales','Philips','IntelliVue MP30','Hospital General Regional No.1','Primero','Urgencias','operativo','alta',5,22,30,'monitor','III','2018-05-20','2025-11-20','2026-05-20'),
    ('PHL-URG-MON-02','7002','Monitor de Signos Vitales','Philips','IntelliVue MP30','Hospital General Regional No.1','Primero','Urgencias','operativo','alta',5,58,30,'monitor','III','2018-05-20','2025-11-20','2026-05-20'),
    ('ZOL-URG-DEF-01','7010','Desfibrilador','Zoll','R Series','Hospital General Regional No.1','Primero','Urgencias','fuera_servicio','alta',5,40,72,'desfibrilador','III','2020-09-15','2025-09-15','2026-03-15'),
    # Laboratorio
    ('SYS-HEM-LAB-01','5001','Analizador Hematológico','Sysmex','XN-1000','Hospital General Regional No.1','Primero','Laboratorio Clínico','operativo','media',6,28,42,'laboratorio','II','2019-07-20',None,None),
    ('BKM-QC-LAB-01','5010','Analizador de Química Clínica','Beckman Coulter','AU480','Hospital General Regional No.1','Primero','Laboratorio Clínico','operativo','media',6,68,42,'laboratorio','II','2018-12-10',None,None),
    ('EPP-CENT-LAB-01','5002','Centrífuga de Laboratorio','Eppendorf','5810 R','Hospital General Regional No.1','Primero','Laboratorio Clínico','operativo','baja',6,48,78,'laboratorio','I','2020-03-15',None,None),
    # CEYE
    ('MEL-AUT-CEYE-01','6001','Autoclave de Vapor','Melag','MELAG 24B','Hospital General Regional No.1','Primero','CEYE','operativo','alta',7,32,45,'autoclave','II','2019-01-10','2025-07-10','2026-01-10'),
    ('MEL-AUT-CEYE-02','6002','Autoclave de Vapor','Melag','MELAG 24B','Hospital General Regional No.1','Primero','CEYE','en_mantenimiento','alta',7,68,45,'autoclave','II','2019-01-10','2025-03-01','2025-09-01'),
    # Hospitalización
    ('PHL-HOS-MON-01','8001','Monitor de Signos Vitales','Philips','IntelliVue MP20','Hospital General Regional No.1','Segundo','Hospitalización','operativo','media',8,14,50,'monitor','II','2019-08-10',None,None),
    ('PHL-HOS-MON-02','8002','Monitor de Signos Vitales','Philips','IntelliVue MP20','Hospital General Regional No.1','Segundo','Hospitalización','operativo','media',8,36,50,'monitor','II','2019-08-10',None,None),
    ('PHL-HOS-MON-03','8003','Monitor de Signos Vitales','Philips','IntelliVue MP20','Hospital General Regional No.1','Segundo','Hospitalización','operativo','media',8,58,50,'monitor','II','2019-08-10',None,None),
    ('BAX-HOS-INF-01','8010','Bomba de Infusión','Baxter','Sigma Spectrum','Hospital General Regional No.1','Segundo','Hospitalización','operativo','media',8,78,50,'bomba_infusion','II','2021-02-20',None,None),
]

inserted = 0
for eq in new_equipos:
    try:
        cur.execute(INSERT_SQL, eq)
        if cur.rowcount > 0:
            inserted += 1
    except Exception as e:
        print(f'  Error inserting {eq[0]}: {e}')

print(f'New equipos inserted: {inserted}')

# Verification
cur.execute(
    'SELECT z.nombre, COUNT(e.id) AS equipos, '
    "SUM(e.estado='operativo') AS op, "
    "SUM(e.estado='en_mantenimiento') AS mant, "
    "SUM(e.estado='fuera_servicio') AS fs "
    'FROM zonas_mapa z '
    'LEFT JOIN equipos e ON e.zona_id = z.id '
    'GROUP BY z.id, z.nombre '
    'ORDER BY z.orden'
)
print('\n--- VERIFICATION ---')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} equipos (op={r[2]}, mant={r[3]}, fs={r[4]})')

conn.close()
print('\nSeed complete!')
