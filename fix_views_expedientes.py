# Ruta al archivo de vistas
file_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el contenido actual del archivo
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Encontrar la función crear_expediente
start_line = -1
for i, line in enumerate(lines):
    if 'def crear_expediente' in line:
        start_line = i
        break

if start_line != -1:
    # Encontrar el final de la función (buscando el return render)
    end_line = -1
    for i in range(start_line, len(lines)):
        if 'return render(' in lines[i]:
            end_line = i
            break
    
    if end_line != -1:
        # Buscar la línea donde se crea el contexto
        context_start = -1
        for i in range(start_line, end_line):
            if 'context = {' in lines[i]:
                context_start = i
                break
        
        if context_start != -1:
            # Encontrar la línea de cierre del diccionario de contexto
            context_end = context_start
            for i in range(context_start, len(lines)):
                if '}' in lines[i] and i > context_start + 5:  # Asumiendo que el diccionario tiene al menos 5 líneas
                    context_end = i
                    break
            
            # Reconstruir el contexto con la variable mostrar_fuente_financiamiento
            new_context = """    # Determinar si se debe mostrar el campo de fuente de financiamiento
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
            new_lines = lines[:context_start] + new_context.splitlines(keepends=True) + lines[context_end+1:]
            
            # Escribir el archivo actualizado
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(new_lines)
            
            print("Contexto actualizado correctamente con el campo de fuente de financiamiento.")
        else:
            print("No se pudo encontrar el contexto en la función crear_expediente.")
    else:
        print("No se pudo encontrar el final de la función crear_expediente.")
else:
    print("No se pudo encontrar la función crear_expediente en el archivo.")
