import customtkinter as ctk
from datetime import datetime

# =====================================================================
# MEMORIA ACTIVA DEL SISTEMA (Base de datos local en tiempo real)
# =====================================================================
MEMORIA_AUDITORIA = []

try:
    from auditoria import registrar_auditoria, validar_nota, obtener_todos_los_registros, modificar_auditoria
except Exception as e:
    print(f"⚠️ Modo seguro activado. Los datos operarán 100% en vivo desde la memoria del Front. {e}")
    def registrar_auditoria(*args, **kwargs): pass
    def validar_nota(*args, **kwargs): return True, ""
    def obtener_todos_los_registros(*args, **kwargs): return []
    def modificar_auditoria(*args, **kwargs): return True, ""

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  


class ActionPanel(ctk.CTkFrame):
    """Formulario lateral libre de datos estáticos y listo para el Login."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=["#f8f9fa", "#1e222b"], corner_radius=12)
        
        self.title_label = ctk.CTkLabel(
            self, text="Panel de Control", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(15, 10), padx=15, anchor="w")
        
        # CAMPO DE LOGIN (Limpio para integración)
        self.user_label = ctk.CTkLabel(self, text="👤 Usuario / Operador:", font=ctk.CTkFont(size=11, weight="bold"))
        self.user_label.pack(padx=15, anchor="w")
        self.user_entry = ctk.CTkEntry(self, height=30, placeholder_text="Escriba usuario (Ej: Wilmary_Control)...")
        self.user_entry.pack(fill="x", pady=(2, 10), padx=15)
        
        self.separator = ctk.CTkFrame(self, height=2, fg_color="gray")
        self.separator.pack(fill="x", padx=15, pady=5)
        
        # ENTRADAS DE DATOS REALES
        self.student_name_entry = ctk.CTkEntry(self, placeholder_text="Nombre del Estudiante", height=38)
        self.student_name_entry.pack(fill="x", pady=6, padx=15)
        
        self.student_entry = ctk.CTkEntry(self, placeholder_text="Cédula (CI)", height=38)
        self.student_entry.pack(fill="x", pady=6, padx=15)
        
        self.subject_menu = ctk.CTkOptionMenu(self, values=["Matemáticas", "Física", "Programación", "Química"], height=38)
        self.subject_menu.pack(fill="x", pady=6, padx=15)
        
        self.grade_entry = ctk.CTkEntry(self, placeholder_text="Nota Final", height=38)
        self.grade_entry.pack(fill="x", pady=6, padx=15)
        
        # ACCIONES
        self.submit_btn = ctk.CTkButton(
            self, text="➕ Registrar Calificación", 
            fg_color="#2ecc71", hover_color="#27ae60",
            height=38, font=ctk.CTkFont(weight="bold"),
            command=self._on_submit
        )
        self.submit_btn.pack(fill="x", pady=(12, 5), padx=15)

        self.update_btn = ctk.CTkButton(
            self, text="🔧 Actualizar Registro", 
            fg_color="#e67e22", hover_color="#d35400",
            height=38, font=ctk.CTkFont(weight="bold"),
            command=self._on_update
        )
        self.update_btn.pack(fill="x", pady=(5, 15), padx=15)

    def _reset_borders(self):
        self.student_name_entry.configure(border_color=["#979da2", "#565b5e"])
        self.student_entry.configure(border_color=["#979da2", "#565b5e"])
        self.grade_entry.configure(border_color=["#979da2", "#565b5e"])

    def _on_submit(self):
        self._reset_borders()
        
        usuario_actual = self.user_entry.get().strip() or "Anonimo_Log"
        nombre = self.student_name_entry.get().strip()
        cedula = self.student_entry.get().strip()
        grade = self.grade_entry.get().strip()  
        subject = self.subject_menu.get()
        
        # Escudo contra campos vacíos
        if not nombre or not cedula or not grade:
            if not nombre: self.student_name_entry.configure(border_color="#e74c3c")
            if not cedula: self.student_entry.configure(border_color="#e74c3c")
            if not grade: self.grade_entry.configure(border_color="#e74c3c")
            return
        
        # Validar consistencia numérica
        es_valida, _ = validar_nota(grade)
        if not es_valida:
            self.grade_entry.configure(border_color="#e74c3c")
            return 
        
        fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        identificador_completo = f"{nombre} [{cedula}]"
        
        # Inyección inmediata en la memoria compartida
        MEMORIA_AUDITORIA.append((fecha_ahora, usuario_actual, identificador_completo, subject, grade))
        
        try:
            registrar_auditoria(
                usuario=usuario_actual,  
                estudiante=identificador_completo,
                materia=subject,
                nota_nueva_str=grade,
                nota_anterior=0
            )
        except Exception as e:
            print(f"⚠️ Alerta Base de Datos: {e}")
        
        # Forzar actualización total de las pestañas
        self.winfo_toplevel().refresh_all_views()
            
        self.student_name_entry.delete(0, 'end')
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')

    def _on_update(self):
        usuario_actual = self.user_entry.get().strip() or "Anonimo_Log"
        nombre = self.student_name_entry.get().strip()
        cedula = self.student_entry.get().strip()
        grade = self.grade_entry.get().strip()  
        subject = self.subject_menu.get()
        
        if not cedula or not grade:
            if not cedula: self.student_entry.configure(border_color="#e74c3c")
            if not grade: self.grade_entry.configure(border_color="#e74c3c")
            return
        
        identificador_completo = f"{nombre} [{cedula}]" if nombre else cedula
        
        # Modificación directa en memoria viva
        modificado_en_memoria = False
        for i, r in enumerate(MEMORIA_AUDITORIA):
            if f"[{cedula}]" in r[2] or r[2] == cedula:
                fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Mantener el nombre anterior si no se especificó uno nuevo
                nombre_final = identificador_completo if nombre else r[2]
                MEMORIA_AUDITORIA[i] = (fecha_ahora, usuario_actual, nombre_final, subject, grade)
                modificado_en_memoria = True
        
        # Si no existía en memoria por sesión, lo agregamos como un cambio directo
        if not modificado_en_memoria:
            fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            MEMORIA_AUDITORIA.append((fecha_ahora, usuario_actual, identificador_completo, subject, grade))

        try:
            modificar_auditoria(
                usuario=usuario_actual,
                estudiante=identificador_completo,
                materia=subject,
                nota_nueva_str=grade
            )
        except Exception:
            pass
            
        self.winfo_toplevel().refresh_all_views()
            
        self.student_name_entry.delete(0, 'end')
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')


class AuditLogsTable(ctk.CTkScrollableFrame):
    """MÓDULO: Historial sin Hashes y con desglose real de nombres y cédulas."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=2)  # Fecha/Hora
        self.grid_columnconfigure(1, weight=3)  # Nombre Estudiante
        self.grid_columnconfigure(2, weight=2)  # CI
        self.grid_columnconfigure(3, weight=2)  # Asignatura
        self.grid_columnconfigure(4, weight=1)  # Nota
        
        self.current_row = 1
        self.filas = []  
        self.construir_cabeceras()

    def construir_cabeceras(self):
        headers = ["Fecha / Hora", "Nombre del Estudiante", "CI (Cédula)", "Asignatura", "Nota"]
        for col, text in enumerate(headers):
            lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db", anchor="w")
            lbl.grid(row=0, column=col, padx=12, pady=8, sticky="w")

    def limpiar_tabla(self):
        for fila in self.filas:
            for widget in fila:
                widget.destroy()
        self.filas.clear()
        self.current_row = 1

    def add_log_entry(self, timestamp: str, name: str, ci: str, subject: str, grade: str):
        fila_widgets = []
        data = [timestamp, name, ci, subject, grade]
        
        for col_idx, text in enumerate(data):
            color = "#2ecc71" if col_idx == 4 and float(text or 0) >= 10 else ["#2c3e50", "#ffffff"]
            lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12), text_color=color, anchor="w")
            lbl.grid(row=self.current_row, column=col_idx, padx=12, pady=6, sticky="w")
            fila_widgets.append(lbl)
            
        self.filas.append(fila_widgets)
        self.current_row += 1
    
    def cargar_registros_desde_bd(self):
        self.limpiar_tabla()
        registros_totales = []
        
        # Cargar de la BD de Juan si responde
        try:
            db_regs = obtener_todos_los_registros()
            if db_regs:
                for r in db_regs:
                    if len(r) >= 5:
                        registros_totales.append((r[0], r[1], r[2], r[3], r[4]))
        except Exception:
            pass
            
        # Unificar con memoria en tiempo real asegurando no duplicar marcas exactas
        for mem_r in MEMORIA_AUDITORIA:
            if mem_r not in registros_totales:
                registros_totales.append(mem_r)
                    
        if not registros_totales:
            return
            
        for r in registros_totales:
            fecha, _, estudiante_raw, materia, nota = r[0], r[1], r[2], r[3], r[4]
            
            nombre_estudiante = estudiante_raw
            ci_estudiante = "N/A"
            
            if "[" in estudiante_raw and "]" in estudiante_raw:
                try:
                    parts = estudiante_raw.split(" [")
                    nombre_estudiante = parts[0]
                    ci_estudiante = parts[1].replace("]", "")
                except Exception:
                    pass
            
            nota_ok = str(int(nota) if hasattr(nota, 'is_integer') and nota.is_integer() else nota)
            self.add_log_entry(fecha, nombre_estudiante, ci_estudiante, materia, nota_ok)


