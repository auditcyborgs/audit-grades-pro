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
    
    # Crear nueva materia si no existe
    codigo_nuevo = nombre_materia[:3].upper() + "-" + str(abs(hash(nombre_materia)) % 100).zfill(2)
    try:
        cursor.execute('''
            INSERT INTO materias (codigo_materia, nombre_materia, descripcion, creditos)
            VALUES (?, ?, ?, ?)
        ''', (codigo_nuevo, nombre_materia, f"Materia: {nombre_materia}", 3))
        return codigo_nuevo
    except sqlite3.Error:
        return "GEN-01"

def obtener_todos_los_registros():
    """Trae SOLO los registros de la base de datos (sin duplicar con memoria)"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                n.fecha_registro as fecha,
                COALESCE(a.usuario, 'Sistema') as usuario,
                e.nombre || ' ' || e.apellido as estudiante_nombre,
                e.cedula,
                m.nombre_materia,
                n.nota
            FROM notas n
            LEFT JOIN estudiante e ON n.cedula = e.cedula
            LEFT JOIN materias m ON n.codigo_materia = m.codigo_materia
            LEFT JOIN auditoria_notas a ON a.nota_nueva = n.nota
            ORDER BY n.fecha_registro DESC
        ''')
        registros = cursor.fetchall()
        conn.close()
        
        if not registros:
            return []
        
        registros_formateados = []
        for r in registros:
            fecha = r[0] if r[0] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            usuario = r[1] if r[1] else "Sistema"
            estudiante_completo = f"{r[2]} [{r[3]}]" if r[2] else f"Estudiante {r[3]}"
            materia = r[4] if r[4] else "General"
            nota = str(int(r[5]) if r[5] and float(r[5]).is_integer() else r[5])
            registros_formateados.append((fecha, usuario, estudiante_completo, materia, nota))
        
        return registros_formateados
        
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error de tabla: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Error inesperado al leer la BD: {e}")
        return []

def registrar_auditoria(usuario, estudiante, materia, nota_nueva_str, nota_anterior=0):
    """Inserta la nota SOLO en la base de datos (sin memoria)"""
    try:
        nota_nueva = float(nota_nueva_str)
    except ValueError:
        print("❌ Error: La calificación no es un número válido.")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Extraer cédula del formato "Nombre [12345678]"
        cedula_num = estudiante
        nombre_estudiante = estudiante
        apellido_estudiante = ""
        if "[" in estudiante and "]" in estudiante:
            try:
                partes = estudiante.split(" [")
                nombre_completo = partes[0].strip()
                cedula_num = partes[1].replace("]", "")
                
                if " " in nombre_completo:
                    partes_nombre = nombre_completo.split(" ", 1)
                    nombre_estudiante = partes_nombre[0]
                    apellido_estudiante = partes_nombre[1] if len(partes_nombre) > 1 else ""
                else:
                    nombre_estudiante = nombre_completo
            except:
                pass
        
        # Verificar si el estudiante existe
        cursor.execute("SELECT cedula FROM estudiante WHERE cedula = ?", (cedula_num,))
        estudiante_existente = cursor.fetchone()
        
        if not estudiante_existente:
            # Insertar nuevo estudiante con correo único
            correo_unico = f"{cedula_num}@estudiante.local"
            cursor.execute('''
                INSERT INTO estudiante (cedula, nombre, apellido, edad, correo, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cedula_num, nombre_estudiante, apellido_estudiante, 0, correo_unico, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Obtener código de materia
        codigo_mat = obtener_codigo_materia(cursor, materia)

        # Guardar en la tabla notas
        cursor.execute('''
            INSERT INTO notas (cedula, estudiante, codigo_materia, nota, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        ''', (cedula_num, nombre_estudiante, codigo_mat, nota_nueva, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Guardar en auditoría
        cursor.execute('''
            INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva, fecha_cambio)
            VALUES (?, ?, ?, ?)
        ''', (usuario, nota_anterior, nota_nueva, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        print(f"💾 Nota {nota_nueva} guardada para {nombre_estudiante} en {materia}")
        
        # Log plano de respaldo
        try:
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("auditoria_notas.log", "a", encoding="utf-8") as archivo:
                archivo.write(f"{fecha_hora} - [REGISTRO] - {usuario} | {nombre_estudiante} | {cedula_num} | {materia} | {nota_nueva}\n")
        except:
            pass
        
        return True

    except sqlite3.Error as e:
        print(f"❌ Error SQL: {e}")
        return False

def modificar_auditoria(usuario, estudiante, materia, nota_nueva_str):
    """Modifica una nota existente"""
    es_valida, mensaje_error = validar_nota(nota_nueva_str)
    if not es_valida:
        return False, mensaje_error

    nota_nueva = float(nota_nueva_str)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cedula_num = estudiante
        nombre_estudiante = estudiante
        if "[" in estudiante and "]" in estudiante:
            try:
                nombre_estudiante = estudiante.split(" [")[0]
                cedula_num = estudiante.split("[")[1].replace("]", "")
            except:
                pass

        codigo_mat = obtener_codigo_materia(cursor, materia)

        # Obtener nota anterior
        cursor.execute('''
            SELECT nota FROM notas 
            WHERE cedula = ? AND codigo_materia = ?
            ORDER BY fecha_registro DESC LIMIT 1
        ''', (cedula_num, codigo_mat))
        resultado = cursor.fetchone()

        if resultado is None:
            conn.close()
            return False, f"No hay nota de {nombre_estudiante} en {materia}"

        nota_anterior = resultado[0]

        # Insertar nueva nota (mantiene historial)
        cursor.execute('''
            INSERT INTO notas (cedula, estudiante, codigo_materia, nota, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        ''', (cedula_num, nombre_estudiante, codigo_mat, nota_nueva, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Registrar en auditoría
        cursor.execute('''
            INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva, fecha_cambio)
            VALUES (?, ?, ?, ?)
        ''', (usuario, nota_anterior, nota_nueva, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        
        try:
            with open("auditoria_notas.log", "a", encoding="utf-8") as archivo:
                archivo.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - [MODIFICACIÓN] - {usuario} | {nombre_estudiante} | {nota_anterior} -> {nota_nueva}\n")
        except:
            pass
        
        return True, f"Modificado: {nota_anterior} -> {nota_nueva}"

    except sqlite3.Error as e:
        return False, f"Error SQL: {e}"

def eliminar_auditoria(usuario, estudiante, materia):
    """Elimina las notas de un estudiante en una materia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cedula_num = estudiante
        nombre_estudiante = estudiante
        if "[" in estudiante and "]" in estudiante:
            try:
                nombre_estudiante = estudiante.split(" [")[0]
                cedula_num = estudiante.split("[")[1].replace("]", "")
            except:
                pass

        codigo_mat = obtener_codigo_materia(cursor, materia)

        # Obtener última nota
        cursor.execute('''
            SELECT nota FROM notas 
            WHERE cedula = ? AND codigo_materia = ?
            ORDER BY fecha_registro DESC LIMIT 1
        ''', (cedula_num, codigo_mat))
        ultima_nota = cursor.fetchone()
        
        if ultima_nota:
            cursor.execute('''
                INSERT INTO auditoria_notas (usuario, nota_anterior, nota_nueva, fecha_cambio)
                VALUES (?, ?, ?, ?)
            ''', (usuario, ultima_nota[0], -1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Eliminar notas
        cursor.execute('DELETE FROM notas WHERE cedula = ? AND codigo_materia = ?', (cedula_num, codigo_mat))
        
        conn.commit()
        conn.close()
        
        try:
            with open("auditoria_notas.log", "a", encoding="utf-8") as archivo:
                archivo.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - [ELIMINACIÓN] - {usuario} | {nombre_estudiante} | {materia}\n")
        except:
            pass
        
        return True, "Eliminado con éxito"
    except sqlite3.Error as e:
        return False, f"Error: {e}"