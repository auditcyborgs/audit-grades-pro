import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("bd", "sistema_de_notas.db")

def validar_nota(nota_str):
    """Valida que la nota sea un número entero entre 0 y 20."""
    if not nota_str.strip():
        return False, "La nota no puede estar vacías."
    
    if not nota_str.isdigit():
        return False, "La nota debe ser un número entero (sin letras ni decimales)."
    
    nota = int(nota_str)
    if nota < 0 or nota > 20:
        return False, "La nota debe estar en el rango de 0 a 20."
    
    return True, ""


def registrar_auditoria(usuario, estudiante, materia, nota_nueva_str, nota_anterior=0):
    """
    Inserta la nota y los datos de auditoría directamente en el archivo .db de SQLite
    y guarda un respaldo de seguridad en el archivo de texto .log.
    """
    try:
        nota_nueva = float(nota_nueva_str)
    except ValueError:
        print("❌ Error: La calificación no es un número válido.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notas (cedula_estudiante, materia, calificacion, comentario)
            VALUES (?, ?, ?, ?)
        ''', (estudiante, materia, nota_nueva, "Registrado desde Panel de Seguridad"))

        cursor.execute('''
            INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva)
            VALUES (?, ?, ?)
        ''', (usuario, nota_anterior, nota_nueva))

       
        conn.commit()
        conn.close()
        print("💾 [SQLITE]: Datos guardados con éxito en 'notas' y 'auditoria_notas'.")

    except sqlite3.Error as e:
        print(f"❌ [SQLITE ERROR]: Falló la inserción en la base de datos: {e}")

    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_log = f"{fecha_hora} - [AUDITORIA] - Profesor: {usuario} | Estudiante: {estudiante} | Materia: {materia} | Nota: {nota_nueva}\n"
        
        with open("auditoria_notas.log", "a", encoding="utf-8") as archivo:
            archivo.write(mensaje_log)
        print("📝 [LOG]: Respaldo guardado en auditoria_notas.log.")
        
    except Exception as e:
        print(f"❌ [LOG ERROR]: No se pudo escribir en el archivo log: {e}")


def obtener_todos_los_registros():
    """
    Obtiene todos los registros combinando las tablas notas y auditoria_notas.
    Retorna una lista de tuplas con (fecha_cambio, usuario, cedula_estudiante, materia, nota_nueva, hash)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM auditoria_notas")
        count_audit = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM notas")
        count_notas = cursor.fetchone()[0]
        
        print(f"📊 Registros en auditoria_notas: {count_audit}")
        print(f"📊 Registros en notas: {count_notas}")
        
        if count_audit == 0 or count_notas == 0:
            print("⚠️ No hay registros en la base de datos")
            conn.close()
            return []
        
        cursor.execute('''
            SELECT 
                a.fecha_cambio,
                a.usuario,
                n.cedula_estudiante,
                n.materia,
                a.nota_nueva,
                '0x' || substr(hex(randomblob(8)), 1, 16) as hash_firma
            FROM auditoria_notas a
            CROSS JOIN notas n
            WHERE a.rowid = n.rowid
            ORDER BY a.fecha_cambio DESC
        ''')
        
        registros = cursor.fetchall()
        print(f"✅ Se encontraron {len(registros)} registros para mostrar")
        conn.close()
        return registros
        
    except sqlite3.Error as e:
        print(f"❌ [SQLITE ERROR]: No se pudo obtener los registros: {e}")
        return []


def obtener_registros_simple():
    """
    Versión simplificada - obtiene solo registros de auditoría con notas
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                datetime(fecha_cambio) as fecha,
                usuario,
                nota_nueva,
                '0x' || substr(hex(randomblob(8)), 1, 16) as hash_firma
            FROM auditoria_notas
            ORDER BY fecha_cambio DESC
        ''')
        
        registros = cursor.fetchall()
        conn.close()
        return registros
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        return []