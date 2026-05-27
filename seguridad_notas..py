def validar_datos(nota_ingresada: str) -> str:
    """
    Valida que la nota ingresada sea un número real entre 0 y 20.
    Evita que el programa se detenga si se ingresan letras o caracteres extraños.
    """
    try:
        # Intentamos convertir la entrada a un número decimal
        nota = float(nota_ingresada)
        
        # Validación de rango lógico para notas (0-20)
        if 0 <= nota <= 20:
            return f"✅ Nota válida: {nota}"
        else:
            return f"❌ Error: La nota {nota} está fuera del rango permitido (0-20)"
            
    except ValueError:
        # Esto ocurre si el usuario escribe letras en lugar de números
        return "❌ Error: Valor inválido. Por favor, ingresa solo números (ejemplo: 15.5)"
    except Exception as e:
        # Esto captura cualquier otro error inesperado
        return f"❌ Error crítico: {str(e)}"

# Prueba de robustez
if __name__ == "__main__":
    print(validar_datos("15.5")) # Debería pasar
    print(validar_datos("25"))   # Debería dar error de rango
    print(validar_datos("hola")) # Debería dar error de tipo