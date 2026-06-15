import asyncio
import aiomysql
import sys
import os

sys.path.append(os.getcwd())
from config import DB_CONFIG
from auth.password import hash_password

async def seed():
    conn = await aiomysql.connect(**DB_CONFIG)
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM usuarios WHERE matricula = %s", ("sigab_user",))
            if await cur.fetchone():
                print("El usuario 'sigab_user' ya existe.")
                return
            
            ph = hash_password(os.environ["SIGAB_AUDIT_PASSWORD"])
            await cur.execute(
                "INSERT INTO usuarios (nombre, matricula, rol, activo, password_hash) VALUES (%s, %s, %s, %s, %s)",
                ("Usuario SIGAB Audit", "sigab_user", "admin", 1, ph)
            )
            print("Usuario 'sigab_user' creado con éxito para auditoría.")
            await conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(seed())
