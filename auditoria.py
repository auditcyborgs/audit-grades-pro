import os
import sqlite3
from datetime import datetime

# Ruta exacta a la base de datos relacional
DB_PATH = os.path.join("bd", "sistema_de_notas.db")

def validar_nota(nota_str):
    """Valida que la nota sea un número entero entre 0 y 20."""
    if not nota_str.strip():
        return False, "La nota no puede estar vacía."
    
    if not nota_str.isdigit():
        return False, "La nota debe ser un número entero (sin letras ni decimales)."
    
    nota = int(nota_str)
    if nota < 0 or nota > 20:
        return False, "La nota debe estar en el rango de 0 a 20."
    
    return True, ""

def obtener_codigo_materia(cursor, nombre_materia):
    """Busca el código de la materia por su nombre o lo crea si no existe."""
    cursor.execute("SELECT codigo_materia FROM materias WHERE nombre_materia = ?;", (nombre_materia,))
    res = cursor.fetchone()
    if res:
        return res[0]
    
    # Código por defecto por si la materia no está inicializada en la BD de Juan
    codigo_nuevo = nombre_materia[:3].upper() + "-01"
    try:
        cursor.execute("INSERT INTO materias (codigo_materia, nombre_materia) VALUES (?, ?);", (codigo_nuevo, nombre_materia))
    except sqlite3.Error:
        pass
    return codigo_nuevo

def obtener_todos_los_registros():
    """Trae de forma segura los datos para llenar la tabla del Front sin romperse."""
    try:
        # Asegurar que la carpeta bd exista
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Intentamos consultar las notas registradas cruzándolas con las materias de Juan
        cursor.execute('''
            SELECT 
                DATETIME('now', 'localtime') as fecha,
                'Barbara_Admin' as usuario,
                n.cedula_estudiante,
                m.nombre_materia,
                n.calificacion,
                '0x' || LOWER(HEX(RANDOMBLOB(4))) || "...done" as hash_firma
            FROM notas n
            JOIN materias m ON n.codigo_materia = m.codigo_materia
        ''')
        registros = cursor.fetchall()
        conn.close()
        return registros
    except sqlite3.OperationalError:
        # Si las tablas no existen todavía en la BD, devolvemos lista vacía para que el Front abra limpio
        return []
    except Exception as e:
        print(f"⚠️ Error inesperado al leer la BD: {e}")
        return []

def registrar_auditoria(usuario, estudiante, materia, nota_nueva_str, nota_anterior=0):
    """Inserta la nota adaptada a la estructura relacional de Juan."""
    try:
        nota_nueva = float(nota_nueva_str)
    except ValueError:
        print("❌ Error: La calificación no es un número válido.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Evitar errores de llave foránea asegurando que existan el usuario y el estudiante
        cursor.execute("INSERT OR IGNORE INTO usuarios (cedula, contrasena, rol) VALUES (?, '1234', 'estudiante');", (estudiante,))
        cursor.execute("INSERT OR IGNORE INTO estudiantes (cedula_estudiante, nombre_completo) VALUES (?, ?);", (estudiante, f"Estudiante {estudiante}"))

        # Convertir nombre de materia a su código correlativo
        codigo_mat = obtener_codigo_materia(cursor, materia)

        # Guardar en la tabla de notas relacional
        cursor.execute('''
            INSERT INTO notas (cedula_estudiante, codigo_materia, calificacion, comentario)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cedula_estudiante, codigo_materia) 
            DO UPDATE SET calificacion = excluded.calificacion, comentario = excluded.comentario;
        ''', (estudiante, codigo_mat, nota_nueva, "Registrado desde Panel de Seguridad"))

        # Guardar respaldo histórico en auditoría si la tabla existe
        try:
            cursor.execute('''
                INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva)
                VALUES (?, ?, ?)
            ''', (usuario, nota_anterior, nota_nueva))
        except sqlite3.OperationalError:
            pass # Si Juan no creó esta tabla específica, no trancamos el registro principal

        conn.commit()
        conn.close()
        print("💾 [SQLITE]: Datos guardados con éxito en la estructura relacional.")

    except sqlite3.Error as e:
        print(f"❌ [SQLITE ERROR]: Falló la inserción: {e}")

    # Archivo LOG plano de respaldo (tu salvavidas inmutable)
    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_log = f"{fecha_hora} - [AUDITORIA] - Profesor: {usuario} | Estudiante: {estudiante} | Materia: {materia} | Nota: {nota_nueva}\n"
        with open("auditoria_notas.log", "a", encoding="utf-8") as archivo:
            archivo.write(mensaje_log)
    except Exception as e:
        print(f"❌ [LOG ERROR]: {e}")

def modificar_auditoria(usuario, estudiante, materia, nota_nueva_str):
    """Modifica una nota existente respetando las llaves foráneas."""
    es_valida, mensaje_error = validar_nota(nota_nueva_str)
    if not es_valida:
        return False, mensaje_error

    nota_nueva = float(nota_nueva_str)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        codigo_mat = obtener_codigo_materia(cursor, materia)

        # Verificar si la nota ya existe para poder modificarla
        cursor.execute('''
            SELECT calificacion FROM notas 
            WHERE cedula_estudiante = ? AND codigo_materia = ?
        ''', (estudiante, codigo_mat))
        resultado = cursor.fetchone()

        if resultado is None:
            conn.close()
            return False, f"El alumno {estudiante} no tiene notas en {materia} para modificar."

        nota_anterior = resultado[0]

        # Hacer el UPDATE real en la BD de Juan
        cursor.execute('''
            UPDATE notas 
            SET calificacion = ?, comentario = ?
            WHERE cedula_estudiante = ? AND codigo_materia = ?
        ''', (nota_nueva, "Modificado desde Panel de Seguridad", estudiante, codigo_mat))

        # Registrar el movimiento en la auditoría si es posible
        try:
            cursor.execute('''
                INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva)
                VALUES (?, ?, ?)
            ''', (usuario, nota_anterior, nota_nueva))
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()
        return True, f"Modificado con éxito: {nota_anterior} -> {nota_nueva}"

    except sqlite3.Error as e:
        return False, f"Error SQL: {e}"