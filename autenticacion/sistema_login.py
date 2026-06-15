import customtkinter as ctk
import sqlite3
import os
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
DB_NAME = r"C:\Users\VICMARYCOVA\Documents\GitHub\audit-grades-pro\bd\sistema_de_notas.db"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==================== VERIFICAR Y REPARAR TABLA NOTAS ====================
def verificar_tabla_notas():
    """Verifica que la tabla notas tenga todas las columnas necesarias"""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notas'")
        if not cursor.fetchone():
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT,
                    estudiante TEXT,
                    codigo_materia TEXT,
                    nota REAL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT DEFAULT 'pendiente'
                )
            """)
            print("✅ Tabla notas creada")
        else:
            # Verificar columnas existentes
            cursor.execute("PRAGMA table_info(notas)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            # Agregar columna fecha si falta
            if 'fecha' not in columnas:
                cursor.execute("ALTER TABLE notas ADD COLUMN fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                print("✅ Columna 'fecha' agregada")
            
            # Agregar columna estado si falta
            if 'estado' not in columnas:
                cursor.execute("ALTER TABLE notas ADD COLUMN estado TEXT DEFAULT 'pendiente'")
                print("✅ Columna 'estado' agregada")
            
            # Agregar columna estudiante si falta
            if 'estudiante' not in columnas:
                cursor.execute("ALTER TABLE notas ADD COLUMN estudiante TEXT")
                print("✅ Columna 'estudiante' agregada")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error verificando tabla: {e}")

# Ejecutar verificación al inicio
verificar_tabla_notas()

# ==================== FUNCIONES DE BASE DE DATOS ====================
def conectar():
    return sqlite3.connect(DB_NAME, timeout=10)

def verificar_login(usuario, contrasena):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, rol, username FROM usuarios WHERE username = ? AND password = ?", (usuario, contrasena))
        resultado = cursor.fetchone()
        if not resultado:
            cursor.execute("SELECT id_usuario, rol, username FROM usuarios WHERE id_usuario = ? AND password = ?", (usuario, contrasena))
            resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {"cedula": str(resultado[0]), "rol": resultado[1], "nombre": resultado[2]}
        return None
    except Exception as e:
        print(f"Error login: {e}")
        return None

def registrar_usuario(cedula, contrasena, rol, nombre):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM usuarios WHERE username = ?", (cedula,))
        if cursor.fetchone():
            conn.close()
            return False, "Este nombre de usuario ya existe"
        
        cursor.execute("INSERT INTO usuarios (id_usuario, username, password, rol) VALUES (?, ?, ?, ?)", 
                      (cedula, cedula, contrasena, rol))
        
        # Registrar también en tabla estudiantes
        cursor.execute("INSERT OR IGNORE INTO estudiantes (cedula_estudiante, nombre_completo) VALUES (?, ?)", (cedula, nombre))
        
        conn.commit()
        conn.close()
        return True, f"✅ {rol.title()} registrado exitosamente"
    except Exception as e:
        return False, f"❌ Error: {e}"

# ==================== FUNCIONES DE NOTAS ====================
def obtener_todas_notas(filtro_estado=None):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if filtro_estado:
            cursor.execute("""
                SELECT id, cedula, estudiante, codigo_materia, nota, fecha, estado
                FROM notas
                WHERE estado = ?
                ORDER BY id DESC
            """, (filtro_estado,))
        else:
            cursor.execute("""
                SELECT id, cedula, estudiante, codigo_materia, nota, fecha, estado
                FROM notas
                ORDER BY id DESC
            """)
        
        notas = cursor.fetchall()
        conn.close()
        
        resultado = []
        for n in notas:
            nombre_materia = obtener_nombre_materia(n[3])
            fecha_valor = n[5] if len(n) > 5 and n[5] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estado_valor = n[6] if len(n) > 6 else "pendiente"
            resultado.append((n[0], n[2] if n[2] else n[1], nombre_materia, n[4], "", fecha_valor, estado_valor, "Sistema"))
        return resultado
    except Exception as e:
        print(f"Error obtener notas: {e}")
        return []

def obtener_notas_estudiante(cedula):
    """Obtiene las notas de un estudiante específico por su cédula"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT codigo_materia, nota, fecha, estado
            FROM notas
            WHERE cedula = ?
            ORDER BY id DESC
        """, (cedula,))
        
        notas = cursor.fetchall()
        conn.close()
        
        resultado = []
        for n in notas:
            codigo = n[0]
            nota_valor = n[1]
            fecha_valor = n[2] if n[2] else datetime.now().strftime("%Y-%m-%d")
            estado_valor = n[3] if len(n) > 3 and n[3] else "pendiente"
            
            nombre_materia = obtener_nombre_materia(codigo)
            resultado.append((nombre_materia, nota_valor, "", fecha_valor, estado_valor))
        
        return resultado
    except Exception as e:
        print(f"Error obtener notas estudiante: {e}")
        return []

def obtener_nombre_materia(codigo):
    """Obtiene el nombre de una materia por su código"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_materia FROM materias WHERE codigo_materia = ?", (codigo,))
        materia = cursor.fetchone()
        conn.close()
        return materia[0] if materia else codigo
    except:
        return codigo

