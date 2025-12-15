file_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\views_expedientes.py"

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Encontrar la línea donde comienza el bloque que necesitamos modificar
start_line = -1
for i, line in enumerate(lines):
    if '# Obtener todos los departamentos activos' in line:
        start_line = i
        break

if start_line != -1:
    # Insertar el try antes de la línea de departamentos
    lines.insert(start_line, '    try:\n')
    
    # Encontrar la línea del return para insertar el except después
    return_line = -1
    for i in range(start_line, len(lines)):
        if 'return render' in lines[i]:
            return_line = i
            break
    
    if return_line != -1:
        # Insertar el bloque except después del return
        lines.insert(return_line + 1, '    except Exception as e:\n')
        lines.insert(return_line + 2, '        logger.error(f\'Error en crear_expediente: {str(e)}\')\n')
        lines.insert(return_line + 3, '        messages.error(request, \'Ocurrió un error al cargar el formulario de creación de expediente.\')\n')
        lines.insert(return_line + 4, '        return redirect(\'expedientes:seleccionar_tipo\')\n')
        
        # Asegurar que la indentación sea consistente
        for i in range(start_line + 1, return_line + 1):
            if lines[i].strip():
                lines[i] = '    ' + lines[i].lstrip()
        
        # Escribir el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        print("Archivo corregido exitosamente.")
    else:
        print("No se pudo encontrar la línea de retorno en la función.")
else:
    print("No se pudo encontrar el bloque de código a modificar.")
