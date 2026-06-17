import customtkinter as ctk
import sqlite3
import os
from datetime import datetime

# ==================== CONFIGURACIÓN ====================
DB_NAME = r"C:\Users\VICMARYCOVA\Documents\GitHub\audit-grades-pro\bd\sistema_de_notas.db"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==================== VERIFICAR Y REPARAR TABLA NOTAS ====================
def reparar_tabla_notas():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(notas)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'profesor' not in columnas:
            cursor.execute("ALTER TABLE notas ADD COLUMN profesor TEXT")
            print("✅ Columna 'profesor' agregada")
        
        if 'comentario' not in columnas:
            cursor.execute("ALTER TABLE notas ADD COLUMN comentario TEXT")
            print("✅ Columna 'comentario' agregada")
        
        if 'fecha' not in columnas:
            cursor.execute("ALTER TABLE notas ADD COLUMN fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Columna 'fecha' agregada")
        
        if 'estado' not in columnas:
            cursor.execute("ALTER TABLE notas ADD COLUMN estado TEXT DEFAULT 'pendiente'")
            print("✅ Columna 'estado' agregada")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error reparando tabla: {e}")

reparar_tabla_notas()

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

def obtener_materias():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_materia, nombre_materia FROM materias")
        materias = cursor.fetchall()
        conn.close()
        
        if not materias:
            conn2 = conectar()
            cursor2 = conn2.cursor()
            materias_ejemplo = [
                ("MAT-101", "Matemáticas I", 4),
                ("MAT-102", "Matemáticas II", 4),
                ("FIS-101", "Física I", 4),
                ("PROG-101", "Programación I", 4),
                ("BD-101", "Base de Datos", 3),
            ]
            for m in materias_ejemplo:
                cursor2.execute("INSERT OR IGNORE INTO materias (codigo_materia, nombre_materia, creditos) VALUES (?, ?, ?)", m)
            conn2.commit()
            conn2.close()
            return materias_ejemplo
        
        return materias
    except:
        return [("MAT-101", "Matemáticas"), ("FIS-101", "Física")]

def registrar_nota(cedula_estudiante, codigo_materia, calificacion, comentario, profesor):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nombre_completo FROM estudiantes WHERE cedula_estudiante = ?", (cedula_estudiante,))
        estudiante = cursor.fetchone()
        nombre_estudiante = estudiante[0] if estudiante else cedula_estudiante
        
        cursor.execute("""
            INSERT INTO notas (cedula, estudiante, codigo_materia, nota, comentario, profesor, estado)
            VALUES (?, ?, ?, ?, ?, ?, 'pendiente')
        """, (cedula_estudiante, nombre_estudiante, codigo_materia, calificacion, comentario, profesor))
        conn.commit()
        conn.close()
        return True, "Nota registrada (pendiente de aprobación)"
    except Exception as e:
        return False, str(e)

def actualizar_nota(id_nota, calificacion, comentario):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET nota = ?, comentario = ?, estado = 'pendiente' WHERE id = ?", (calificacion, comentario, id_nota))
        conn.commit()
        conn.close()
        return True, "Nota actualizada (requiere nueva aprobación)"
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
        return True, f"✅ Nota ID {id_nota} aprobada correctamente"
    except Exception as e:
        return False, str(e)

def aprobar_todas_notas():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET estado = 'aprobada' WHERE estado = 'pendiente'")
        cantidad = cursor.rowcount
        conn.commit()
        conn.close()
        return True, f"✅ Se aprobaron {cantidad} nota(s) pendientes"
    except Exception as e:
        return False, f"❌ Error: {e}"