def obtener_materias():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_materia, nombre_materia FROM materias")
        materias = cursor.fetchall()
        conn.close()
        return materias if materias else [("MAT-101", "Matemáticas"), ("FIS-101", "Física")]
    except:
        return [("MAT-101", "Matemáticas"), ("FIS-101", "Física")]

def registrar_nota(cedula, codigo_materia, calificacion, comentario, profesor):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar si el estudiante existe
        cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?", (cedula,))
        estudiante = cursor.fetchone()
        
        if not estudiante:
            conn.close()
            return False, f"❌ Estudiante con cédula {cedula} no encontrado. Debe registrarse primero."
        
        nombre_estudiante = estudiante[0]
        
        # Insertar nota (sin especificar fecha, se usará CURRENT_TIMESTAMP)
        cursor.execute("""
            INSERT INTO notas (cedula, estudiante, codigo_materia, nota, estado)
            VALUES (?, ?, ?, ?, 'pendiente')
        """, (cedula, nombre_estudiante, codigo_materia, calificacion))
        
        conn.commit()
        conn.close()
        return True, f"✅ Nota registrada para {nombre_estudiante}"
    except Exception as e:
        return False, str(e)

def actualizar_nota(id_nota, calificacion, comentario):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET nota = ?, estado = 'pendiente' WHERE id = ?", (calificacion, id_nota))
        conn.commit()
        conn.close()
        return True, "Nota actualizada"
    except Exception as e:
        return False, str(e)

def eliminar_nota(id_nota):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notas WHERE id = ?", (id_nota,))
        conn.commit()
        conn.close()
        return True, "Nota eliminada"
    except Exception as e:
        return False, str(e)

def aprobar_nota(id_nota):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET estado = 'aprobada' WHERE id = ?", (id_nota,))
        conn.commit()
        conn.close()
        return True, "Nota aprobada"
    except Exception as e:
        return False, str(e)

