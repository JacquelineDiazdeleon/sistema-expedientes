# Script para corregir el archivo views_expedientes.py

# Ruta al archivo
file_path = r"C:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el contenido actual
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Encontrar la posición de la segunda definición de la función
first_occurrence = content.find('def editar_numero_sima(')
if first_occurrence != -1:
    # Encontrar el inicio de la siguiente función después de la primera ocurrencia
    next_function = content.find('def ', first_occurrence + 1)
    if next_function != -1:
        # Extraer la primera función
        first_function = content[first_occurrence:next_function]
        # Eliminar la primera ocurrencia de la función
        new_content = content.replace(first_function, '', 1)
        # Eliminar los caracteres de escape restantes
        new_content = new_content.replace('\n\n', '\n')
        
        # Escribir el contenido corregido
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print("Archivo corregido exitosamente.")
    else:
        print("No se pudo encontrar la siguiente función después de la primera ocurrencia.")
else:
    print("No se encontró la función 'editar_numero_sima' en el archivo.")
