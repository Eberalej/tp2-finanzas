import sqlite3
import os

RUTA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
NOMBRE_BD = os.path.join(RUTA_PROYECTO, "finanzas.db")


def conectar():
    conexion = sqlite3.connect(NOMBRE_BD)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = conectar()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    crear_tablas()
    print("Base de datos lista")