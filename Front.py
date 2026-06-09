import customtkinter as ctk
from datetime import datetime
import sqlite3
import os

# =====================================================================
# CONFIGURACIÓN Y VERIFICACIÓN AUTOMÁTICA DE LA BASE DE DATOS
# =====================================================================

DB_PATH = os.path.join("bd", "sistema_de_notas.db")

def verificar_y_crear_estructura():
    """Verifica y crea automáticamente la estructura necesaria si no existe"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        estructura_modificada = False
        
        # 1. Verificar/Crear tabla materias
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='materias'
        """)
        
        if not cursor.fetchone():
            print("Creando tabla 'materias'...")
            cursor.execute('''
                CREATE TABLE materias (
                    codigo_materia TEXT PRIMARY KEY,
                    nombre_materia TEXT NOT NULL UNIQUE,
                    descripcion TEXT,
                    creditos INTEGER DEFAULT 3,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            estructura_modificada = True
            
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
            print("✅ Materias creadas exitosamente")
        
        # 2. Verificar que la tabla notas tenga la columna codigo_materia
        cursor.execute("PRAGMA table_info(notas)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'codigo_materia' not in columnas:
            print("Agregando columna 'codigo_materia' a la tabla notas...")
            cursor.execute("ALTER TABLE notas ADD COLUMN codigo_materia TEXT DEFAULT 'MAT-01'")
            cursor.execute("UPDATE notas SET codigo_materia = 'MAT-01' WHERE codigo_materia IS NULL")
            estructura_modificada = True
            print("✅ Columna agregada")
        
        # 3. Verificar que la tabla auditoria_notas tenga la estructura correcta
        cursor.execute("PRAGMA table_info(auditoria_notas)")
        columnas_aud = [col[1] for col in cursor.fetchall()]
        
        if 'fecha_cambio' not in columnas_aud:
            print("Actualizando tabla 'auditoria_notas'...")
            try:
                cursor.execute("ALTER TABLE auditoria_notas ADD COLUMN fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                estructura_modificada = True
            except:
                pass
        
        if estructura_modificada:
            conn.commit()
            print("Estructura de base de datos actualizada correctamente")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Error verificando estructura: {e}")
        return False

# Ejecutar verificación automática
verificar_y_crear_estructura()

# =====================================================================
# IMPORTAR FUNCIONES DE AUDITORIA
# =====================================================================

try:
    from auditoria import (registrar_auditoria, validar_nota, 
                           obtener_todos_los_registros, modificar_auditoria, 
                           eliminar_auditoria)
except Exception as e:
    print(f"Error importando auditoria: {e}")
    def registrar_auditoria(*args, **kwargs): return False
    def validar_nota(*args, **kwargs): return True, ""
    def obtener_todos_los_registros(*args, **kwargs): return []
    def modificar_auditoria(*args, **kwargs): return False, ""
    def eliminar_auditoria(*args, **kwargs): return False, ""

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ
# =====================================================================

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  


class ActionPanel(ctk.CTkFrame):
    """Formulario lateral con opciones de Registro, Actualización y Eliminación."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=["#f8f9fa", "#1e222b"], corner_radius=12)
        
        self.title_label = ctk.CTkLabel(
            self, text="Panel de Control", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(15, 10), padx=15, anchor="w")
        
        # CAMPO DE USUARIO
        self.user_label = ctk.CTkLabel(self, text="👤 Usuario / Operador:", font=ctk.CTkFont(size=11, weight="bold"))
        self.user_label.pack(padx=15, anchor="w")
        self.user_entry = ctk.CTkEntry(self, height=30, placeholder_text="Ej: Wilmary_Control")
        self.user_entry.pack(fill="x", pady=(2, 10), padx=15)
        
        self.separator = ctk.CTkFrame(self, height=2, fg_color="gray")
        self.separator.pack(fill="x", padx=15, pady=5)
        
        # ENTRADAS
        self.student_name_entry = ctk.CTkEntry(self, placeholder_text="Nombre del Estudiante", height=38)
        self.student_name_entry.pack(fill="x", pady=6, padx=15)
        
        self.student_entry = ctk.CTkEntry(self, placeholder_text="Cédula (CI)", height=38)
        self.student_entry.pack(fill="x", pady=6, padx=15)
        
        self.subject_menu = ctk.CTkOptionMenu(self, values=["Matemáticas", "Física", "Programación", "Química"], height=38)
        self.subject_menu.pack(fill="x", pady=6, padx=15)
        
        self.grade_entry = ctk.CTkEntry(self, placeholder_text="Nota Final (0-20)", height=38)
        self.grade_entry.pack(fill="x", pady=6, padx=15)
        
        # BOTONES
        self.submit_btn = ctk.CTkButton(
            self, text="➕ Registrar Calificación", 
            fg_color="#2ecc71", hover_color="#27ae60",
            height=38, font=ctk.CTkFont(weight="bold"),
            command=self._on_submit
        )
        self.submit_btn.pack(fill="x", pady=(12, 4), padx=15)

        self.update_btn = ctk.CTkButton(
            self, text="🔧 Actualizar Registro", 
            fg_color="#e67e22", hover_color="#d35400",
            height=38, font=ctk.CTkFont(weight="bold"),
            command=self._on_update
        )
        self.update_btn.pack(fill="x", pady=4, padx=15)

        self.delete_btn = ctk.CTkButton(
            self, text="❌ Eliminar Registro", 
            fg_color="#e74c3c", hover_color="#c0392b",
            height=38, font=ctk.CTkFont(weight="bold"),
            command=self._on_delete
        )
        self.delete_btn.pack(fill="x", pady=(4, 15), padx=15)
        
        # Botón de refrescar manual
        self.refresh_btn = ctk.CTkButton(
            self, text="🔄 Refrescar Tablas", 
            fg_color="#3498db", hover_color="#2980b9",
            height=32, font=ctk.CTkFont(size=12),
            command=self._on_refresh
        )
        self.refresh_btn.pack(fill="x", pady=(5, 10), padx=15)

    def _reset_borders(self):
        self.student_name_entry.configure(border_color=["#979da2", "#565b5e"])
        self.student_entry.configure(border_color=["#979da2", "#565b5e"])
        self.grade_entry.configure(border_color=["#979da2", "#565b5e"])

    def _on_refresh(self):
        """Refresca manualmente todas las vistas"""
        self.winfo_toplevel().refresh_all_views()
        self._mostrar_mensaje("Info", "Tablas actualizadas", "info")

    def _on_submit(self):
        self._reset_borders()
        usuario_actual = self.user_entry.get().strip() or "Anonimo"
        nombre = self.student_name_entry.get().strip()
        cedula = self.student_entry.get().strip()
        grade = self.grade_entry.get().strip()  
        subject = self.subject_menu.get()
        
        if not nombre or not cedula or not grade:
            if not nombre: self.student_name_entry.configure(border_color="#e74c3c")
            if not cedula: self.student_entry.configure(border_color="#e74c3c")
            if not grade: self.grade_entry.configure(border_color="#e74c3c")
            self._mostrar_mensaje("Error", "Complete todos los campos", "error")
            return
        
        es_valida, msg = validar_nota(grade)
        if not es_valida:
            self.grade_entry.configure(border_color="#e74c3c")
            self._mostrar_mensaje("Error", msg, "error")
            return 
        
        identificador_completo = f"{nombre} [{cedula}]"
        
        # Guardar en BD
        exito = registrar_auditoria(usuario=usuario_actual, estudiante=identificador_completo, 
                                    materia=subject, nota_nueva_str=grade, nota_anterior=0)
        
        if exito:
            self._mostrar_mensaje("Éxito", f"Nota {grade} registrada para {nombre}", "success")
        else:
            self._mostrar_mensaje("Error", "No se pudo guardar en la base de datos", "error")
        
        self.winfo_toplevel().refresh_all_views()
        self.student_name_entry.delete(0, 'end')
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')

    def _on_update(self):
        self._reset_borders()
        usuario_actual = self.user_entry.get().strip() or "Anonimo"
        nombre = self.student_name_entry.get().strip()
        cedula = self.student_entry.get().strip()
        grade = self.grade_entry.get().strip()  
        subject = self.subject_menu.get()
        
        if not cedula or not grade:
            if not cedula: self.student_entry.configure(border_color="#e74c3c")
            if not grade: self.grade_entry.configure(border_color="#e74c3c")
            self._mostrar_mensaje("Error", "Cédula y nota son requeridos", "error")
            return
        
        es_valida, msg = validar_nota(grade)
        if not es_valida:
            self.grade_entry.configure(border_color="#e74c3c")
            self._mostrar_mensaje("Error", msg, "error")
            return
        
        identificador = f"{nombre} [{cedula}]" if nombre else cedula
        
        exito, mensaje = modificar_auditoria(usuario=usuario_actual, estudiante=identificador, 
                                            materia=subject, nota_nueva_str=grade)
        
        if exito:
            self._mostrar_mensaje("Éxito", mensaje, "success")
        else:
            self._mostrar_mensaje("Error", mensaje, "error")
            
        self.winfo_toplevel().refresh_all_views()
        self.student_name_entry.delete(0, 'end')
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')

    def _on_delete(self):
        self._reset_borders()
        usuario_actual = self.user_entry.get().strip() or "Anonimo"
        nombre = self.student_name_entry.get().strip()
        cedula = self.student_entry.get().strip()
        subject = self.subject_menu.get()
        
        if not cedula:
            self.student_entry.configure(border_color="#e74c3c")
            self._mostrar_mensaje("Error", "Ingrese la cédula del estudiante", "error")
            return
        
        # Confirmar eliminación
        dialog = ctk.CTkInputDialog(
            text=f"¿Eliminar TODAS las notas de {nombre if nombre else cedula} en {subject}?\n\nEscribe 'CONFIRMAR' para continuar:", 
            title="⚠️ Confirmar Eliminación"
        )
        if dialog.get_input() != "CONFIRMAR":
            return
        
        identificador = f"{nombre} [{cedula}]" if nombre else cedula
        exito, mensaje = eliminar_auditoria(usuario=usuario_actual, estudiante=identificador, materia=subject)
        
        if exito:
            self._mostrar_mensaje("Éxito", mensaje, "success")
        else:
            self._mostrar_mensaje("Error", mensaje, "error")
            
        self.winfo_toplevel().refresh_all_views()
        self.student_name_entry.delete(0, 'end')
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')

    def _mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """Muestra un mensaje emergente"""
        colores = {"success": "#2ecc71", "error": "#e74c3c", "warning": "#f39c12", "info": "#3498db"}
        dialog = ctk.CTkToplevel(self)
        dialog.title(titulo)
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text=mensaje, font=ctk.CTkFont(size=12))
        label.pack(pady=30, padx=20)
        
        btn = ctk.CTkButton(dialog, text="Aceptar", command=dialog.destroy, fg_color=colores.get(tipo, "#3498db"))
        btn.pack(pady=10)


class AuditLogsTable(ctk.CTkScrollableFrame):
    """Historial de notas - LEE DE LA BD"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=2)
        self.grid_columnconfigure(4, weight=1)
        self.current_row = 1
        self.filas = []
        self.construir_cabeceras()

    def construir_cabeceras(self):
        headers = ["Fecha", "Usuario", "Estudiante", "Materia", "Nota"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"), 
                              text_color="#3498db", anchor="w")
            lbl.grid(row=0, column=col, padx=12, pady=8, sticky="w")

    def limpiar_tabla(self):
        for fila in self.filas:
            for widget in fila:
                widget.destroy()
        self.filas.clear()
        self.current_row = 1

    def add_log_entry(self, fecha, usuario, estudiante, materia, nota):
        fila_widgets = []
        try:
            nota_val = float(nota)
            color = "#2ecc71" if nota_val >= 10 else "#e74c3c"
        except:
            color = ["#2c3e50", "#ffffff"]
        
        for col_idx, text in enumerate([fecha, usuario, estudiante, materia, nota]):
            lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12), 
                              text_color=color if col_idx == 4 else ["#2c3e50", "#ffffff"], anchor="w")
            lbl.grid(row=self.current_row, column=col_idx, padx=12, pady=6, sticky="w")
            fila_widgets.append(lbl)
        self.filas.append(fila_widgets)
        self.current_row += 1
    
    def cargar_registros_desde_bd(self):
        self.limpiar_tabla()
        registros = obtener_todos_los_registros()
        
        if not registros:
            lbl_empty = ctk.CTkLabel(self, text="📭 No hay registros de notas. Use el Panel de Control para agregar.",
                                     font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
            lbl_empty.grid(row=1, column=0, columnspan=5, pady=30)
            return
        
        for r in registros:
            if len(r) >= 5:
                self.add_log_entry(r[0], r[1], r[2], r[3], r[4])


class StudentInfoModule(ctk.CTkFrame):
    """Fichas de Alumnos desde la BD"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        self.proposal_banner = ctk.CTkLabel(
            self, text="📌 EXPEDIENTES: Listado de estudiantes con notas registradas",
            font=ctk.CTkFont(size=11, slant="italic"), text_color="#2ecc71",
            corner_radius=6, height=30
        )
        self.proposal_banner.pack(fill="x", pady=(0, 15))
        
        self.scroll_info = ctk.CTkScrollableFrame(self, label_text="Fichas Técnicas del Alumnado")
        self.scroll_info.pack(fill="both", expand=True)
        self.scroll_info.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.widgets_dinamicos = []
        self.actualizar_alumnos()

    def actualizar_alumnos(self):
        for w in self.widgets_dinamicos:
            w.destroy()
        self.widgets_dinamicos.clear()
        
        headers = ["Estudiante", "Cédula", "Materias", "Promedio", "Estado"]
        for idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_info, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                              text_color="#3498db")
            lbl.grid(row=0, column=idx, padx=10, pady=5)
            self.widgets_dinamicos.append(lbl)
        
        registros = obtener_todos_los_registros()
        alumnos_data = {}
        
        for r in registros:
            if len(r) >= 5:
                estudiante_raw = r[2]
                materia = r[3]
                nota = float(r[4]) if r[4] else 0
                
                if "[" in estudiante_raw:
                    nombre = estudiante_raw.split(" [")[0]
                    cedula = estudiante_raw.split("[")[1].replace("]", "")
                else:
                    nombre = estudiante_raw
                    cedula = estudiante_raw
                
                if cedula not in alumnos_data:
                    alumnos_data[cedula] = {"nombre": nombre, "materias": {}, "total_notas": 0, "cantidad": 0}
                
                if materia not in alumnos_data[cedula]["materias"]:
                    alumnos_data[cedula]["materias"][materia] = []
                alumnos_data[cedula]["materias"][materia].append(nota)
                alumnos_data[cedula]["total_notas"] += nota
                alumnos_data[cedula]["cantidad"] += 1

        if not alumnos_data:
            lbl_empty = ctk.CTkLabel(self.scroll_info, text="No hay alumnos registrados",
                                     font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
            lbl_empty.grid(row=1, column=0, columnspan=5, pady=30)
            self.widgets_dinamicos.append(lbl_empty)
            return

        for row_idx, (cedula, datos) in enumerate(alumnos_data.items(), start=1):
            promedio = datos["total_notas"] / datos["cantidad"] if datos["cantidad"] > 0 else 0
            materias_str = ", ".join([f"{m}: {sum(n)/len(n):.1f}" for m, n in datos["materias"].items()])
            estado = "✅ Aprobado" if promedio >= 10 else "⚠️ Recuperación"
            estado_color = "#2ecc71" if promedio >= 10 else "#e74c3c"
            
            row_data = [datos["nombre"], cedula, materias_str[:50], f"{promedio:.2f}", estado]
            for col_idx, text in enumerate(row_data):
                lbl = ctk.CTkLabel(self.scroll_info, text=text, font=ctk.CTkFont(size=11),
                                  text_color=estado_color if col_idx == 4 else ["#2c3e50", "#ffffff"])
                lbl.grid(row=row_idx, column=col_idx, padx=10, pady=8, sticky="w")
                self.widgets_dinamicos.append(lbl)


class SingleStudentSearchModule(ctk.CTkFrame):
    """Búsqueda Individual - Lee de la BD"""
    def __init__(self, master, action_panel_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.action_panel = action_panel_ref 
        
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", pady=(0, 15))
        
        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Buscar por cédula o nombre...", width=250)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        btn_search = ctk.CTkButton(search_bar, text="🔍 Buscar", width=90, command=self._buscar_estudiante)
        btn_search.pack(side="left")
        
        self.result_box = ctk.CTkScrollableFrame(self, fg_color=["#f8f9fa", "#1e222b"], corner_radius=8)
        self.result_box.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.info_label = ctk.CTkLabel(self.result_box, text="🔎 Ingrese cédula o nombre para buscar",
                                       font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.info_label.pack(expand=True, pady=50)

    def _buscar_estudiante(self):
        busqueda = self.search_entry.get().strip().lower()
        if not busqueda:
            return
        
        for w in self.result_box.winfo_children():
            w.destroy()
        
        registros = obtener_todos_los_registros()
        
        coincidencias = []
        for r in registros:
            if len(r) >= 5 and (busqueda in r[2].lower() or busqueda in r[2]):
                coincidencias.append(r)
        
        if not coincidencias:
            lbl = ctk.CTkLabel(self.result_box, text=f"❌ No se encontraron registros para: {busqueda}",
                               text_color="#e74c3c", font=ctk.CTkFont(size=12))
            lbl.pack(pady=20)
            return
        
        header_lbl = ctk.CTkLabel(self.result_box, text=f"📊 Resultados: {len(coincidencias)} registro(s)",
                                  font=ctk.CTkFont(weight="bold", size=14))
        header_lbl.pack(pady=10, padx=15, anchor="w")
        
        estudiantes_dict = {}
        for r in coincidencias:
            estudiante_raw = r[2]
            materia = r[3]
            nota = r[4]
            fecha = r[0]
            
            if "[" in estudiante_raw:
                nombre = estudiante_raw.split(" [")[0]
                cedula = estudiante_raw.split("[")[1].replace("]", "")
            else:
                nombre = estudiante_raw
                cedula = estudiante_raw
            
            if cedula not in estudiantes_dict:
                estudiantes_dict[cedula] = {"nombre": nombre, "notas": []}
            estudiantes_dict[cedula]["notas"].append((fecha, materia, nota))
        
        for cedula, datos in estudiantes_dict.items():
            estudiante_frame = ctk.CTkFrame(self.result_box, fg_color=["#ffffff", "#2b2b2b"], corner_radius=8)
            estudiante_frame.pack(fill="x", padx=10, pady=5)
            
            nombre_label = ctk.CTkLabel(estudiante_frame, text=f"👨‍🎓 {datos['nombre']} - CI: {cedula}",
                                        font=ctk.CTkFont(weight="bold", size=13))
            nombre_label.pack(pady=(8, 5), padx=10, anchor="w")
            
            for fecha, materia, nota in datos["notas"]:
                nota_frame = ctk.CTkFrame(estudiante_frame, fg_color="transparent")
                nota_frame.pack(fill="x", padx=20, pady=2)
                
                materia_lbl = ctk.CTkLabel(nota_frame, text=f"📚 {materia}:", font=ctk.CTkFont(size=11), width=100)
                materia_lbl.pack(side="left", padx=5)
                
                nota_lbl = ctk.CTkLabel(nota_frame, text=nota, font=ctk.CTkFont(weight="bold", size=11),
                                        text_color="#2ecc71" if float(nota) >= 10 else "#e74c3c")
                nota_lbl.pack(side="left", padx=5)
                
                fecha_lbl = ctk.CTkLabel(nota_frame, text=f"({fecha[:10]})", font=ctk.CTkFont(size=9), text_color="gray")
                fecha_lbl.pack(side="left", padx=5)
                
                btn_cargar = ctk.CTkButton(nota_frame, text="✏️ Editar", width=60, height=22,
                                           fg_color="#34495e", hover_color="#e67e22",
                                           command=lambda n=datos['nombre'], c=cedula, m=materia, nt=nota: 
                                           self._cargar_en_formulario(c, n, m, nt))
                btn_cargar.pack(side="right", padx=5)
            
            ctk.CTkFrame(estudiante_frame, height=1, fg_color="gray").pack(fill="x", pady=5)

    def _cargar_en_formulario(self, cedula, nombre, materia, nota):
        self.action_panel.student_name_entry.delete(0, 'end')
        self.action_panel.student_name_entry.insert(0, nombre)
        self.action_panel.student_entry.delete(0, 'end')
        self.action_panel.student_entry.insert(0, cedula)
        self.action_panel.subject_menu.set(materia)
        self.action_panel.grade_entry.delete(0, 'end')
        self.action_panel.grade_entry.insert(0, str(nota).replace(".0", ""))


class TeacherDashboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)   
        self.grid_columnconfigure(1, weight=3)   
        self.grid_rowconfigure(0, weight=1)
        
        self.action_panel = ActionPanel(self)
        self.action_panel.grid(row=0, column=0, padx=(0, 15), pady=10, sticky="nsew")
        
        self.tab_control = ctk.CTkTabview(self)
        self.tab_control.grid(row=0, column=1, pady=0, sticky="nsew")
        
        self.tab_control.add("📋 Notas Generales")
        self.tab_control.add("👥 Información Alumnos")
        self.tab_control.add("🔎 Búsqueda Individual")
        
        self.logs_tab = AuditLogsTable(self.tab_control.tab("📋 Notas Generales"))
        self.logs_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.info_tab = StudentInfoModule(self.tab_control.tab("👥 Información Alumnos"))
        self.info_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.search_tab = SingleStudentSearchModule(self.tab_control.tab("🔎 Búsqueda Individual"), 
                                                     action_panel_ref=self.action_panel)
        self.search_tab.pack(fill="both", expand=True, padx=5, pady=5)


class AuditGradesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📚 SISTEMA DE GESTIÓN ACADÉMICA")
        self.geometry("1300x720") 
        self.minsize(1000, 580)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.main_dashboard = TeacherDashboard(self)
        self.main_dashboard.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.after(500, self.refresh_all_views)
        self.iniciar_auto_refresh()
    
    def iniciar_auto_refresh(self):
        """Actualiza automáticamente las tablas cada 5 segundos"""
        self.refresh_all_views()
        self.after(5000, self.iniciar_auto_refresh)
    
    def refresh_all_views(self):
        """Refresca todas las vistas con datos actuales de la BD"""
        try:
            self.main_dashboard.logs_tab.cargar_registros_desde_bd()
            self.main_dashboard.info_tab.actualizar_alumnos()
        except Exception as e:
            print(f"🔄 Actualizando vistas: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("Iniciando Sistema de Gestión Académica")
    print("=" * 50)
    app = AuditGradesApp() 
    app.mainloop()