file_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Encontrar la línea donde comienza la función crear_expediente
start_line = -1
for i, line in enumerate(lines):
    if 'def crear_expediente' in line:
        start_line = i
        break

if start_line != -1:
    # Encontrar la línea donde se define el contexto
    context_start = -1
    for i in range(start_line, len(lines)):
        if 'context = {' in lines[i]:
            context_start = i
            break
    
    if context_start != -1:
        # Buscar la línea donde termina el diccionario de contexto
        context_end = -1
        for i in range(context_start, len(lines)):
            if '}' in lines[i] and i > context_start + 5:  # Asumiendo que el diccionario tiene al menos 5 líneas
                context_end = i
                break
        
        # Verificar si ya existe la variable mostrar_fuente_financiamiento
        fuente_line = -1
        for i in range(context_start - 5, context_start):
            if 'mostrar_fuente_financiamiento' in lines[i]:
                fuente_line = i
                break
        
        # Si no existe la línea, agregarla
        if fuente_line == -1:
            # Insertar la línea después de la definición de departamentos
            for i in range(context_start - 10, context_start):
                if 'departamentos = ' in lines[i]:
                    lines.insert(i + 1, '    \n')
                    lines.insert(i + 2, '    # Determinar si se debe mostrar el campo de fuente de financiamiento\n')
                    lines.insert(i + 3, '    mostrar_fuente_financiamiento = tipo_id in [\'adjudicacion_directa\', \'compra_directa\', \'concurso_invitacion\']\n')
                    break
        
        # Asegurarse de que el contexto tenga la variable mostrar_fuente_financiamiento
        context_found = False
        for i in range(context_start, context_end + 1):
            if 'mostrar_fuente_financiamiento\'' in lines[i]:
                context_found = True
                break
        
        if not context_found:
            # Insertar la variable en el contexto
            for i in range(context_start, context_end + 1):
                if 'departamentos\'' in lines[i]:
                    lines.insert(i + 1, '        \'mostrar_fuente_financiamiento\': mostrar_fuente_financiamiento,\n')
                    break
        
        # Escribir el archivo actualizado
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        print("Archivo corregido correctamente.")
    else:
        print("No se pudo encontrar el contexto en la función crear_expediente.")
else:
    print("No se pudo encontrar la función crear_expediente en el archivo.")
