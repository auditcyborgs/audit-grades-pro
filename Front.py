import customtkinter as ctk
from datetime import datetime

from auditoria import registrar_auditoria, validar_nota, obtener_todos_los_registros

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")  

class ActionPanel(ctk.CTkFrame):
    """Componente de formulario para el registro y auditoría de notas."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        
        self.title_label = ctk.CTkLabel(
            self, text="Auditar Calificación", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(pady=(0, 20), anchor="w")
        
        self.student_entry = ctk.CTkEntry(
            self, placeholder_text="Cédula del Estudiante", height=40
        )
        self.student_entry.pack(fill="x", pady=10)
        
        self.subject_menu = ctk.CTkOptionMenu(
            self, values=["Matemáticas", "Física", "Programación", "Química"], height=40
        )
        self.subject_menu.pack(fill="x", pady=10)
        
        self.grade_entry = ctk.CTkEntry(
            self, placeholder_text="Nota Final (ej: 14)", height=40
        )
        self.grade_entry.pack(fill="x", pady=10)
        
        self.submit_btn = ctk.CTkButton(
            self, text="Firmar y Registrar", 
            fg_color="#2ecc71", hover_color="#27ae60",
            height=40, font=ctk.CTkFont(weight="bold"),
            command=self._on_submit
        )
        self.submit_btn.pack(fill="x", pady=20)

    def _on_submit(self):
        student = self.student_entry.get()
        grade = self.grade_entry.get()  
        subject = self.subject_menu.get()
        
        if not student:
            self.student_entry.configure(border_color="#e74c3c")
            return
        self.student_entry.configure(border_color=["#979da2", "#565b5e"])
        
        es_valida, mensaje_error = validar_nota(grade)
        if not es_valida:
            print(f"❌ [BLOQUEADO]: {mensaje_error}")
            self.grade_entry.configure(border_color="#e74c3c")
            return 
        
        self.grade_entry.configure(border_color=["#979da2", "#565b5e"])
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        mock_hash = "0x" + str(hex(hash(student + grade)))[2:10] + "...done"
        
        registrar_auditoria(
            usuario="Barbara_Admin",  
            estudiante=student,
            materia=subject,
            nota_nueva_str=grade,
            nota_anterior=0
        )
        
        self.master.master.dashboard.logs_table.cargar_registros_desde_bd()
        
        self.student_entry.delete(0, 'end')
        self.grade_entry.delete(0, 'end')


class AuditLogsTable(ctk.CTkScrollableFrame):
    """Componente de tabla optimizado y corregido para evitar solapamientos."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Distribución de columnas balanceada para que nada se pise
        self.grid_columnconfigure(0, weight=2)  # Espacio para Fecha
        self.grid_columnconfigure(1, weight=4)  # Espacio ancho para la Acción
        self.grid_columnconfigure(2, weight=2)  # Espacio para el Hash
        
        self.current_row = 1
        self.filas = []  
        
        headers = ["Fecha/Hora", "Acción Realizada", "Firma Digital (Hash)"]
        for col, text in enumerate(headers):
            padx_config = (20, 10) if col == 0 else 10
            lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray", anchor="w")
            lbl.grid(row=0, column=col, padx=padx_config, pady=5, sticky="w")

    def limpiar_tabla(self):
        """Limpia todas las filas de la tabla excepto los encabezados."""
        for fila in self.filas:
            for widget in fila:
                widget.destroy()
        self.filas.clear()
        self.current_row = 1

    def add_log_entry(self, timestamp: str, action: str, crypto_hash: str):
        """Inserta las filas de forma ordenada y alineada."""
        data = [timestamp, action, crypto_hash]
        fila_widgets = []
        
        for col_idx, text in enumerate(data):
            font_style = ctk.CTkFont(family="Courier", size=11) if col_idx == 2 else ctk.CTkFont(size=12)
            text_color = "#2ecc71" if col_idx == 2 else ["#000000", "#FFFFFF"]
            
            lbl = ctk.CTkLabel(self, text=text, font=font_style, text_color=text_color, anchor="w")
            
            padx_config = (20, 10) if col_idx == 0 else 10
            
            lbl.grid(row=self.current_row, column=col_idx, padx=padx_config, pady=8, sticky="w")
            fila_widgets.append(lbl)
        
        self.filas.append(fila_widgets)
        self.current_row += 1
    
    def cargar_registros_desde_bd(self):
        """Carga todos los registros existentes desde la base de datos."""
        self.limpiar_tabla()
        registros = obtener_todos_los_registros()
        
        if not registros:
            print("⚠️ No hay registros para mostrar")
            return
        
        for registro in registros:
            if len(registro) >= 5:
                fecha = registro[0]      # fecha_cambio
                usuario = registro[1]    # usuario
                estudiante = registro[2]  # cedula_estudiante
                materia = registro[3]    # materia
                nota = registro[4]       # nota_nueva
                hash_firma = registro[5] if len(registro) > 5 else "0x00000000...done"
                
                # Formatear la acción como en tu imagen
                accion = f"Registro Nota: {estudiante} -> {materia}: {int(nota) if nota.is_integer() else nota}"
                
                self.add_log_entry(fecha, accion, hash_firma)
            else:
                fecha = registro[0]
                usuario = registro[1]
                nota = registro[2]
                hash_firma = registro[3]
                accion = f"Registro Nota: {usuario} -> Nota: {int(nota) if nota.is_integer() else nota}"
                self.add_log_entry(fecha, accion, hash_firma)


class DashboardFrame(ctk.CTkFrame):
    """Contenedor principal del Dashboard."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=3) 
        self.grid_rowconfigure(0, weight=1)
        
        self.action_panel = ActionPanel(self)
        self.action_panel.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.logs_table = AuditLogsTable(self, label_text="Registros de Calificaciones")
        self.logs_table.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")


class AuditGradesApp(ctk.CTk):
    """Ventana principal de la aplicación AUDIT-GRADES PRO."""
    def __init__(self):
        super().__init__()
        
        self.title("AUDIT-GRADES PRO v1.0 - Sistema de Auditoría Inmutable")
        self.geometry("1100x600") 
        self.minsize(900, 500)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.dashboard = DashboardFrame(self)
        self.dashboard.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # Cargar los registros existentes al iniciar la aplicación
        self.after(500, self.cargar_registros_iniciales)
    
    def cargar_registros_iniciales(self):
        """Carga los registros existentes desde la base de datos."""
        print("🔄 Cargando registros desde la base de datos...")
        self.dashboard.logs_table.cargar_registros_desde_bd()


if __name__ == "__main__":
    app = AuditGradesApp() 
    app.mainloop()