def rechazar_nota(id_nota, motivo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE notas SET estado = 'rechazada', comentario = ? WHERE id = ?", (f"RECHAZADA: {motivo}", id_nota))
        conn.commit()
        conn.close()
        return True, f"❌ Nota ID {id_nota} rechazada"
    except Exception as e:
        return False, str(e)

def obtener_notas_por_estado(estado=None):
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if estado:
            cursor.execute("""
                SELECT id, cedula, estudiante, codigo_materia, nota, comentario, fecha, estado, profesor
                FROM notas
                WHERE estado = ?
                ORDER BY id DESC
            """, (estado,))
        else:
            cursor.execute("""
                SELECT id, cedula, estudiante, codigo_materia, nota, comentario, fecha, estado, profesor
                FROM notas
                ORDER BY id DESC
            """)
        
        notas = cursor.fetchall()
        conn.close()
        
        resultado = []
        for n in notas:
            conn2 = conectar()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT nombre_materia FROM materias WHERE codigo_materia = ?", (n[3],))
            materia = cursor2.fetchone()
            conn2.close()
            nombre_materia = materia[0] if materia else n[3]
            resultado.append((n[0], n[2] if n[2] else n[1], nombre_materia, n[4], n[5] if n[5] else "", n[6] if n[6] else "", n[7] if len(n) > 7 else "pendiente", n[8] if len(n) > 8 else "Sistema"))
        return resultado
    except Exception as e:
        print(f"Error: {e}")
        return []

def contar_notas_pendientes():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notas WHERE estado = 'pendiente'")
        cantidad = cursor.fetchone()[0]
        conn.close()
        return cantidad
    except:
        return 0

# ==================== PANEL DE NOTAS ====================
class PanelNotas(ctk.CTkFrame):
    def __init__(self, master, usuario_actual, **kwargs):
        super().__init__(master, **kwargs)
        self.usuario_actual = usuario_actual
        self.rol = usuario_actual['rol']
        self.configure(fg_color="transparent")
        
        self.puede_aprobar = self.rol in ["control de estudio", "director", "root"]
        
        # Título
        titulo = ctk.CTkLabel(self, text=f"📋 PANEL DE CONTROL - {usuario_actual['nombre']}", 
                             font=ctk.CTkFont(size=20, weight="bold"))
        titulo.pack(pady=10)
        
        # --- FORMULARIO PARA REGISTRAR (solo profesores) ---
        if not self.puede_aprobar:
            form_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
            form_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(form_frame, text="📝 REGISTRAR NUEVA NOTA", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
            
            campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            campos_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(campos_frame, text="Cédula del Estudiante:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.cedula_entry = ctk.CTkEntry(campos_frame, placeholder_text="Ej: 28434992", width=200)
            self.cedula_entry.grid(row=1, column=0, padx=10, pady=5)
            
            ctk.CTkLabel(campos_frame, text="Materia:").grid(row=0, column=1, padx=10, pady=5, sticky="w")
            materias = [m[1] for m in obtener_materias()]
            self.materia_combo = ctk.CTkOptionMenu(campos_frame, values=materias, width=200)
            self.materia_combo.grid(row=1, column=1, padx=10, pady=5)
            
            ctk.CTkLabel(campos_frame, text="Calificación:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
            self.nota_entry = ctk.CTkEntry(campos_frame, placeholder_text="0-20", width=100)
            self.nota_entry.grid(row=1, column=2, padx=10, pady=5)
            
            ctk.CTkLabel(campos_frame, text="Comentario:").grid(row=0, column=3, padx=10, pady=5, sticky="w")
            self.comentario_entry = ctk.CTkEntry(campos_frame, placeholder_text="Opcional", width=150)
            self.comentario_entry.grid(row=1, column=3, padx=10, pady=5)
            
            btn_registrar = ctk.CTkButton(campos_frame, text="REGISTRAR", command=self.registrar_nota, fg_color="#2ecc71", height=40)
            btn_registrar.grid(row=1, column=4, padx=20, pady=5)
        
        # --- TABLA DE NOTAS ---
        self.tabla_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- PANEL INFERIOR 1: MODIFICAR / ELIMINAR ---
        panel_modificar = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
        panel_modificar.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(panel_modificar, text="✏️ MODIFICAR / ELIMINAR NOTA", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        campos_modificar = ctk.CTkFrame(panel_modificar, fg_color="transparent")
        campos_modificar.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(campos_modificar, text="ID Nota:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.id_nota_entry = ctk.CTkEntry(campos_modificar, placeholder_text="ID de la nota", width=100)
        self.id_nota_entry.grid(row=1, column=0, padx=10, pady=5)
        
        ctk.CTkLabel(campos_modificar, text="Nueva Nota:").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.nueva_nota_entry = ctk.CTkEntry(campos_modificar, placeholder_text="0-20", width=100)
        self.nueva_nota_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(campos_modificar, text="Nuevo Comentario:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.nuevo_comentario_entry = ctk.CTkEntry(campos_modificar, placeholder_text="Comentario", width=180)
        self.nuevo_comentario_entry.grid(row=1, column=2, padx=10, pady=5)
        
        btn_frame_modificar = ctk.CTkFrame(campos_modificar, fg_color="transparent")
        btn_frame_modificar.grid(row=1, column=3, padx=10, pady=5)
        
        btn_actualizar = ctk.CTkButton(btn_frame_modificar, text="💾 ACTUALIZAR", command=self.actualizar_nota_panel, 
                                      fg_color="#e67e22", height=38, width=120)
        btn_actualizar.pack(side="left", padx=5)
        
        btn_eliminar = ctk.CTkButton(btn_frame_modificar, text="🗑️ ELIMINAR", command=self.eliminar_nota_panel, 
                                    fg_color="#e74c3c", height=38, width=120)
        btn_eliminar.pack(side="left", padx=5)
        
        # --- PANEL INFERIOR 2: APROBAR / RECHAZAR (solo para control de estudio y director) ---
        if self.puede_aprobar:
            panel_aprobacion = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
            panel_aprobacion.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(panel_aprobacion, text="✅ APROBAR / RECHAZAR NOTA", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
            
            # Contador de notas pendientes
            notas_pendientes = contar_notas_pendientes()
            lbl_pendientes = ctk.CTkLabel(panel_aprobacion, text=f"📊 Notas pendientes de aprobación: {notas_pendientes}", 
                                         font=ctk.CTkFont(size=13), text_color="#f39c12")
            lbl_pendientes.pack(pady=5)
            
            # --- BOTÓN APROBAR TODAS ---
            btn_aprobar_todo = ctk.CTkButton(panel_aprobacion, text="✅ APROBAR TODAS LAS NOTAS", 
                                            command=self.aprobar_todas_notas_panel,
                                            fg_color="#2ecc71", hover_color="#27ae60", 
                                            height=40, font=ctk.CTkFont(size=13, weight="bold"))
            btn_aprobar_todo.pack(pady=10, padx=20)
            
            # --- APROBAR/RECHAZAR INDIVIDUAL (todo junto en una fila) ---
            frame_individual = ctk.CTkFrame(panel_aprobacion, fg_color="transparent")
            frame_individual.pack(fill="x", padx=20, pady=10)
            
            # ID de la nota
            ctk.CTkLabel(frame_individual, text="ID Nota:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.id_aprobar_entry = ctk.CTkEntry(frame_individual, placeholder_text="Ej: 10", width=100, height=35)
            self.id_aprobar_entry.grid(row=1, column=0, padx=10, pady=5)
            
            # Motivo (para rechazo)
            ctk.CTkLabel(frame_individual, text="Motivo:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")
            self.motivo_rechazo_entry = ctk.CTkEntry(frame_individual, placeholder_text="Motivo del rechazo", width=200, height=35)
            self.motivo_rechazo_entry.grid(row=1, column=1, padx=10, pady=5)
            
            # Botones APROBAR y RECHAZAR (juntos)
            btn_frame = ctk.CTkFrame(frame_individual, fg_color="transparent")
            btn_frame.grid(row=1, column=2, padx=10, pady=5)
            
            btn_aprobar = ctk.CTkButton(btn_frame, text="✅ APROBAR", 
                                       command=self.aprobar_nota_panel, 
                                       fg_color="#2ecc71", hover_color="#27ae60",
                                       height=38, width=110, font=ctk.CTkFont(size=12, weight="bold"))
            btn_aprobar.pack(side="left", padx=5)
            
            btn_rechazar = ctk.CTkButton(btn_frame, text="❌ RECHAZAR", 
                                        command=self.rechazar_nota_panel, 
                                        fg_color="#e74c3c", hover_color="#c0392b",
                                        height=38, width=110, font=ctk.CTkFont(size=12, weight="bold"))
            btn_rechazar.pack(side="left", padx=5)
        
        # --- BOTÓN REFRESCAR ---
        btn_refresh = ctk.CTkButton(self, text="🔄 REFRESCAR", command=self.cargar_tabla, fg_color="#3498db", width=150)
        btn_refresh.pack(pady=10)
        
        # Cargar datos iniciales
        self.cargar_tabla()
    
    def cargar_tabla(self):
        # Limpiar tabla
        for widget in self.tabla_frame.winfo_children():
            widget.destroy()
        
        notas = obtener_notas_por_estado()
        
        if not notas:
            ctk.CTkLabel(self.tabla_frame, text="📭 No hay notas registradas", font=ctk.CTkFont(size=14, slant="italic")).pack(pady=50)
            return
        
        # Encabezados
        headers = ["ID", "Estudiante", "Materia", "Nota", "Comentario", "Estado", "Profesor", "Fecha"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.tabla_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                        text_color="#3498db").grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Datos
        for row, nota in enumerate(notas, start=1):
            id_nota = nota[0]
            estudiante = nota[1] if nota[1] else "N/A"
            materia = nota[2] if nota[2] else "N/A"
            calif = nota[3] if nota[3] else "N/A"
            comentario = nota[4] if nota[4] else "-"
            estado = nota[6] if len(nota) > 6 else "pendiente"
            profesor = nota[7] if len(nota) > 7 else "Sistema"
            fecha = nota[5][:10] if nota[5] else "Sin fecha"
            
            if estado == "aprobada":
                color = "#2ecc71"
                estado_texto = "✅ APROBADA"
            elif estado == "rechazada":
                color = "#e74c3c"
                estado_texto = "❌ RECHAZADA"
            else:
                color = "#f39c12"
                estado_texto = "⏳ PENDIENTE"
            
            ctk.CTkLabel(self.tabla_frame, text=str(id_nota)).grid(row=row, column=0, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=estudiante, width=180).grid(row=row, column=1, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=materia, width=150).grid(row=row, column=2, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=str(calif), text_color=color).grid(row=row, column=3, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=comentario, width=120).grid(row=row, column=4, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=estado_texto, text_color=color).grid(row=row, column=5, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=profesor, width=120).grid(row=row, column=6, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.tabla_frame, text=fecha).grid(row=row, column=7, padx=10, pady=3, sticky="w")
    
    def registrar_nota(self):
        cedula = self.cedula_entry.get().strip()
        nota_str = self.nota_entry.get().strip()
        materia_nombre = self.materia_combo.get()
        comentario = self.comentario_entry.get().strip()
        
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
        
        exito, msg = registrar_nota(cedula, codigo, nota, comentario, self.usuario_actual['nombre'])
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.cedula_entry.delete(0, 'end')
            self.nota_entry.delete(0, 'end')
            self.comentario_entry.delete(0, 'end')
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def actualizar_nota_panel(self):
        id_nota = self.id_nota_entry.get().strip()
        nota_str = self.nueva_nota_entry.get().strip()
        comentario = self.nuevo_comentario_entry.get().strip()
        
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
        
        exito, msg = actualizar_nota(int(id_nota), nota, comentario)
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_nota_entry.delete(0, 'end')
            self.nueva_nota_entry.delete(0, 'end')
            self.nuevo_comentario_entry.delete(0, 'end')
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def eliminar_nota_panel(self):
        id_nota = self.id_nota_entry.get().strip()
        
        if not id_nota:
            self.mostrar_mensaje("Error", "Ingrese el ID de la nota", "error")
            return
        
        dialog = ctk.CTkInputDialog(text="Escribe 'CONFIRMAR' para eliminar esta nota:", title="Confirmar Eliminación")
        if dialog.get_input() != "CONFIRMAR":
            return
        
        exito, msg = eliminar_nota(int(id_nota))
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_nota_entry.delete(0, 'end')
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def aprobar_nota_panel(self):
        """Aprueba una nota individual usando el ID ingresado"""
        id_nota = self.id_aprobar_entry.get().strip()
        
        if not id_nota:
            self.mostrar_mensaje("Error", "❌ Ingrese el ID de la nota", "error")
            return
        
        try:
            id_int = int(id_nota)
        except:
            self.mostrar_mensaje("Error", "❌ El ID debe ser un número", "error")
            return
        
        # Confirmar antes de aprobar
        dialog = ctk.CTkInputDialog(
            text=f"⚠️ ¿Estás seguro de APROBAR la nota ID {id_int}?\n\nEscribe 'CONFIRMAR' para continuar:", 
            title="Confirmar Aprobación"
        )
        if dialog.get_input() != "CONFIRMAR":
            return
        
        exito, msg = aprobar_nota(id_int)
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_aprobar_entry.delete(0, 'end')
            self.motivo_rechazo_entry.delete(0, 'end')
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def rechazar_nota_panel(self):
        """Rechaza una nota individual usando el ID ingresado"""
        id_nota = self.id_aprobar_entry.get().strip()
        motivo = self.motivo_rechazo_entry.get().strip()
        
        if not id_nota:
            self.mostrar_mensaje("Error", "❌ Ingrese el ID de la nota", "error")
            return
        
        try:
            id_int = int(id_nota)
        except:
            self.mostrar_mensaje("Error", "❌ El ID debe ser un número", "error")
            return
        
        if not motivo:
            motivo = "Sin motivo especificado"
        
        # Confirmar antes de rechazar
        dialog = ctk.CTkInputDialog(
            text=f"⚠️ ¿Estás seguro de RECHAZAR la nota ID {id_int}?\nMotivo: {motivo}\n\nEscribe 'CONFIRMAR' para continuar:", 
            title="Confirmar Rechazo"
        )
        if dialog.get_input() != "CONFIRMAR":
            return
        
        exito, msg = rechazar_nota(id_int, motivo)
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.id_aprobar_entry.delete(0, 'end')
            self.motivo_rechazo_entry.delete(0, 'end')
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def aprobar_todas_notas_panel(self):
        """Aprueba TODAS las notas pendientes"""
        pendientes = contar_notas_pendientes()
        
        if pendientes == 0:
            self.mostrar_mensaje("Info", "No hay notas pendientes para aprobar", "info")
            return
        
        dialog = ctk.CTkInputDialog(
            text=f"⚠️ ¿Estás seguro de aprobar TODAS las {pendientes} notas pendientes?\n\nEscribe 'CONFIRMAR' para continuar:", 
            title="Confirmar Aprobación Masiva"
        )
        if dialog.get_input() != "CONFIRMAR":
            return
        
        exito, msg = aprobar_todas_notas()
        if exito:
            self.mostrar_mensaje("Éxito", msg, "success")
            self.cargar_tabla()
        else:
            self.mostrar_mensaje("Error", msg, "error")
    
    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        dialog = ctk.CTkToplevel(self)
        dialog.title(titulo)
        dialog.geometry("400x120")
        dialog.grab_set()
        
        colores = {"success": "#2ecc71", "error": "#e74c3c", "info": "#3498db"}
        ctk.CTkLabel(dialog, text=mensaje, font=ctk.CTkFont(size=12)).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy, fg_color=colores.get(tipo, "#3498db")).pack(pady=10)

# ==================== PANEL ESTUDIANTE ====================
class PanelEstudiante(ctk.CTkFrame):
    def __init__(self, master, usuario_actual, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text=f"🎓 ¡Bienvenido Estudiante {usuario_actual['nombre']}!", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        notas_frame = ctk.CTkScrollableFrame(frame, label_text="📚 MIS CALIFICACIONES")
        notas_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigo_materia, nota, comentario, fecha, estado
            FROM notas
            WHERE cedula = ?
            ORDER BY id DESC
        """, (usuario_actual['cedula'],))
        notas = cursor.fetchall()
        conn.close()
        
        if not notas:
            ctk.CTkLabel(notas_frame, text="📭 No tienes notas registradas", 
                        font=ctk.CTkFont(size=14, slant="italic"), text_color="gray").pack(pady=50)
        else:
            for n in notas:
                codigo = n[0]
                nota_valor = n[1]
                comentario = n[2] if n[2] else ""
                fecha = n[3][:10] if n[3] else "Sin fecha"
                estado = n[4] if len(n) > 4 else "pendiente"
                
                conn2 = conectar()
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT nombre_materia FROM materias WHERE codigo_materia = ?", (codigo,))
                materia = cursor2.fetchone()
                conn2.close()
                nombre_materia = materia[0] if materia else codigo
                
                if estado == "aprobada":
                    color = "#2ecc71"
                    estado_txt = "✅ APROBADA"
                elif estado == "rechazada":
                    color = "#e74c3c"
                    estado_txt = "❌ RECHAZADA"
                else:
                    color = "#f39c12"
                    estado_txt = "⏳ PENDIENTE"
                
                card = ctk.CTkFrame(notas_frame, corner_radius=10, fg_color="#2b2b2b")
                card.pack(fill="x", pady=5, padx=10)
                ctk.CTkLabel(card, text=nombre_materia, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10,0))
                ctk.CTkLabel(card, text=f"Nota: {nota_valor}", font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(anchor="w", padx=15)
                if comentario:
                    ctk.CTkLabel(card, text=f"💬 {comentario}", text_color="gray").pack(anchor="w", padx=15)
                ctk.CTkLabel(card, text=f"Estado: {estado_txt}", text_color=color).pack(anchor="w", padx=15)
                ctk.CTkLabel(card, text=f"📅 {fecha}", text_color="gray").pack(anchor="w", padx=15, pady=(0,10))

# ==================== VENTANA LOGIN ====================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Audit Grades Pro - Login")
        self.geometry("400x550")
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
        win.geometry("450x600")
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
        roles = ["estudiante", "profesor", "control de estudio", "director"]
        ctk.CTkOptionMenu(frame, values=roles, variable=rol_var, width=250).pack(pady=5)
        
        extra1_entry = ctk.CTkEntry(frame, placeholder_text="", width=250)
        extra1_entry.pack(pady=5)
        extra2_entry = ctk.CTkEntry(frame, placeholder_text="", width=250)
        extra2_entry.pack(pady=5)
        
        def actualizar_campos(*args):
            rol = rol_var.get()
            if rol == "estudiante":
                extra1_entry.configure(placeholder_text="Carrera")
                extra2_entry.configure(placeholder_text="Semestre")
                extra2_entry.pack()
            elif rol == "profesor":
                extra1_entry.configure(placeholder_text="Carrera que dicta")
                extra2_entry.configure(placeholder_text="Especialidad")
                extra2_entry.pack()
            elif rol in ["control de estudio", "director"]:
                extra1_entry.configure(placeholder_text="Cargo")
                extra2_entry.pack_forget()
        
        rol_var.trace("w", actualizar_campos)
        actualizar_campos()
        
        error_label = ctk.CTkLabel(frame, text="")
        error_label.pack(pady=10)
        
        def guardar():
            cedula = cedula_entry.get().strip()
            contrasena = pass_entry.get().strip()
            nombre = nombre_entry.get().strip()
            rol = rol_var.get()
            extra1 = extra1_entry.get().strip()
            extra2 = extra2_entry.get().strip()
            
            if not cedula or not contrasena or not nombre:
                error_label.configure(text="❌ Complete los campos obligatorios", text_color="red")
                return
            
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO usuarios (id_usuario, username, password, rol) VALUES (?, ?, ?, ?)", 
                              (cedula, cedula, contrasena, rol))
                
                if rol == "estudiante":
                    cursor.execute("INSERT OR REPLACE INTO estudiantes (cedula_estudiante, nombre_completo, carrera, semestre) VALUES (?, ?, ?, ?)", 
                                  (cedula, nombre, extra1, extra2))
                elif rol == "profesor":
                    cursor.execute("INSERT OR REPLACE INTO profesores (cedula_profesor, nombre_completo, carrera, especialidad) VALUES (?, ?, ?, ?)", 
                                  (cedula, nombre, extra1, extra2))
                elif rol == "control de estudio":
                    cursor.execute("INSERT OR REPLACE INTO personal (cedula_personal, nombre_completo, cargo, area) VALUES (?, ?, ?, 'Control de Estudio')", 
                                  (cedula, nombre, extra1))
                elif rol == "director":
                    cursor.execute("INSERT OR REPLACE INTO personal (cedula_personal, nombre_completo, cargo, area) VALUES (?, ?, ?, 'Dirección')", 
                                  (cedula, nombre, extra1))
                
                conn.commit()
                conn.close()
                error_label.configure(text=f"✅ {rol.title()} registrado exitosamente", text_color="green")
                win.after(1500, win.destroy)
            except Exception as e:
                error_label.configure(text=f"❌ Error: {e}", text_color="red")
        
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
        self.geometry("1400x900")
        
        top_bar = ctk.CTkFrame(self, height=50, fg_color="#1a1a1a")
        top_bar.pack(fill="x")
        
        ctk.CTkLabel(top_bar, text=f"👤 {usuario['nombre']} | Rol: {self.rol.title()}", 
                    font=ctk.CTkFont(size=14)).pack(side="left", padx=20)
        
        if self.rol in ["control de estudio", "director"]:
            ctk.CTkLabel(top_bar, text="🔓 Permisos: Aprobar/Rechazar", 
                        font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(side="left", padx=20)
        
        btn_logout = ctk.CTkButton(top_bar, text="CERRAR SESIÓN", command=self.logout, 
                                   fg_color="#e74c3c", width=120)
        btn_logout.pack(side="right", padx=20, pady=5)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        if self.rol == "estudiante":
            PanelEstudiante(self.content_frame, self.usuario).pack(fill="both", expand=True)
        else:
            PanelNotas(self.content_frame, self.usuario).pack(fill="both", expand=True)
    
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