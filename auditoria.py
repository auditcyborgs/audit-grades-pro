import logging
import os

# ==========================================
# CONFIGURACIÓN DEL LOG (ARCHIVO DE TEXTO)
# ==========================================
logging.basicConfig(
    filename='auditoria_notas.log',
    level=logging.INFO,
    format='%(asctime)s - [AUDITORIA] - %(message)s',
    encoding='utf-8'
)

# ==========================================
# CAPA DE SEGURIDAD (VALIDACIONES)
# ==========================================
def validar_nota(nota_ingresada: str) -> tuple[bool, str]:
    """
    Valida que la nota ingresada cumpla estrictamente con las reglas:
    1. No puede estar vacía.
    2. No puede tener decimales (ni puntos ni comas).
    3. No puede contener letras ni símbolos.
    4. Debe estar en el rango entero de 0 a 20 (bloquea negativos).
    """
    # 1. Verificar si el campo está vacío
    if not nota_ingresada or not nota_ingresada.strip():
        return False, "Error: El campo de la nota no puede estar vacío."
    
    nota_str = nota_ingresada.strip()
    
    # 2. Bloquear decimales de forma explícita
    if "." in nota_str or "," in nota_str:
        return False, "Error: No se permiten números decimales. Ingrese un número entero."
    
    # 3. Intentar convertir a entero (Atrapa letras, símbolos y caracteres especiales)
    try:
        nota = int(nota_str)
    except ValueError:
        return False, f"Error: '{nota_ingresada}' contiene letras o símbolos no válidos."
    
    # 4. Validación de rango (Bloquea automáticamente los números negativos)
    if not (0 <= nota <= 20):
        return False, f"Error: La nota {nota} está fuera del rango permitido (0-20)."
    
    return True, "Nota válida"


# ==========================================
# CAPA DE PERSISTENCIA (GUARDAR Y LEER LOGS)
# ==========================================
def registrar_auditoria(usuario: str, estudiante: str, materia: str, nota_nueva_str: str, nota_anterior: int = 0) -> bool:
    """
    Aplica la doble capa de validación en el backend y, si todo es correcto,
    escribe de forma persistente el registro de auditoría en el archivo log.
    """
    # Doble verificación de seguridad antes de escribir el archivo
    es_valida, mensaje = validar_nota(nota_nueva_str)
    if not es_valida:
        print(f"❌ [FALLO DE AUDITORÍA - BLOQUEADO POR SEGURIDAD]: {mensaje}")
        return False

    try:
        nota_final = int(nota_nueva_str.strip())
        mensaje_log = f"Profesor: {usuario} | Estudiante: {student if 'student' in locals() else estudiante} | Materia: {materia} | Nota: {nota_anterior} -> {nota_final}"
        
        # Guardamos físicamente en el archivo de texto log
        logging.info(mensaje_log)
        print(f"✅ [AUDITORIA EXITOSA]: {mensaje_log}")
        return True
    
    except Exception as e:
        print(f"❌ [ERROR CRÍTICO DE AUDITORIA]: {e}")
        return False


def obtener_historial_auditoria():
    """
    Lee el archivo 'auditoria_notas.log' línea por línea, extrae los datos
    reales guardados y los devuelve en una lista para cargar la vista del Front.
    """
    historial = []
    if os.path.exists('auditoria_notas.log'):
        with open('auditoria_notas.log', 'r', encoding='utf-8') as archivo:
            for linea in archivo:
                # Nos aseguramos de procesar únicamente líneas con la etiqueta de auditoría
                if "[AUDITORIA]" in linea:
                    # Separamos la estampa de tiempo del contenido del mensaje
                    partes = linea.split(" - [AUDITORIA] - ")
                    fecha_hora = partes[0]
                    detalles = partes[1].strip()
                    historial.append((fecha_hora, detalles))
    return historial