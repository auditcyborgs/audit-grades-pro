import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def crear_tablas():
    conexion = None
    cursor = None
    try:
        # Ruta del SQLite3 
        ruta_carpeta = os.path.join(BASE_DIR, "bd")
        ruta_bd = os.path.join(ruta_carpeta, "sistema_de_notas.db")

        
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        # 3. Conexión SQLite3
        conexion = sqlite3.connect(ruta_bd)
        cursor = conexion.cursor()

        # 4. Creación de Tablas adaptadas a la sintaxis de SQLite3
        tablas = [
            """
            CREATE TABLE IF NOT EXISTS notas (
                cedula INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante TEXT NOT NULL,
                nota REAL NOT NULL CHECK (nota >= 0 AND nota <= 20),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS auditoria_notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                nota_anterior REAL,
                nota_nueva REAL NOT NULL,
                fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
        ]

        # Ejecución de tabla
        for tabla in tablas:
            cursor.execute(tabla)

        # Guardar los cambios
        conexion.commit()
        print(f"✅ ¡Base de datos creada en: {ruta_bd}!")
        print("✅ ¡Tablas 'notas' y 'auditoria_notas' creadas con éxito!")

    except Exception as e:
        print(f"❌ Error al intentar crear las tablas: {e}")

    finally:
        # Asegurarnos de cerrar las conexiones siempre y cuando se hayan creado
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


if __name__ == "__main__":
    crear_tablas()