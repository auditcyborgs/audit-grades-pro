import logging
import os  # <-- Lo movemos aquí arriba con los demás imports

# Configuramos el log para que guarde en 'auditoria_notas.log'
logging.basicConfig(
    filename='auditoria_notas.log',
    level=logging.INFO,
    format='%(asctime)s - [AUDITORIA] - %(message)s',
    encoding='utf-8'
)

def registrar_auditoria(usuario: str, estudiante: str, materia: str, nota_nueva: float, nota_anterior: float = 0.0) -> bool:
    """
    Registra los cambios e ingresos de notas en el archivo log persistente.
    """
    try:
        # Mensaje estructurado con toda la información
        mensaje = f"Profesor: {usuario} | Estudiante: {estudiante} | Materia: {materia} | Nota: {nota_anterior} -> {nota_nueva}"
        
        # Guardamos en el archivo de texto log
        logging.info(mensaje)
        
        # Feedback en la consola
        print(f"✅ [AUDITORIA EXITOSA]: {mensaje}")
        return True
    
    except Exception as e:
        print(f"❌ [ERROR DE AUDITORIA]: {e}")
        return False


def obtener_historial_auditoria():
    """Lee el archivo log y devuelve una lista con los registros reales."""
    historial = []
    if os.path.exists('auditoria_notas.log'):
        with open('auditoria_notas.log', 'r', encoding='utf-8') as archivo:
            for linea in archivo:
                # Filtramos para asegurarnos de que sea una línea de auditoría
                if "[AUDITORIA]" in linea:
                    # Separamos la fecha del mensaje
                    partes = linea.split(" - [AUDITORIA] - ")
                    fecha_hora = partes[0]
                    detalles = partes[1].strip()
                    historial.append((fecha_hora, detalles))
    return historial