class StudentInfoModule(ctk.CTkFrame):
    """MÓDULO: Fichas de Alumnos 100% dinámicas (Sin ejemplos estáticos)."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        
        self.proposal_banner = ctk.CTkLabel(
            self, text="📌 EXPEDIENTES VIVOS: Listado generado a partir de las cargas del Panel de Control.",
            font=ctk.CTkFont(size=11, slant="italic"), text_color="#2ecc71", bg_color=["#ebf9eb", "#142414"],
            corner_radius=6, height=30
        )
        self.proposal_banner.pack(fill="x", pady=(0, 15))
        
        self.scroll_info = ctk.CTkScrollableFrame(self, label_text="Fichas Técnicas del Alumnado")
        self.scroll_info.pack(fill="both", expand=True)
        self.scroll_info.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.widgets_dinamicos = []
        self.actualizar_alumnos_dinamicos()

    def actualizar_alumnos_dinamicos(self):
        for w in self.widgets_dinamicos:
            w.destroy()
        self.widgets_dinamicos.clear()
        
        headers = ["Nombre del Estudiante", "Cédula (CI)", "Última Materia Evaluada", "Estado de Carga"]
        for idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_info, text=h, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
            lbl.grid(row=0, column=idx, padx=10, pady=5)
            self.widgets_dinamicos.append(lbl)
            
        alumnos_procesados = {}
        
        # Mapear lo que el usuario ha ingresado activamente
        for r in MEMORIA_AUDITORIA:
            estudiante_raw = r[2]
            materia = r[3]
            if "[" in estudiante_raw:
                try:
                    parts = estudiante_raw.split(" [")
                    nom = parts[0]
                    ced = parts[1].replace("]", "")
                    alumnos_procesados[ced] = (nom, materia, "Sincronizado")
                except Exception:
                    alumnos_procesados[estudiante_raw] = (estudiante_raw, materia, "Sincronizado")
            else:
                alumnos_procesados[estudiante_raw] = (estudiante_raw, materia, "Sincronizado")

        if not alumnos_procesados:
            lbl_empty = ctk.CTkLabel(
                self.scroll_info, 
                text="No hay alumnos registrados en este lapso. Use el Panel de Control para agregar uno.",
                font=ctk.CTkFont(size=12, slant="italic"), text_color="gray"
            )
            lbl_empty.grid(row=1, column=0, columnspan=4, pady=30)
            self.widgets_dinamicos.append(lbl_empty)
            return

        for row_idx, (cedula, datos) in enumerate(alumnos_procesados.items(), start=1):
            row_data = [datos[0], cedula, datos[1], datos[2]]
            for col_idx, text in enumerate(row_data):
                lbl = ctk.CTkLabel(self.scroll_info, text=text, font=ctk.CTkFont(size=12))
                lbl.grid(row=row_idx, column=col_idx, padx=10, pady=8)
                self.widgets_dinamicos.append(lbl)


class SingleStudentSearchModule(ctk.CTkFrame):
    """MÓDULO: Búsqueda Individual conectada a la memoria activa."""
    def __init__(self, master, action_panel_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.action_panel = action_panel_ref 
        
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", pady=(0, 15))
        
        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Buscar cédula específica...", width=250)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        btn_search = ctk.CTkButton(search_bar, text="🔍 Buscar", width=90, command=self._buscar_estudiante)
        btn_search.pack(side="left")
        
        self.result_box = ctk.CTkFrame(self, fg_color=["#ffffff", "#24292e"], corner_radius=8)
        self.result_box.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.info_label = ctk.CTkLabel(
            self.result_box, 
            text="Introduce una cédula arriba para desplegar historial individual e interactuar.",
            font=ctk.CTkFont(size=12, slant="italic"), text_color="gray"
        )
        self.info_label.pack(expand=True)

    def _buscar_estudiante(self):
        cedula_target = self.search_entry.get().strip()
        if not cedula_target:
            return
            
        for w in self.result_box.winfo_children():
            w.destroy()
            
        coincidencias = [r for r in MEMORIA_AUDITORIA if len(r) >= 3 and cedula_target in r[2]]
        
        if not coincidencias:
            lbl = ctk.CTkLabel(self.result_box, text="❌ No se encontraron notas cargadas para esa cédula.", text_color="#e74c3c")
            lbl.pack(pady=20)
            return
            
        header_lbl = ctk.CTkLabel(self.result_box, text=f"Historial Encontrado - CI: {cedula_target}", font=ctk.CTkFont(weight="bold", size=14))
        header_lbl.pack(pady=10, padx=15, anchor="w")
        
        for r in coincidencias:
            estudiante_raw = r[2]
            materia = r[3]
            nota = r[4]
            
            nombre_estudiante = estudiante_raw.split(" [")[0] if "[" in estudiante_raw else estudiante_raw
            
            row_frame = ctk.CTkFrame(self.result_box, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=4)
            
            lbl_materia = ctk.CTkLabel(row_frame, text=f"• {materia}:", font=ctk.CTkFont(size=12))
            lbl_materia.pack(side="left", padx=5)
            
            lbl_nota = ctk.CTkLabel(row_frame, text=str(nota), font=ctk.CTkFont(weight="bold", size=12), text_color="#3498db")
            lbl_nota.pack(side="left", padx=5)
            
            btn_edit = ctk.CTkButton(
                row_frame, text="✏️ Editar", width=60, height=22,
                fg_color="#34495e", hover_color="#e67e22",
                command=lambda m=materia, c=cedula_target, n=nota, nom=nombre_estudiante: self._cargar_en_formulario(c, nom, m, n)
            )
            btn_edit.pack(side="right", padx=10)

    def _cargar_en_formulario(self, cedula, nombre, materia, nota):
        self.action_panel.student_name_entry.delete(0, 'end')
        self.action_panel.student_name_entry.insert(0, nombre)
        self.action_panel.student_entry.delete(0, 'end')
        self.action_panel.student_entry.insert(0, cedula)
        self.action_panel.subject_menu.set(materia)
        self.action_panel.grade_entry.delete(0, 'end')
        self.action_panel.grade_entry.insert(0, str(nota))


class TeacherDashboard(ctk.CTkFrame):
    """Contenedor General de la Vista del Profesor."""
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
        
        self.tab_control.add("Notas Generales")
        self.tab_control.add("Información Alumnos")
        self.tab_control.add("Búsqueda Individual")
        
        self.logs_tab = AuditLogsTable(self.tab_control.tab("Notas Generales"))
        self.logs_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.info_tab = StudentInfoModule(self.tab_control.tab("Información Alumnos"))
        self.info_tab.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.search_tab = SingleStudentSearchModule(self.tab_control.tab("Búsqueda Individual"), action_panel_ref=self.action_panel)
        self.search_tab.pack(fill="both", expand=True, padx=5, pady=5)


class AuditGradesApp(ctk.CTk):
    """Ventana raíz del sistema."""
    def __init__(self):
        super().__init__()
        
        self.title("SISTEMA DE GESTIÓN ACADÉMICA E INMUTABILIDAD DE NOTAS")
        self.geometry("1200x680") 
        self.minsize(1000, 580)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.main_dashboard = TeacherDashboard(self)
        self.main_dashboard.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.after(300, self.refresh_all_views)
    
    def refresh_all_views(self):
        """Disparador maestro de sincronización de vistas."""
        try:
            self.main_dashboard.logs_tab.cargar_registros_desde_bd()
            self.main_dashboard.info_tab.actualizar_alumnos_dinamicos()
        except Exception as e:
            print(f"🔄 Sincronizando vistas dinámicas en memoria: {e}")


if __name__ == "__main__":
    app = AuditGradesApp() 
    app.mainloop()