def rechazar_nota(id_nota, motivo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET estado = 'rechazada' WHERE id = ?", (id_nota,))
        conn.commit()
        conn.close()
        return True, "Nota rechazada"
    except Exception as e:
        return False, str(e)

# ==================== PANEL DE NOTAS (PROFESORES) ====================
class PanelNotas(ctk.CTkFrame):
    def __init__(self, master, usuario_actual, **kwargs):
        super().__init__(master, **kwargs)
        self.usuario_actual = usuario_actual
        self.rol = usuario_actual['rol']
        self.configure(fg_color="transparent")
        
        self.puede_aprobar = self.rol in ["control de estudio", "director", "root"]
        
        titulo = ctk.CTkLabel(self, text=f"📋 PANEL DE CONTROL - {usuario_actual['nombre']}", 
                             font=ctk.CTkFont(size=18, weight="bold"))
        titulo.pack(pady=10)
        
        # Pestañas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Todas")
        self.tabview.add("Pendientes")
        self.tabview.add("Aprobadas")
        self.tabview.add("Rechazadas")
        
        self.frames = {}
        for tab in ["Todas", "Pendientes", "Aprobadas", "Rechazadas"]:
            frame = ctk.CTkScrollableFrame(self.tabview.tab(tab), fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.frames[tab] = frame
        
        # Formulario
        form_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="📝 REGISTRAR NOTA", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        campos_frame.pack(fill="x", padx=10, pady=5)
        
        self.cedula_entry = ctk.CTkEntry(campos_frame, placeholder_text="Cédula del Estudiante", width=180)
        self.cedula_entry.grid(row=0, column=0, padx=5, pady=5)
        
        materias = [m[1] for m in obtener_materias()]
        self.materia_combo = ctk.CTkOptionMenu(campos_frame, values=materias, width=180)
        self.materia_combo.grid(row=0, column=1, padx=5, pady=5)
        
        self.nota_entry = ctk.CTkEntry(campos_frame, placeholder_text="Nota (0-20)", width=100)
        self.nota_entry.grid(row=0, column=2, padx=5, pady=5)
        
        btn_registrar = ctk.CTkButton(campos_frame, text="REGISTRAR", command=self.registrar_nota, fg_color="#2ecc71")
        btn_registrar.grid(row=0, column=3, padx=10, pady=5)
        
        # Modificar
        ctk.CTkFrame(form_frame, height=2, fg_color="#555").pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(form_frame, text="✏️ MODIFICAR / ELIMINAR", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        mod_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        mod_frame.pack(fill="x", padx=10, pady=5)
        
        self.id_nota_entry = ctk.CTkEntry(mod_frame, placeholder_text="ID Nota", width=80)
        self.id_nota_entry.grid(row=0, column=0, padx=5, pady=5)
        
        self.nueva_nota_entry = ctk.CTkEntry(mod_frame, placeholder_text="Nueva Nota", width=100)
        self.nueva_nota_entry.grid(row=0, column=1, padx=5, pady=5)
        
        btn_actualizar = ctk.CTkButton(mod_frame, text="ACTUALIZAR", command=self.actualizar_nota, fg_color="#e67e22")
        btn_actualizar.grid(row=0, column=2, padx=5, pady=5)
        
        btn_eliminar = ctk.CTkButton(mod_frame, text="ELIMINAR", command=self.eliminar_nota, fg_color="#e74c3c")
        btn_eliminar.grid(row=0, column=3, padx=5, pady=5)
        
        # Aprobar/Rechazar
        if self.puede_aprobar:
            ctk.CTkFrame(form_frame, height=2, fg_color="#555").pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(form_frame, text="✅ APROBAR / RECHAZAR", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
            
            aprob_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            aprob_frame.pack(fill="x", padx=10, pady=5)
            
            self.id_aprobar_entry = ctk.CTkEntry(aprob_frame, placeholder_text="ID Nota", width=80)
            self.id_aprobar_entry.grid(row=0, column=0, padx=5, pady=5)
            
            self.motivo_entry = ctk.CTkEntry(aprob_frame, placeholder_text="Motivo (si es rechazo)", width=200)
            self.motivo_entry.grid(row=0, column=1, padx=5, pady=5)
            
            btn_aprobar = ctk.CTkButton(aprob_frame, text="APROBAR", command=self.aprobar_nota, fg_color="#2ecc71")
            btn_aprobar.grid(row=0, column=2, padx=5, pady=5)
            
            btn_rechazar = ctk.CTkButton(aprob_frame, text="RECHAZAR", command=self.rechazar_nota, fg_color="#e74c3c")
            btn_rechazar.grid(row=0, column=3, padx=5, pady=5)
        
        btn_refresh = ctk.CTkButton(self, text="🔄 REFRESCAR", command=self.cargar_tablas, fg_color="#3498db", width=150)
        btn_refresh.pack(pady=5)
        
        self.cargar_tablas()
    
    def cargar_tablas(self):
        todas = obtener_todas_notas()
        pendientes = obtener_todas_notas(filtro_estado="pendiente")
        aprobadas = obtener_todas_notas(filtro_estado="aprobada")
        rechazadas = obtener_todas_notas(filtro_estado="rechazada")
        
        self.cargar_tabla(self.frames["Todas"], todas)
        self.cargar_tabla(self.frames["Pendientes"], pendientes)
        self.cargar_tabla(self.frames["Aprobadas"], aprobadas)
        self.cargar_tabla(self.frames["Rechazadas"], rechazadas)
    
    def cargar_tabla(self, parent, notas):
        for w in parent.winfo_children():
            w.destroy()
        
        if not notas:
            ctk.CTkLabel(parent, text="📭 No hay notas", font=ctk.CTkFont(size=14, slant="italic")).pack(pady=50)
            return
        
        headers = ["ID", "Estudiante", "Materia", "Nota", "Estado", "Profesor"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(parent, text=h, font=ctk.CTkFont(weight="bold"), text_color="#3498db").grid(row=0, column=i, padx=5, pady=5)
        
        for row, nota in enumerate(notas, start=1):
            id_nota = nota[0]
            estudiante = nota[1] if nota[1] else "N/A"
            materia = nota[2] if nota[2] else "N/A"
            calif = nota[3] if nota[3] else "N/A"
            estado = nota[6] if len(nota) > 6 else "pendiente"
            profesor = nota[7] if len(nota) > 7 else "Sistema"
            
            if estado == "aprobada":
                color = "#2ecc71"
            elif estado == "rechazada":
                color = "#e74c3c"
            else:
                color = "#f39c12"
            
            ctk.CTkLabel(parent, text=str(id_nota)).grid(row=row, column=0, padx=5, pady=2)
            ctk.CTkLabel(parent, text=estudiante, width=150).grid(row=row, column=1, padx=5, pady=2)
            ctk.CTkLabel(parent, text=materia, width=120).grid(row=row, column=2, padx=5, pady=2)
            ctk.CTkLabel(parent, text=str(calif), text_color=color).grid(row=row, column=3, padx=5, pady=2)
            ctk.CTkLabel(parent, text=estado.upper(), text_color=color).grid(row=row, column=4, padx=5, pady=2)
            ctk.CTkLabel(parent, text=profesor, width=120).grid(row=row, column=5, padx=5, pady=2)
    
    def registrar_nota(self):
        cedula = self.cedula_entry.get().strip()
        nota_str = self.nota_entry.get().strip()
        materia_nombre = self.materia_combo.get()
        
        if not cedula or not nota_str:
            self.mostrar_mensaje("Error", "Complete cédula y nota", "error")
            return
        
        try:
            nota = float(nota_str)
            if nota < 0 or nota > 20:
                self.mostrar_mensaje("Error", "Nota entre 0 y 20", "error")
                return
        except:
            self.mostrar_mensaje("Error", "Nota inválida", "error")
            return
        
        codigo = "MAT-101"
        for m in obtener_materias():
            if m[1] == materia_nombre:
                codigo = m[0]
                break
        
        exito, msg = registrar_nota(cedula, codigo, nota, "", self.usuario_actual['nombre'])
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.cedula_entry.delete(0, 'end')
            self.nota_entry.delete(0, 'end')
            self.cargar_tablas()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def actualizar_nota(self):
        id_nota = self.id_nota_entry.get().strip()
        nota_str = self.nueva_nota_entry.get().strip()
        
        if not id_nota or not nota_str:
            self.mostrar_mensaje("Error", "Complete ID y nueva nota", "error")
            return
        
        try:
            nota = float(nota_str)
            if nota < 0 or nota > 20:
                self.mostrar_mensaje("Error", "Nota entre 0 y 20", "error")
                return
        except:
            self.mostrar_mensaje("Error", "Nota inválida", "error")
            return
        
        exito, msg = actualizar_nota(int(id_nota), nota, "")
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_nota_entry.delete(0, 'end')
            self.nueva_nota_entry.delete(0, 'end')
            self.cargar_tablas()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def eliminar_nota(self):
        id_nota = self.id_nota_entry.get().strip()
        if not id_nota:
            self.mostrar_mensaje("Error", "Ingrese el ID", "error")
            return
        
        dialog = ctk.CTkInputDialog(text="Escribe 'CONFIRMAR' para eliminar:", title="Confirmar")
        if dialog.get_input() != "CONFIRMAR":
            return
        
        exito, msg = eliminar_nota(int(id_nota))
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_nota_entry.delete(0, 'end')
            self.cargar_tablas()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def aprobar_nota(self):
        if not self.puede_aprobar:
            self.mostrar_mensaje("Error", "No tienes permiso", "error")
            return
        
        id_nota = self.id_aprobar_entry.get().strip()
        if not id_nota:
            self.mostrar_mensaje("Error", "Ingrese el ID", "error")
            return
        
        exito, msg = aprobar_nota(int(id_nota))
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_aprobar_entry.delete(0, 'end')
            self.cargar_tablas()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def rechazar_nota(self):
        if not self.puede_aprobar:
            self.mostrar_mensaje("Error", "No tienes permiso", "error")
            return
        
        id_nota = self.id_aprobar_entry.get().strip()
        motivo = self.motivo_entry.get().strip()
        
        if not id_nota:
            self.mostrar_mensaje("Error", "Ingrese el ID", "error")
            return
        if not motivo:
            motivo = "Sin motivo"
        
        exito, msg = rechazar_nota(int(id_nota), motivo)
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_aprobar_entry.delete(0, 'end')
            self.motivo_entry.delete(0, 'end')
            self.cargar_tablas()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        dialog = ctk.CTkToplevel(self)
        dialog.title(titulo)
        dialog.geometry("350x120")
        dialog.grab_set()
        
        colores = {"success": "#2ecc71", "error": "#e74c3c", "info": "#3498db"}
        ctk.CTkLabel(dialog, text=mensaje, font=ctk.CTkFont(size=12)).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy, fg_color=colores.get(tipo, "#3498db")).pack(pady=10)

# ==================== PANEL ESTUDIANTE ====================
class PanelEstudiante(ctk.CTkFrame):
    def __init__(self, master, usuario_actual, **kwargs):
        super().__init__(master, **kwargs)
        self.usuario_actual = usuario_actual
        self.configure(fg_color="transparent")
        
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"🎓 ¡Bienvenido Estudiante {usuario_actual['nombre']}!", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(frame, text=f"Cédula: {usuario_actual['cedula']}", font=ctk.CTkFont(size=12, slant="italic")).pack(pady=5)
        
        separator = ctk.CTkFrame(frame, height=2, fg_color="#3498db")
        separator.pack(fill="x", pady=15, padx=50)
        
        ctk.CTkLabel(frame, text="📚 MIS CALIFICACIONES", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        notas_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        notas_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        # Cargar notas del estudiante
        notas = obtener_notas_estudiante(usuario_actual['cedula'])
        
        if not notas:
            ctk.CTkLabel(notas_frame, text="📭 No tienes notas registradas aún\n\nSi eres estudiante, pide a tu profesor que registre tus notas con tu cédula.", 
                        font=ctk.CTkFont(size=14, slant="italic"), text_color="gray").pack(pady=50)
        else:
            for nota in notas:
                materia, calif, comentario, fecha, estado = nota
                
                if estado == "aprobada":
                    color = "#2ecc71"
                    estado_txt = "✅ APROBADA"
                elif estado == "rechazada":
                    color = "#e74c3c"
                    estado_txt = "❌ RECHAZADA"
                else:
                    color = "#f39c12"
                    estado_txt = "⏳ PENDIENTE DE APROBACIÓN"
                
                card = ctk.CTkFrame(notas_frame, corner_radius=12, fg_color="#2b2b2b")
                card.pack(fill="x", pady=8, padx=10)
                
                ctk.CTkLabel(card, text=materia or "Sin materia", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10,0))
                ctk.CTkLabel(card, text=f"Calificación: {calif}", font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="w", padx=15)
                ctk.CTkLabel(card, text=f"Estado: {estado_txt}", font=ctk.CTkFont(size=12), text_color=color).pack(anchor="w", padx=15)
                if comentario:
                    ctk.CTkLabel(card, text=f"💬 Comentario: {comentario}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15)
                ctk.CTkLabel(card, text=f"📅 Fecha: {fecha[:10] if fecha else 'Sin fecha'}", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=15, pady=(0,10))
        
        btn_refresh = ctk.CTkButton(frame, text="🔄 REFRESCAR", command=self.refrescar_notas, fg_color="#3498db", width=150)
        btn_refresh.pack(pady=10)
    
    def refrescar_notas(self):
        # Recargar el frame
        for widget in self.winfo_children():
            widget.destroy()
        self.__init__(self.master, self.usuario_actual)

# ==================== VENTANA LOGIN ====================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Audit Grades Pro - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.pack(pady=40, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="🎓 AUDIT GRADES PRO", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkLabel(frame, text="Sistema de Gestión de Notas", font=ctk.CTkFont(size=12)).pack(pady=5)
        
        self.user_entry = ctk.CTkEntry(frame, placeholder_text="Usuario", width=250, height=40)
        self.user_entry.pack(pady=10)
        
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", width=250, height=40, show="*")
        self.pass_entry.pack(pady=10)
        
        ctk.CTkButton(frame, text="🔑 INICIAR SESIÓN", command=self.login, height=40).pack(pady=10)
        ctk.CTkButton(frame, text="📝 REGISTRARSE", command=self.registro, height=35, fg_color="transparent", border_width=2).pack(pady=5)
        ctk.CTkButton(frame, text="🚪 SALIR", command=self.destroy, height=35, fg_color="transparent", text_color="red").pack(pady=5)
    
    def login(self):
        usuario = self.user_entry.get().strip()
        contrasena = self.pass_entry.get().strip()
        
        if not usuario or not contrasena:
            self.mostrar_error("Complete todos los campos")
            return
        
        datos = verificar_login(usuario, contrasena)
        if datos:
            self.destroy()
            MainApp(datos).mainloop()
        else:
            self.mostrar_error("Credenciales incorrectas")
    
    def registro(self):
        win = ctk.CTkToplevel(self)
        win.title("Registro de Usuario")
        win.geometry("400x550")
        win.grab_set()
        
        frame = ctk.CTkFrame(win, corner_radius=20)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="📝 REGISTRO DE USUARIO", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        cedula_entry = ctk.CTkEntry(frame, placeholder_text="Cédula / Usuario", width=250)
        cedula_entry.pack(pady=5)
        
        pass_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", width=250, show="*")
        pass_entry.pack(pady=5)
        
        nombre_entry = ctk.CTkEntry(frame, placeholder_text="Nombre completo", width=250)
        nombre_entry.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Tipo de usuario:").pack(pady=(10,0))
        rol_var = ctk.StringVar(value="estudiante")
        ctk.CTkOptionMenu(frame, values=["estudiante", "profesor", "control de estudio", "director"], variable=rol_var, width=250).pack(pady=5)
        
        error_label = ctk.CTkLabel(frame, text="")
        error_label.pack(pady=10)
        
        def guardar():
            cedula = cedula_entry.get().strip()
            contrasena = pass_entry.get().strip()
            nombre = nombre_entry.get().strip()
            rol = rol_var.get()
            
            if not cedula or not contrasena or not nombre:
                error_label.configure(text="❌ Complete todos los campos", text_color="red")
                return
            
            exito, msg = registrar_usuario(cedula, contrasena, rol, nombre)
            if exito:
                error_label.configure(text=msg, text_color="green")
                win.after(1500, win.destroy)
            else:
                error_label.configure(text=msg, text_color="red")
        
        ctk.CTkButton(frame, text="REGISTRAR", command=guardar, height=40).pack(pady=20)
    
    def mostrar_error(self, msg):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("300x100")
        ctk.CTkLabel(dialog, text=msg).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack()

# ==================== VENTANA PRINCIPAL ====================
class MainApp(ctk.CTk):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.rol = usuario['rol']
        
        self.title(f"Audit Grades Pro - {self.rol.title()}")
        self.geometry("1100x650")
        
        # Barra superior
        top_bar = ctk.CTkFrame(self, height=50, fg_color="#1a1a1a")
        top_bar.pack(fill="x")
        
        ctk.CTkLabel(top_bar, text=f"👤 {usuario['nombre']} | Rol: {self.rol.title()}", font=ctk.CTkFont(size=14)).pack(side="left", padx=20)
        
        if self.rol in ["control de estudio", "director"]:
            ctk.CTkLabel(top_bar, text="🔓 Permisos especiales: Aprobar/Rechazar notas", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(side="left", padx=20)
        
        btn_logout = ctk.CTkButton(top_bar, text="CERRAR SESIÓN", command=self.logout, fg_color="#e74c3c", width=120)
        btn_logout.pack(side="right", padx=20, pady=5)
        
        # Contenido
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.rol == "estudiante":
            PanelEstudiante(self.content, self.usuario).pack(fill="both", expand=True)
        else:
            PanelNotas(self.content, self.usuario).pack(fill="both", expand=True)
    
    def logout(self):
        self.destroy()
        LoginWindow().mainloop()

# ==================== EJECUTAR ====================
if __name__ == "__main__":
    print("="*50)
    print("🎓 AUDIT GRADES PRO")
    print("="*50)
    
    if not os.path.exists(DB_NAME):
        print("❌ Base de datos no encontrada")
        exit(1)
    
    print("✅ Base de datos encontrada")
    print("="*50)
    
    app = LoginWindow()
    app.mainloop()