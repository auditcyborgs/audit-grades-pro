import sqlite3
import os

# CONFIGURACIÓN DE TU RUTA Y BASE DE DATOS REAL
CARPETA_BD = r"C:\Sistema_de_notas\audit-grades-pro\bd"
DB_NAME = os.path.join(CARPETA_BD, "sistema_de_notas.db") # Usa tu archivo existente

def inicializar_base_de_datos():
    """Verifica la carpeta y crea las tablas si aún no existen en tu archivo .db"""
    if not os.path.exists(CARPETA_BD):
        os.makedirs(CARPETA_BD)
        print(f"📁 Carpeta creada automáticamente en: {CARPETA_BD}")

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # 1. Tabla principal de Autenticación (Cédula como serial/PRIMARY KEY)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        cedula TEXT PRIMARY KEY,
        contrasena TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('root', 'profesor', 'estudiante'))
    );
    """)
    
    # 2. Tabla de Datos del Estudiante
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estudiantes (
        cedula_estudiante TEXT PRIMARY KEY,
        nombre_completo TEXT NOT NULL,
        FOREIGN KEY(cedula_estudiante) REFERENCES usuarios(cedula) ON DELETE CASCADE
    );
    """)
    
    # 3. Tabla de Notas (Relacionada con estudiantes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula_estudiante TEXT,
        materia TEXT NOT NULL,
        calificacion REAL NOT NULL,
        comentario TEXT,
        FOREIGN KEY(cedula_estudiante) REFERENCES estudiantes(cedula_estudiante) ON DELETE CASCADE
    );
    """)
    
    conexion.commit()
    conexion.close()

# =====================================================================
# LÓGICA DE REGISTRO E INICIO DE SESIÓN
# =====================================================================

def registrar_usuario():
    print("\n--- REGISTRO DE NUEVO USUARIO ---")
    cedula = input("Ingrese la Cédula: ").strip()
    contrasena = input("Ingrese la Contraseña: ").strip()
    print("Seleccione el Rol:")
    print("1. Estudiante\n2. Profesor\n3. Root")
    opcion_rol = input("Opción: ").strip()
    
    roles = {"1": "estudiante", "2": "profesor", "3": "root"}
    rol = roles.get(opcion_rol)
    
    if not rol:
        print("❌ Opción de rol inválida.")
        return

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    try:
        cursor.execute("INSERT INTO usuarios (cedula, contrasena, rol) VALUES (?, ?, ?);", (cedula, contrasena, rol))
        
        if rol == "estudiante":
            nombre = input("Ingrese el Nombre Completo del Estudiante: ").strip()
            cursor.execute("INSERT INTO estudiantes (cedula_estudiante, nombre_completo) VALUES (?, ?);", (cedula, nombre))
            
            # Materias base por defecto para el estudiante recién creado
            cursor.execute("INSERT INTO notas (cedula_estudiante, materia, calificacion) VALUES (?, 'Matemáticas', 0.0);", (cedula,))
            cursor.execute("INSERT INTO notas (cedula_estudiante, materia, calificacion) VALUES (?, 'Programación', 0.0);", (cedula,))
            
        conexion.commit()
        print(f"✔️ Usuario con cédula {cedula} y rol '{rol}' registrado con éxito.")
    except sqlite3.IntegrityError:
        print("❌ Error: Esa cédula ya se encuentra registrada en el sistema.")
    finally:
        conexion.close()

def iniciar_sesion():
    print("\n--- INICIO DE SESIÓN ---")
    cedula = input("Cédula: ").strip()
    contrasena = input("Contraseña: ").strip()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute("SELECT cedula, rol FROM usuarios WHERE cedula = ? AND contrasena = ?;", (cedula, contrasena))
    usuario = cursor.fetchone()
    
    if usuario:
        datos_sesion = {"cedula": usuario[0], "rol": usuario[1], "nombre": "Usuario"}
        
        # Si es estudiante, extraemos su nombre real desde la tabla estudiantes
        if usuario[1] == "estudiante":
            cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?;", (cedula,))
            res_nombre = cursor.fetchone()
            if res_nombre:
                datos_sesion["nombre"] = res_nombre[0]
                
        conexion.close()
        return datos_sesion
    
    conexion.close()
    print("❌ Cédula o contraseña incorrectas.")
    return None

# =====================================================================
# VISTAS Y PERMISOS SEGÚN EL ROL
# =====================================================================

def vista_estudiante(usuario):
    """El estudiante solo ve sus propias notas y puede dejar comentarios."""
    while True:
        print(f"\n--- PANEL DE ESTUDIANTE: {usuario['nombre']} ---")
        print("1. Ver mis notas y comentarios")
        print("2. Escribir/Modificar un comentario en una materia")
        print("3. Cerrar Sesión")
        opcion = input("Seleccione una opción: ").strip()
        
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        
        if opcion == "1":
            cursor.execute("SELECT id_nota, materia, calificacion, comentario FROM notas WHERE cedula_estudiante = ?;", (usuario['cedula'],))
            notas = cursor.fetchall()
            print("\nID Nota | Materia | Nota | Tu Comentario")
            print("-" * 55)
            for n in notas:
                print(f"{n[0]} | {n[1]} | {n[2]} | {n[3] if n[3] else 'Sin comentario'}")
                
        elif opcion == "2":
            id_nota = input("Ingrese el ID de la nota a comentar: ").strip()
            nuevo_comentario = input("Escriba su comentario: ").strip()
            # Asegura que el estudiante solo pueda modificar comentarios de SUS PROPIAS notas
            cursor.execute("UPDATE notas SET comentario = ? WHERE id_nota = ? AND cedula_estudiante = ?;", (nuevo_comentario, id_nota, usuario['cedula']))
            conexion.commit()
            if cursor.rowcount > 0:
                print("✔️ Comentario guardado correctamente.")
            else:
                print("❌ No se pudo guardar (ID inválido o la nota no te pertenece).")
                
        elif opcion == "3":
            conexion.close()
            break
        conexion.close()

def vista_profesor(usuario):
    """El profesor ve los nombres y cédulas de todos, y puede modificar calificaciones."""
    while True:
        print(f"\n--- PANEL DE PROFESOR ---")
        print("1. Ver lista de estudiantes y sus notas")
        print("2. Registrar/Modificar nota de un estudiante")
        print("3. Cerrar Sesión")
        opcion = input("Seleccione una opción: ").strip()
        
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        
        if opcion == "1":
            # Unimos la tabla estudiantes y notas mediante la cédula para cruzar la información
            cursor.execute("""
                SELECT e.cedula_estudiante, e.nombre_completo, n.id_nota, n.materia, n.calificacion, n.comentario
                FROM estudiantes e
                INNER JOIN notas n ON e.cedula_estudiante = n.cedula_estudiante;
            """)
            registros = cursor.fetchall()
            print("\nCédula | Estudiante | ID Nota | Materia | Nota | Comentario del Alumno")
            print("-" * 85)
            for r in registros:
                print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5] if r[5] else ''}")
                
        elif opcion == "2":
            id_nota = input("Ingrese el ID de la nota que desea modificar: ").strip()
            nueva_nota = input("Ingrese la nueva calificación: ").strip()
            cursor.execute("UPDATE notas SET calificacion = ? WHERE id_nota = ?;", (nueva_nota, id_nota))
            conexion.commit()
            if cursor.rowcount > 0:
                print("✔️ Nota modificada con éxito.")
            else:
                print("❌ El ID de la nota no existe.")
                
        elif opcion == "3":
            conexion.close()
            break
        conexion.close()

def vista_root(usuario):
    """Panel de control absoluto"""
    print(f"\n--- PANEL ROOT ---")
    print(f"Modo Dios activo en el archivo: {DB_NAME}")
    input("Presione Enter para regresar al menú...")

# =====================================================================
# MENÚ PRINCIPAL
# =====================================================================

def menu_principal():
    inicializar_base_de_datos()
    while True:
        print(f"\n========== AUDIT GRADES PRO ==========")
        print(f"Base de datos: {DB_NAME}")
        print("1. Registrarse (Crear Usuario, Contraseña y Rol)")
        print("2. Iniciar Sesión")
        print("3. Salir")
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            registrar_usuario()
        elif opcion == "2":
            sesion = iniciar_sesion()
            if sesion:
                print(f"\n🔓 ¡Sesión autorizada! Rol asignado: {sesion['rol']}\n")
                if sesion["rol"] == "estudiante":
                    vista_estudiante(sesion)
                elif sesion["rol"] == "profesor":
                    vista_profesor(sesion)
                elif sesion["rol"] == "root":
                    vista_root(sesion)
        elif opcion == "3":
            print("¡Cerrando el sistema escolar!")
            break
        else:
            print("❌ Opción inválida.")

if __name__ == "__main__":
    menu_principal()