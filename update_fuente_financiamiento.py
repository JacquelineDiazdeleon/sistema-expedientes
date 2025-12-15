# Ruta al archivo de vistas
file_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el contenido actual del archivo
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Encontrar la línea donde comienza el contexto
start_line = -1
for i, line in enumerate(lines):
    if 'context = {' in line:
        start_line = i
        break

if start_line != -1:
    # Encontrar la línea donde termina el diccionario de contexto
    end_line = start_line
    for i in range(start_line, len(lines)):
        if '}' in lines[i] and i > start_line + 5:  # Asumiendo que el diccionario tiene al menos 5 líneas
            end_line = i
            break
    
    # Construir el nuevo contexto
    new_context = """    # Determinar si se debe mostrar el campo de fuente de financiamiento
    # Mostrar para: adjudicacion_directa, compra_directa, concurso_invitacion
    mostrar_fuente_financiamiento = tipo_id in ['adjudicacion_directa', 'compra_directa', 'concurso_invitacion']
    
    context = {
        'form': form,
        'tipo': tipo_id,
        'tipo_nombre': tipo_nombre,
        'titulo': f'Nuevo Expediente - {tipo_nombre}',
        'departamentos': departamentos,
        'mostrar_fuente_financiamiento': mostrar_fuente_financiamiento,
        'subtipo': subtipo if ':' in tipo_id else None
    }
"""
    
    # Reemplazar las líneas del contexto
    new_lines = lines[:start_line] + new_context.splitlines(keepends=True) + lines[end_line+1:]
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)
    
    print("Contexto actualizado correctamente con el campo de fuente de financiamiento.")
else:
    print("No se pudo encontrar el contexto en el archivo.")

# Verificar si el campo ya está en la plantilla
template_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templates\digitalizacion\expedientes\crear_expediente.html"

with open(template_path, 'r', encoding='utf-8') as file:
    template_content = file.read()

# Verificar si el campo de fuente de financiamiento ya existe en la plantilla
if 'name="fuente_financiamiento"' not in template_content:
    print("El campo de fuente de financiamiento no está en la plantilla. Asegúrate de que esté presente.")
    print("El campo debe estar dentro de un bloque condicional como: {% if mostrar_fuente_financiamiento %}")
else:
    print("El campo de fuente de financiamiento ya está presente en la plantilla.")
