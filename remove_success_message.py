# Ruta al archivo de vistas
file_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el contenido actual del archivo
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Buscar y eliminar la línea del mensaje de éxito
new_lines = []
for line in lines:
    if 'messages.success(request,' in line and 'creado exitosamente' in line:
        continue  # Saltar esta línea
    new_lines.append(line)

# Escribir el contenido actualizado
with open(file_path, 'w', encoding='utf-8') as file:
    file.writelines(new_lines)

print("Mensaje de éxito eliminado correctamente.")
