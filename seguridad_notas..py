def validar_datos(nota_ingresada: str) -> tuple[bool, str]:
    """
<<<<<<< HEAD
    Valida que la nota ingresada sea un número real entre 0 y 20.
    Evita que el programa se detenga si se ingresan letras o caracteres extraños
=======
    Valida que la nota sea un número entre 0 y 20.
    Retorna un par: (Es_valido, Mensaje)
>>>>>>> 976aa930d109f48555bd2fd0c9ded48d60a44375
    """
    try:
        # .strip() elimina espacios accidentales al inicio o final
        nota = float(nota_ingresada.strip())
        
        if 0 <= nota <= 20:
            return True, f"Nota válida: {nota}"
        else:
            return False, f"Error: La nota {nota} está fuera del rango (0-20)"
            
    except ValueError:
        return False, "Error: Entrada inválida. Por favor, ingresa solo números."
    except Exception as e:
        return False, f"Error crítico: {str(e)}"

# Prueba de robustez mejorada
if __name__ == "__main__":
    pruebas = ["15.5", "25", "hola", " 10 "] # Incluí un caso con espacios
    
    for p in pruebas:
        es_valido, mensaje = validar_datos(p)
        print(f"Entrada: '{p}' -> {mensaje}")