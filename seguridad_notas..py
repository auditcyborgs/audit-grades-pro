import logging

def validar_datos(nota_ingresada: str) -> tuple[bool, str]:
    """
    Validación avanzada:
    1. Detecta vacíos.
    2. Convierte comas a puntos.
    3. Valida rango (0-20).
    4. Limita decimales a máximo 2.
    """
    # 1. Limpieza inicial
    if not nota_ingresada or not nota_ingresada.strip():
        return False, "Error: El campo no puede estar vacío."
    
    nota_str = nota_ingresada.replace(',', '.').strip()
    
    # 2. Intentar convertir a float
    try:
        nota = float(nota_str)
    except ValueError:
        return False, f"Error: '{nota_ingresada}' no es un valor numérico válido."
    
    # 3. Validación de rango
    if not (0 <= nota <= 20):
        return False, f"Error: {nota} está fuera de rango (0-20)."
    
    # 4. Control de precisión (Opcional: max 2 decimales)
    # Convertimos a string y contamos después del punto
    if "." in nota_str:
        decimales = nota_str.split(".")[1]
        if len(decimales) > 2:
            return False, "Error: La nota no puede tener más de 2 decimales."

    # 5. Si todo pasa, retornamos éxito
    return True, f"Nota validada correctamente: {nota:.2f}"

# --- MEJORA PARA DIANA Y SEBASTIÁN ---
# Esto ayuda a que el "escudo de excepciones" sea más inteligente
def registrar_intento(input_usuario: str, es_valido: bool):
    """
    Registra en los logs cualquier intento de ingreso de nota.
    Esto es puro nivel profesional.
    """
    estado = "EXITOSO" if es_valido else "FALLIDO"
    # Aquí puedes conectar con tu módulo de auditoría.py
    print(f"[LOG DE SISTEMA] Intento: {input_usuario} | Resultado: {estado}")

if __name__ == "__main__":
    pruebas = ["18.55", "18.555", "20", "-1", "ABC", "15,5"]
    
    for p in pruebas:
        valido, mensaje = validar_datos(p)
        registrar_intento(p, valido)
        print(f"Entrada: '{p}' -> {mensaje}")