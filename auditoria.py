import logging
import os  # <-- Lo movemos aquí arriba con los demás imports

# Configuramos el log para que guarde un archivo de texto llamado 'auditoria_notas.log'
# Si el archivo no existe, lo crea automáticamente.
logging.basicConfig(
    filename='auditoria_notas.log',
    level=logging.INFO,
    format='%(asctime)s - [AUDITORIA] - %(message)s',
    encoding='utf-8'
)

def registrar_auditoria(usuario: str, nota_anterior: float, nota_nueva: float) -> bool:
    """
    Registra cambios de notas en un archivo de log persistente.
    Retorna True si el registro fue exitoso.
    """
    try:
        # Creamos el mensaje de forma estructurada
        mensaje = f"Usuario: {usuario} | Cambio: {nota_anterior} -> {nota_nueva}"
        
        # Guardamos en el archivo log
        logging.info(mensaje)
        
        # Feedback visual para la consola
        print(f"✅ [AUDITORIA EXITOSA]: {mensaje}")
        return True
    
    except Exception as e:
        print(f"❌ [ERROR CRÍTICO DE AUDITORIA]: {e}")
        return False

# Ejemplo de uso:
if __name__ == "__main__":
    registrar_auditoria("Barbara", 12.0, 18.5)