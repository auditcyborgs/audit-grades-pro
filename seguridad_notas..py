def validar_datos(nota_ingresada):
    # Esto es el "Escudo": evita que el programa explote si alguien mete letras
    try:
        nota = float(nota_ingresada)
        if nota < 0 or nota > 20:
            return "Error: La nota debe estar entre 0 y 20"
        return f"Nota válida: {nota}"
    except ValueError:
        return "Error: Debes ingresar un número, no letras"

# Prueba tu parte
print(validar_datos("15"))   # Esto debe salir bien
print(validar_datos("hola")) # Esto debe salir error controlado