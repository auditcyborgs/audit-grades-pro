import sqlite3
import os
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
CARPETA_BD = r"C:\Users\VICMARYCOVA\Documents\GitHub\audit-grades-pro\bd"
DB_NAME = os.path.join(CARPETA_BD, "sistema_de_notas.db")

# ==================== FUNCIÓN PARA CREAR TABLAS SI NO EXISTEN ====================
def crear_tablas_si_no_existen():
    """Crea todas las tablas necesarias si no existen en la base de datos"""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Tabla de usuarios (verificar si existe)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE usuarios (
                cedula TEXT PRIMARY KEY,
                contrasena TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        """)
        print("✅ Tabla 'usuarios' creada")
    
    # Tabla de estudiantes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estudiantes'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE estudiantes (
                cedula_estudiante TEXT PRIMARY KEY,
                nombre_completo TEXT NOT NULL,
                carrera TEXT,
                semestre INTEGER
            )
        """)
        print("✅ Tabla 'estudiantes' creada")
    
    # Tabla de profesores (¡LA QUE FALTA!)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profesores'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE profesores (
                cedula_profesor TEXT PRIMARY KEY,
                nombre_completo TEXT NOT NULL,
                departamento TEXT,
                especialidad TEXT,
                email TEXT,
                telefono TEXT
            )
        """)
        print("✅ Tabla 'profesores' creada")
    
    # Tabla de personal (para control de estudio y director)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personal'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE personal (
                cedula_personal TEXT PRIMARY KEY,
                nombre_completo TEXT NOT NULL,
                cargo TEXT NOT NULL,
                area TEXT
            )
        """)
        print("✅ Tabla 'personal' creada")
    
    # Tabla de materias
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materias'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE materias (
                codigo_materia TEXT PRIMARY KEY,
                nombre_materia TEXT NOT NULL,
                creditos INTEGER DEFAULT 3,
                semestre INTEGER
            )
        """)
        print("✅ Tabla 'materias' creada")
        
        # Insertar materias de ejemplo
        materias_ejemplo = [
            ("MAT-101", "Matemáticas I", 4, 1),
            ("MAT-102", "Matemáticas II", 4, 2),
            ("FIS-101", "Física I", 4, 1),
            ("PROG-101", "Programación I", 4, 1),
            ("BD-101", "Base de Datos", 3, 3),
        ]
        for m in materias_ejemplo:
            try:
                cursor.execute("INSERT INTO materias (codigo_materia, nombre_materia, creditos, semestre) VALUES (?, ?, ?, ?)", m)
            except:
                pass
        print("✅ Materias de ejemplo creadas")
    
    # Tabla de notas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notas'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE notas (
                id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula_estudiante TEXT,
                codigo_materia TEXT,
                calificacion REAL,
                comentario TEXT,
                profesor TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'notas' creada")
    
    conexion.commit()
    conexion.close()
    print("\n✅ Todas las tablas verificadas/creadas correctamente")

# ==================== FUNCIÓN PARA DETECTAR ESTRUCTURA ====================
def obtener_estructura_bd():
    """Detecta automáticamente los nombres de las columnas en la base de datos"""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Obtener información de la tabla usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas = cursor.fetchall()
    
    estructura = {
        'columna_id': None,
        'columna_pass': None,
        'columna_rol': None
    }
    
    for col in columnas:
        nombre_col = col[1]
        
        # Detectar columna de identificación
        if nombre_col in ['cedula', 'usuario', 'id', 'username', 'user']:
            estructura['columna_id'] = nombre_col
        # Detectar columna de contraseña
        if nombre_col in ['contrasena', 'contraseña', 'password', 'pass']:
            estructura['columna_pass'] = nombre_col
        # Detectar columna de rol
        if nombre_col in ['rol', 'role', 'tipo']:
            estructura['columna_rol'] = nombre_col
    
    # Si no se detectaron, usar las primeras columnas
    if not estructura['columna_id'] and len(columnas) > 0:
        estructura['columna_id'] = columnas[0][1]
    if not estructura['columna_pass'] and len(columnas) > 1:
        estructura['columna_pass'] = columnas[1][1]
    if not estructura['columna_rol'] and len(columnas) > 2:
        estructura['columna_rol'] = columnas[2][1]
    
    conexion.close()
    return estructura

# Crear tablas si no existen
crear_tablas_si_no_existen()

# Obtener estructura
ESTRUCTURA = obtener_estructura_bd()

# ==================== PERMISOS POR ROL ====================
PERMISOS = {
    'estudiante': {'ver_notas': True},
    'profesor': {'ver_notas': True, 'crear_notas': True, 'modificar_notas': True},
    'control de estudio': {'ver_notas': True, 'modificar_notas': True, 'eliminar_notas': True},
    'director': {'ver_notas': True, 'modificar_notas': True, 'eliminar_notas': True, 'reportes': True},
    'root': {'todos_los_permisos': True}
}

def verificar_permiso(usuario, permiso):
    if usuario['rol'] == 'root':
        return True
    return PERMISOS.get(usuario['rol'], {}).get(permiso, False)

# ==================== FUNCIONES DE REGISTRO ====================
def registrar_estudiante():
    print("\n" + "="*50)
    print("   🎓 REGISTRO DE ESTUDIANTE")
    print("="*50)
    
    cedula = input("\n📝 Cédula: ").strip()
    contrasena = input("🔒 Contraseña: ").strip()
    nombre = input("👤 Nombre completo: ").strip()
    carrera = input("📚 Carrera: ").strip()
    semestre = input("📖 Semestre: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        sql = f"INSERT INTO usuarios ({ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_pass']}, {ESTRUCTURA['columna_rol']}) VALUES (?, ?, 'estudiante')"
        cursor.execute(sql, (cedula, contrasena))
        
        cursor.execute("""
            INSERT OR REPLACE INTO estudiantes (cedula_estudiante, nombre_completo, carrera, semestre) 
            VALUES (?, ?, ?, ?)
        """, (cedula, nombre, carrera, semestre))
        
        conexion.commit()
        print(f"\n✅ ¡Estudiante registrado exitosamente!")
        print(f"   Usuario: {cedula}")
        print(f"   Contraseña: {contrasena}")
        
    except sqlite3.IntegrityError:
        print("\n❌ Error: Esta cédula ya existe")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conexion.close()

def registrar_profesor():
    print("\n" + "="*50)
    print("   👨‍🏫 REGISTRO DE PROFESOR")
    print("="*50)
    
    cedula = input("\n📝 Cédula: ").strip()
    contrasena = input("🔒 Contraseña: ").strip()
    nombre = input("👤 Nombre completo: ").strip()
    departamento = input("🏛️ Departamento: ").strip()
    especialidad = input("🎓 Especialidad (opcional): ").strip() or "General"
    email = input("📧 Email (opcional): ").strip() or "no@email.com"
    telefono = input("📱 Teléfono (opcional): ").strip() or "000-0000000"
    
    print("\n" + "="*50)
    print("   CONFIRMAR REGISTRO")
    print("="*50)
    print(f"👤 Usuario: {cedula}")
    print(f"👨‍🏫 Nombre: {nombre}")
    print(f"🏛️ Departamento: {departamento}")
    
    confirmar = input("\n¿Confirmar registro? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Registro cancelado")
        return
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        # Verificar si el usuario ya existe
        sql_check = f"SELECT {ESTRUCTURA['columna_id']} FROM usuarios WHERE {ESTRUCTURA['columna_id']} = ?"
        cursor.execute(sql_check, (cedula,))
        if cursor.fetchone():
            print("\n❌ Error: Esta cédula ya está registrada")
            conexion.close()
            return
        
        # Insertar en tabla usuarios
        sql = f"INSERT INTO usuarios ({ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_pass']}, {ESTRUCTURA['columna_rol']}) VALUES (?, ?, 'profesor')"
        cursor.execute(sql, (cedula, contrasena))
        
        # Insertar en tabla profesores (ahora existe porque la creamos)
        cursor.execute("""
            INSERT INTO profesores (cedula_profesor, nombre_completo, departamento, especialidad, email, telefono) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cedula, nombre, departamento, especialidad, email, telefono))
        
        conexion.commit()
        
        print("\n" + "="*50)
        print("   ✅ ¡PROFESOR REGISTRADO EXITOSAMENTE!")
        print("="*50)
        print(f"👤 Usuario: {cedula}")
        print(f"🔑 Contraseña: {contrasena}")
        
    except sqlite3.IntegrityError as e:
        print(f"\n❌ Error de integridad: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conexion.close()

def registrar_control_estudio():
    print("\n" + "="*50)
    print("   📋 REGISTRO DE CONTROL DE ESTUDIO")
    print("="*50)
    
    cedula = input("\n📝 Cédula: ").strip()
    contrasena = input("🔒 Contraseña: ").strip()
    nombre = input("👤 Nombre completo: ").strip()
    cargo = input("📋 Cargo: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        sql = f"INSERT INTO usuarios ({ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_pass']}, {ESTRUCTURA['columna_rol']}) VALUES (?, ?, 'control de estudio')"
        cursor.execute(sql, (cedula, contrasena))
        
        cursor.execute("""
            INSERT OR REPLACE INTO personal (cedula_personal, nombre_completo, cargo, area) 
            VALUES (?, ?, ?, 'Control de Estudio')
        """, (cedula, nombre, cargo))
        
        conexion.commit()
        print(f"\n✅ Control de Estudio registrado exitosamente!")
        print(f"   Usuario: {cedula}")
        print(f"   Contraseña: {contrasena}")
        
    except sqlite3.IntegrityError:
        print("\n❌ Error: Esta cédula ya existe")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conexion.close()

def registrar_director():
    print("\n" + "="*50)
    print("   👨‍💼 REGISTRO DE DIRECTOR")
    print("="*50)
    
    cedula = input("\n📝 Cédula: ").strip()
    contrasena = input("🔒 Contraseña: ").strip()
    nombre = input("👤 Nombre completo: ").strip()
    cargo = input("👔 Cargo: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        sql = f"INSERT INTO usuarios ({ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_pass']}, {ESTRUCTURA['columna_rol']}) VALUES (?, ?, 'director')"
        cursor.execute(sql, (cedula, contrasena))
        
        cursor.execute("""
            INSERT OR REPLACE INTO personal (cedula_personal, nombre_completo, cargo, area) 
            VALUES (?, ?, ?, 'Dirección')
        """, (cedula, nombre, cargo))
        
        conexion.commit()
        print(f"\n✅ Director registrado exitosamente!")
        print(f"   Usuario: {cedula}")
        print(f"   Contraseña: {contrasena}")
        
    except sqlite3.IntegrityError:
        print("\n❌ Error: Esta cédula ya existe")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conexion.close()

# ==================== FUNCIONES DE LOGIN ====================
def iniciar_sesion():
    print("\n" + "="*50)
    print("   🔑 INICIO DE SESIÓN")
    print("="*50)
    
    cedula = input("\n📝 Usuario/Cédula: ").strip()
    contrasena = input("🔒 Contraseña: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        sql = f"SELECT {ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_rol']} FROM usuarios WHERE {ESTRUCTURA['columna_id']} = ? AND {ESTRUCTURA['columna_pass']} = ?"
        cursor.execute(sql, (cedula, contrasena))
        usuario = cursor.fetchone()
        
        if usuario:
            nombre = usuario[0]
            rol = usuario[1]
            
            # Buscar nombre real según el rol
            if rol == "estudiante":
                cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?", (cedula,))
                res = cursor.fetchone()
                if res: nombre = res[0]
            elif rol == "profesor":
                cursor.execute("SELECT nombre_completo FROM profesores WHERE cedula_profesor = ?", (cedula,))
                res = cursor.fetchone()
                if res: nombre = res[0]
            elif rol == "control de estudio":
                cursor.execute("SELECT nombre_completo FROM personal WHERE cedula_personal = ?", (cedula,))
                res = cursor.fetchone()
                if res: nombre = res[0]
            elif rol == "director":
                cursor.execute("SELECT nombre_completo FROM personal WHERE cedula_personal = ?", (cedula,))
                res = cursor.fetchone()
                if res: nombre = res[0]
            
            conexion.close()
            return {"cedula": usuario[0], "rol": rol, "nombre": nombre}
        
        conexion.close()
        print("\n❌ Credenciales incorrectas")
        return None
        
    except Exception as e:
        print(f"\n❌ Error al iniciar sesión: {e}")
        conexion.close()
        return None

# ==================== FUNCIONES DE MATERIAS ====================
def listar_materias():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute("SELECT codigo_materia, nombre_materia, creditos FROM materias")
    materias = cursor.fetchall()
    conexion.close()
    
    print("\n📚 MATERIAS DISPONIBLES:")
    for idx, mat in enumerate(materias, 1):
        print(f"   {idx}. {mat[0]} - {mat[1]} ({mat[2]} créditos)")
    
    return materias

# ==================== PANELES POR ROL ====================
def panel_estudiante(usuario):
    while True:
        print(f"\n{'='*50}")
        print(f"🎓 PANEL ESTUDIANTE: {usuario['nombre']}")
        print(f"{'='*50}")
        print("1. Ver mis notas")
        print("2. Cerrar Sesión")
        
        opcion = input("\n➡️ Opción: ").strip()
        
        if opcion == "1":
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            
            try:
                cursor.execute("""
                    SELECT m.nombre_materia, n.calificacion, n.comentario, n.fecha
                    FROM notas n
                    JOIN materias m ON n.codigo_materia = m.codigo_materia
                    WHERE n.cedula_estudiante = ?
                """, (usuario['cedula'],))
                
                notas = cursor.fetchall()
                
                print("\n📚 MIS CALIFICACIONES")
                if not notas:
                    print("   No tienes notas registradas aún")
                else:
                    for n in notas:
                        print(f"\n   📖 {n[0]}")
                        print(f"      Nota: {n[1]}")
                        if n[2]:
                            print(f"      Comentario: {n[2]}")
                        print(f"      Fecha: {n[3]}")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                conexion.close()
            input("\nPresione Enter...")
        elif opcion == "2":
            break

def panel_profesor(usuario):
    while True:
        print(f"\n{'='*50}")
        print(f"👨‍🏫 PANEL PROFESOR: {usuario['nombre']}")
        print(f"{'='*50}")
        print("1. Cargar nota")
        print("2. Ver materias")
        print("3. Cerrar Sesión")
        
        opcion = input("\n➡️ Opción: ").strip()
        
        if opcion == "1":
            materias = listar_materias()
            if materias:
                try:
                    idx = int(input("\nSeleccione materia (número): ")) - 1
                    if 0 <= idx < len(materias):
                        materia = materias[idx]
                        cedula_est = input("📝 Cédula del estudiante: ").strip()
                        
                        conexion = sqlite3.connect(DB_NAME)
                        cursor = conexion.cursor()
                        
                        cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?", (cedula_est,))
                        estudiante = cursor.fetchone()
                        
                        if not estudiante:
                            print("❌ Estudiante no encontrado")
                        else:
                            nota = float(input(f"📊 Calificación (0-20): "))
                            comentario = input("💬 Comentario: ").strip()
                            
                            cursor.execute("""
                                INSERT INTO notas (cedula_estudiante, codigo_materia, calificacion, comentario, profesor)
                                VALUES (?, ?, ?, ?, ?)
                            """, (cedula_est, materia[0], nota, comentario, usuario['cedula']))
                            
                            conexion.commit()
                            print(f"\n✅ Nota guardada para {estudiante[0]}")
                        conexion.close()
                except ValueError:
                    print("❌ Opción inválida")
            input("\nPresione Enter...")
        elif opcion == "2":
            listar_materias()
            input("\nPresione Enter...")
        elif opcion == "3":
            break

def panel_control_estudio(usuario):
    print(f"\n📋 PANEL CONTROL DE ESTUDIO: {usuario['nombre']}")
    print("Funcionalidad en desarrollo...")
    input("\nPresione Enter...")

def panel_director(usuario):
    print(f"\n👨‍💼 PANEL DIRECTOR: {usuario['nombre']}")
    print("Funcionalidad en desarrollo...")
    input("\nPresione Enter...")

def panel_root(usuario):
    while True:
        print(f"\n{'='*50}")
        print(f"👑 PANEL ROOT: {usuario['nombre']}")
        print(f"{'='*50}")
        print("1. Ver todos los usuarios")
        print("2. Ver todas las notas")
        print("3. Cerrar Sesión")
        
        opcion = input("\n➡️ Opción: ").strip()
        
        if opcion == "1":
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            
            sql = f"SELECT {ESTRUCTURA['columna_id']}, {ESTRUCTURA['columna_rol']} FROM usuarios"
            cursor.execute(sql)
            usuarios = cursor.fetchall()
            conexion.close()
            
            print("\n👥 USUARIOS DEL SISTEMA")
            for u in usuarios:
                print(f"   {u[0]} - '{u[1]}'")
            input("\nPresione Enter...")
        elif opcion == "2":
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT e.nombre_completo, m.nombre_materia, n.calificacion, n.comentario
                FROM notas n
                JOIN estudiantes e ON n.cedula_estudiante = e.cedula_estudiante
                JOIN materias m ON n.codigo_materia = m.codigo_materia
            """)
            notas = cursor.fetchall()
            conexion.close()
            
            print("\n📊 TODAS LAS NOTAS")
            for n in notas:
                print(f"   {n[0]} - {n[1]}: {n[2]}")
                if n[3]:
                    print(f"      Comentario: {n[3]}")
            input("\nPresione Enter...")
        elif opcion == "3":
            break

# ==================== MENÚ PRINCIPAL ====================
def menu_principal():
    print("\n" + "="*50)
    print("   🎓 AUDIT GRADES PRO")
    print("   Sistema de Gestión de Notas")
    print("="*50)
    
    while True:
        print("\n1. 📝 Registrarse")
        print("2. 🔑 Iniciar Sesión")
        print("3. 🚪 Salir")
        
        opcion = input("\n➡️ Opción: ").strip()
        
        if opcion == "1":
            print("\n¿Tipo de usuario?")
            print("1. Estudiante")
            print("2. Profesor")
            print("3. Control de Estudio")
            print("4. Director")
            
            tipo = input("Opción: ").strip()
            
            if tipo == "1":
                registrar_estudiante()
            elif tipo == "2":
                registrar_profesor()
            elif tipo == "3":
                registrar_control_estudio()
            elif tipo == "4":
                registrar_director()
            else:
                print("❌ Opción inválida")
                
        elif opcion == "2":
            sesion = iniciar_sesion()
            
            if sesion:
                print(f"\n✅ ¡Bienvenido {sesion['nombre']}!")
                print(f"   Rol: '{sesion['rol']}'")
                
                if sesion['rol'] == 'estudiante':
                    panel_estudiante(sesion)
                elif sesion['rol'] == 'profesor':
                    panel_profesor(sesion)
                elif sesion['rol'] == 'control de estudio':
                    panel_control_estudio(sesion)
                elif sesion['rol'] == 'director':
                    panel_director(sesion)
                elif sesion['rol'] == 'root':
                    panel_root(sesion)
                else:
                    print(f"❌ Rol '{sesion['rol']}' no reconocido")
                    input("\nPresione Enter...")
                    
        elif opcion == "3":
            print("\n👋 ¡Hasta luego!")
            break

# ==================== EJECUTAR ====================
if __name__ == "__main__":
    menu_principal()
    PRUEBA