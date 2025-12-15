import re

# Ruta al archivo
file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py'

# Leer el contenido del archivo
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Reemplazar la línea problemática
content = content.replace(
    "'tamaño_archivo': documento.tamaño_archivo  # Tamaño en bytes",
    "'tamano_archivo': documento.tamano_archivo if hasattr(documento, 'tamano_archivo') else 0  # Tamaño en bytes"
)

# Escribir el contenido de vuelta al archivo
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)

print('Archivo actualizado correctamente')
