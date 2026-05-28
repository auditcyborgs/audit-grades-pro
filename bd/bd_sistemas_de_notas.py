import sqlite3

def crear_tablas():
    try:
        # SQLite crea el archivo 'sistema_de_notas.db' automáticamente
        conexion = sqlite3.connect('bd/sistema_de_notas.db')
        cursor = conexion.cursor()

        # SQL para SQLite (hemos quitado 'SERIAL' porque SQLite usa 'INTEGER PRIMARY KEY')
        tablas = [
            """
            CREATE TABLE IF NOT EXISTS notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            """
        ]

        # Ejecutar la creación de cada tabla
        for tabla in tablas:
            cursor.execute(tabla)
        
        # Guardar cambios
        conexion.commit()
        print("✅ ¡Tablas 'notas' y 'auditoria_notas' creadas con éxito en SQLite!")

    except Exception as e:
        print(f"❌ Error al intentar crear las tablas: {e}")
        
    finally:
        if 'conexion' in locals() and conexion:
            conexion.close()

if __name__ == "__main__":
    crear_tablas()
