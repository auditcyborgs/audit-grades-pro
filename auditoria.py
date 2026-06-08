import os
import sqlite3
from datetime import datetime

# Ruta exacta a la base de datos según tu estructura de carpetas
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