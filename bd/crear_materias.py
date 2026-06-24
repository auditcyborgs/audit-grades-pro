import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bd", "sistema_de_notas.db")

def crear_estructura_materias():
    """Crea la tabla materias y actualiza la estructura de notas"""
    try:
        # Asegurar que la carpeta existe
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Activar llaves foráneas
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Crear tabla materias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materias (
                codigo_materia TEXT PRIMARY KEY,
                nombre_materia TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                creditos INTEGER DEFAULT 3,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar materias por defecto
        materias_default = [
            ('MAT-01', 'Matemáticas', 'Matemáticas básicas y avanzadas', 4),
            ('FIS-01', 'Física', 'Física general', 4),
            ('PRO-01', 'Programación', 'Fundamentos de programación', 4),
            ('QUI-01', 'Química', 'Química general', 3)
        ]
        
        for mat in materias_default:
            cursor.execute('''
                INSERT OR IGNORE INTO materias (codigo_materia, nombre_materia, descripcion, creditos)
                VALUES (?, ?, ?, ?)
            ''', mat)
        
        # Verificar si la tabla notas tiene la columna codigo_materia
        cursor.execute("PRAGMA table_info(notas)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'codigo_materia' not in columnas:
            print("Agregando columna codigo_materia a la tabla notas...")
            cursor.execute("ALTER TABLE notas ADD COLUMN codigo_materia TEXT DEFAULT 'MAT-01'")
            cursor.execute("UPDATE notas SET codigo_materia = 'MAT-01' WHERE codigo_materia IS NULL")
            print("✅ Columna agregada")
        
        conn.commit()
        
        # Mostrar materias disponibles
        cursor.execute("SELECT codigo_materia, nombre_materia, creditos FROM materias")
        materias = cursor.fetchall()
        print("\n" + "="*50)
        print("MATERIAS DISPONIBLES:")
        print("="*50)
        for codigo, nombre, creditos in materias:
            print(f"   • {codigo} - {nombre} ({creditos} créditos)")
        print("="*50)
        
        conn.close()
        print("\n✅ Estructura creada/actualizada exitosamente")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error en la base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("Preparando base de datos para materias...")
    crear_estructura_materias()
    print("\n Ahora puedes ejecutar front.py normalmente")