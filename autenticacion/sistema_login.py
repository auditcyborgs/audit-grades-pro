import sqlite3
import os

# CONFIGURACIÓN DE TU RUTA Y BASE DE DATOS REAL
CARPETA_BD = r"C:\Sistema_de_notas\audit-grades-pro\bd"
DB_NAME = os.path.join(CARPETA_BD, "sistema_de_notas.db")

def inicializar_base_de_datos():
    """Crea la estructura de tablas relacionales e inyecta los Roots."""
    if not os.path.exists(CARPETA_BD):
        os.makedirs(CARPETA_BD)

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla de Usuarios (Credenciales)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        cedula TEXT PRIMARY KEY,
        contrasena TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('root', 'profesor', 'estudiante', 'administrador'))
    );
    """)
    
    # 2. Tabla de Estudiantes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estudiantes (
        cedula_estudiante TEXT PRIMARY KEY,
        nombre_completo TEXT NOT NULL,
        FOREIGN KEY(cedula_estudiante) REFERENCES usuarios(cedula) ON DELETE CASCADE
    );
    """)
    
    # 3. Tabla de Administradores (Control de Estudio)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administradores (
        cedula_admin TEXT PRIMARY KEY,
        nombre_completo TEXT NOT NULL,
        cargo TEXT,
        FOREIGN KEY(cedula_admin) REFERENCES usuarios(cedula) ON DELETE CASCADE
    );
    """)
    
    # 4. NUEVA TABLA: Materias 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias (
        codigo_materia TEXT PRIMARY KEY,
        nombre_materia TEXT NOT NULL UNIQUE
    );
    """)
    
    # 5. TABLA ACTUALIZADA: Notas Relacionales 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula_estudiante TEXT,
        codigo_materia TEXT,
        calificacion REAL NOT NULL DEFAULT 0.0 CHECK(calificacion >= 0.0 AND calificacion <= 20.0),
        comentario TEXT,
        FOREIGN KEY(cedula_estudiante) REFERENCES estudiantes(cedula_estudiante) ON DELETE CASCADE,
        FOREIGN KEY(codigo_materia) REFERENCES materias(codigo_materia) ON DELETE CASCADE,
        UNIQUE(cedula_estudiante, codigo_materia) -- Evita duplicar la misma materia para un alumno
    );
    """)
    
    conexion.commit()
    
    # Inyección de Roots Iniciales (Todo en minúsculas)
    roots = ["daniel", "barbara", "juan", "sebastian", "wilmary", "diana"]
    for r in roots:
        try:
            cursor.execute("INSERT OR IGNORE INTO usuarios (cedula, contrasena, rol) VALUES (?, '1234', 'root');", (r,))
        except sqlite3.Error:
            pass

    conexion.commit()
    conexion.close()
    print("✔️ Base de datos sincronizada. Relaciones y Roles Root cargados correctamente.")

# =====================================================================
# SISTEMA DE AUTENTICACIÓN
# =====================================================================

def registrar_usuario_publico():
    print("\n--- REGISTRO PÚBLICO (SOLO ALUMNOS Y PROFES) ---")
    cedula = input("Cédula / Usuario: ").strip()
    contrasena = input("Contraseña: ").strip()
    print("Seleccione su Rol:\n1. Estudiante\n2. Profesor")
    opc = input("Opción: ").strip()
    
    rol = "estudiante" if opc == "1" else "profesor" if opc == "2" else None
    if not rol:
        print("❌ Opción inválida.")
        return

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (cedula, contrasena, rol) VALUES (?, ?, ?);", (cedula, contrasena, rol))
        if rol == "estudiante":
            nombre = input("Nombre Completo del Alumno: ").strip()
            cursor.execute("INSERT INTO estudiantes (cedula_estudiante, nombre_completo) VALUES (?, ?);", (cedula, nombre))
        conexion.commit()
        print(f"✔️ Usuario registrado exitosamente como {rol.upper()}.")
    except sqlite3.IntegrityError:
        print("❌ Error: Ese usuario o cédula ya existe.")
    finally:
        conexion.close()

def iniciar_sesion():
    print("\n--- INICIO DE SESIÓN ---")
    cedula = input("Usuario / Cédula: ").strip()
    contrasena = input("Contraseña: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT cedula, rol FROM usuarios WHERE cedula = ? AND contrasena = ?;", (cedula, contrasena))
    usuario = cursor.fetchone()
    
    if usuario:
        nombre = usuario[0]
        if usuario[1] == "estudiante":
            cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?;", (cedula,))
            res = cursor.fetchone()
            if res: nombre = res[0]
        elif usuario[1] == "administrador":
            cursor.execute("SELECT nombre_completo FROM administradores WHERE cedula_admin = ?;", (cedula,))
            res = cursor.fetchone()
            if res: nombre = res[0]
            
        conexion.close()
        return {"cedula": usuario[0], "rol": usuario[1], "nombre": nombre}
    
    conexion.close()
    print("❌ Credenciales incorrectas.")
    return None

# =====================================================================
# VISTAS DE USUARIOS
# =====================================================================

def vista_estudiante(usuario):
    """El estudiante SOLO puede ver sus materias, notas y comentarios."""
    while True:
        print(f"\n--- PANEL DE ESTUDIANTE: {usuario['nombre']} ---")
        print("1. Ver mis Notas (Record Académico)")
        print("2. Cerrar Sesión")
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            # Unimos notas con materias para mostrar la información limpia
            cursor.execute("""
                SELECT m.codigo_materia, m.nombre_materia, n.calificacion, n.comentario
                FROM notas n
                INNER JOIN materias m ON n.codigo_materia = m.codigo_materia
                WHERE n.cedula_estudiante = ?;
            """, (usuario['cedula'],))
            notas = cursor.fetchall()
            conexion.close()
            
            print("\nCódigo    | Materia              | Nota  | Comentario del Profesor")
            print("-" * 75)
            if not notas:
                print("No tienes materias inscritas o notas cargadas aún.")
            for n in notas:
                print(f"{n[0]:<9} | {n[1]:<20} | {n[2]:<5} | {n[3] if n[3] else 'Sin observaciones'}")
        elif opcion == "2":
            break

def vista_profesor(usuario):
    """El profesor puede agregar materias, alumnos e inscribirlos."""
    while True:
        print(f"\n--- PANEL DE PROFESOR ---")
        print("1. Crear Nueva Materia")
        print("2. Inscribir Estudiante en Materia")
        print("3. Cargar / Modificar Nota de un Estudiante")
        print("4. Ver Listado de Notas General")
        print("5. Cerrar Sesión")
        opcion = input("Seleccione una opción: ").strip()
        
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        if opcion == "1":
            cod = input("Código de la materia (ej: INF-01): ").strip().upper()
            nom = input("Nombre de la materia (ej: Matematica I): ").strip()
            try:
                cursor.execute("INSERT INTO materias (codigo_materia, nombre_materia) VALUES (?, ?);", (cod, nom))
                conexion.commit()
                print(f"✔️ Materia '{nom}' creada exitosamente.")
            except sqlite3.IntegrityError:
                print("❌ Error: El código o nombre de materia ya existe.")
                
        elif opcion == "2":
            ced = input("Cédula del Estudiante a inscribir: ").strip()
            cod = input("Código de la Materia: ").strip().upper()
            try:
                cursor.execute("INSERT INTO notas (cedula_estudiante, codigo_materia, calificacion) VALUES (?, ?, 0.0);", (ced, cod))
                conexion.commit()
                print(f"✔️ Estudiante {ced} inscrito con éxito en la materia {cod}.")
            except sqlite3.IntegrityError:
                print("❌ Error: Verifique que el alumno y la materia existan, o si ya está inscrito.")
                
        elif opcion == "3":
            ced = input("Cédula del Estudiante: ").strip()
            cod = input("Código de la Materia: ").strip().upper()
            try:
                nota = float(input("Ingrese la Calificación (0-20): "))
                comentario = input("Comentario u Observación: ").strip()
                cursor.execute("""
                    UPDATE notas SET calificacion = ?, comentario = ? 
                    WHERE cedula_estudiante = ? AND codigo_materia = ?;
                """, (nota, comentario, ced, cod))
                conexion.commit()
                if cursor.rowcount > 0:
                    print("✔️ Nota cargada correctamente.")
                else:
                    print("❌ El alumno no está inscrito en esa materia.")
            except ValueError:
                print("❌ Ingrese una nota válida con números enteros o decimales.")
                
        elif opcion == "4":
            cursor.execute("""
                SELECT n.id_nota, e.nombre_completo, m.nombre_materia, n.calificacion 
                FROM notas n
                INNER JOIN estudiantes e ON n.cedula_estudiante = e.cedula_estudiante
                INNER JOIN materias m ON n.codigo_materia = m.codigo_materia;
            """)
            regs = cursor.fetchall()
            print("\nID Nota | Estudiante           | Materia              | Nota")
            print("-" * 65)
            for r in regs:
                print(f"{r[0]:<7} | {r[1]:<20} | {r[2]:<20} | {r[3]}")
                
        elif opcion == "5":
            conexion.close()
            break
        conexion.close()

def vista_control_estudio(usuario):
    while True:
        print(f"\n--- PANEL DE CONTROL DE ESTUDIO ---")
        print("1. Ver todas las materias registradas")
        print("2. Cerrar Sesión")
        opc = input("Opción: ").strip()
        if opc == "1":
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM materias;")
            mats = cursor.fetchall()
            conexion.close()
            print("\nCódigo    | Materia")
            print("-" * 35)
            for m in mats:
                print(f"{m[0]:<9} | {m[1]}")
        elif opc == "2":
            break

def vista_root(usuario):
    """Permisos Absolutos (Dueños del sistema): Registro forzado de cualquier rol."""
    while True:
        print(f"\n--- ⚡ ACCESO TOTAL ROOT: {usuario['nombre'].upper()} ⚡ ---")
        print("1. Registrar cualquier Usuario (Root, Profe, Control de Estudio, Alumno)")
        print("2. Ver listado de todas las credenciales del sistema")
        print("3. Forzar borrado de un usuario")
        print("4. Cerrar Sesión")
        opcion = input("Seleccione una opción: ").strip()
        
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        if opcion == "1":
            cedula = input("Cédula/ID: ").strip()
            contrasena = input("Contraseña: ").strip()
            print("Seleccione Rol:\n1. Root\n2. Profesor\n3. Administrador (Control de Estudio)\n4. Estudiante")
            r_opc = input("Opción: ").strip()
            
            roles = {"1": "root", "2": "profesor", "3": "administrador", "4": "estudiante"}
            rol = roles.get(r_opc)
            
            if not rol:
                print("❌ Rol inválido.")
                continue
                
            try:
                cursor.execute("INSERT INTO usuarios (cedula, contrasena, rol) VALUES (?, ?, ?);", (cedula, contrasena, rol))
                if rol == "estudiante":
                    nom = input("Nombre Completo del Estudiante: ").strip()
                    cursor.execute("INSERT INTO estudiantes (cedula_estudiante, nombre_completo) VALUES (?, ?);", (cedula, nom))
                elif rol == "administrador":
                    nom = input("Nombre Completo del Personal: ").strip()
                    cargo = input("Cargo (ej: Jefe de Control de Estudios): ").strip()
                    cursor.execute("INSERT INTO administradores (cedula_admin, nombre_completo, cargo) VALUES (?, ?, ?);", (cedula, nom, cargo))
                conexion.commit()
                print(f"✔️ {rol.upper()} registrado con éxito por la administración superior.")
            except sqlite3.IntegrityError:
                print("❌ El ID/Cédula ya existe.")
                
        elif opcion == "2":
            cursor.execute("SELECT cedula, rol FROM usuarios;")
            usuarios = cursor.fetchall()
            print("\nUsuario/ID           | Rol")
            print("-" * 35)
            for u in usuarios:
                print(f"{u[0]:<20} | {u[1]}")
                
        elif opcion == "3":
            ced = input("Ingrese la cédula/ID del usuario a eliminar del sistema: ").strip()
            if ced in ["daniel", "barbara", "juan", "sebastian", "wilmary", "diana"]:
                print("❌ Seguridad: No puedes auto-eliminar a los fundadores del sistema.")
                continue
            cursor.execute("DELETE FROM usuarios WHERE cedula = ?;", (ced,))
            conexion.commit()
            if cursor.rowcount > 0:
                print(f"💥 Usuario {ced} eliminado de raíz de la base de datos.")
            else:
                print("❌ El usuario no existe.")
                
        elif opcion == "4":
            conexion.close()
            break
        conexion.close()

# =====================================================================
# MENÚ PRINCIPAL
# =====================================================================

def menu_principal():
    inicializar_base_de_datos()
    while True:
        print(f"\n========== AUDIT GRADES PRO ==========")
        print("1. Registrarse (Público: Estudiantes y Profesores)")
        print("2. Iniciar Sesión")
        print("3. Salir")
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            registrar_usuario_publico()
        elif opcion == "2":
            sesion = iniciar_sesion()
            if sesion:
                rol_visible = "Control de Estudio" if sesion['rol'] == "administrador" else sesion['rol'].upper()
                print(f"\n🔓 ¡Sesión autorizada! Bienvenido: {rol_visible}\n")
                
                if sesion["rol"] == "estudiante":
                    vista_estudiante(sesion)
                elif sesion["rol"] == "profesor":
                    vista_profesor(sesion)
                elif sesion["rol"] == "administrador":
                    vista_control_estudio(sesion)
                elif sesion["rol"] == "root":
                    vista_root(sesion)
        elif opcion == "3":
            print("¡Cerrando el sistema de auditoría escolar!")
            break
        else:
            print("❌ Opción inválida.")

if __name__ == "__main__":
    menu_principal()