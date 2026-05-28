import psycopg2

def crear_tablas():
    try:
        # Base de datos WSL - PostgreSQL 16 
        conexion = psycopg2.connect(
            host="localhost",
            database="sistema_de_notas",  # Asegúrate de haber creado esta BD en pgAdmin primero
            user="postgres",
            password="123456"
        )
        cursor = conexion.cursor()

        # Creacion_Tablas
        tablas = [
            """
            CREATE TABLE IF NOT EXISTS notas (
                id SERIAL PRIMARY KEY,
                estudiante VARCHAR(100) NOT NULL,
                nota NUMERIC(4, 2) NOT NULL CHECK (nota >= 0 AND nota <= 20),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS auditoria_notas (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(100) NOT NULL,
                nota_anterior NUMERIC(4, 2),
                nota_nueva NUMERIC(4, 2) NOT NULL,
                fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        #Ejecutar la creación de cada tabla
        for tabla in tablas:
            cursor.execute(tabla)
        
        # Guardar los cambios de forma permanente
        conexion.commit()
        print("✅ ¡Tablas 'notas' y 'auditoria_notas' creadas con éxito!")

    except Exception as e:
        print(f"❌ Error al intentar crear las tablas: {e}")
        
    finally:
        # Asegurarnos de cerrar las conexiones siempre
        if conexion:
            cursor.close()
            conexion.close()

if __name__ == "__main__":
    crear_tablas()