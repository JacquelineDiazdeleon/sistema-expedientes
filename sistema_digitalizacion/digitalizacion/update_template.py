def update_template():
    # Ruta al archivo de plantilla
    template_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\templates\digitalizacion\expedientes\detalle_expediente.html'
    
    # Leer el contenido del archivo
    with open(template_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Buscar y modificar la línea que contiene el div con la clase 'area-item'
    modified = False
    for i, line in enumerate(lines):
        if 'class="area-item"' in line and 'data-area-id' in line and 'data-etapa' not in line:
            # Insertar el atributo data-etapa después de data-area-id
            if 'onclick=' in line:
                parts = line.split('onclick=', 1)
                new_line = f"{parts[0].rstrip()} data-etapa=\"{{{{ area.etapa.slug|default:'temporal' }}}}" onclick={parts[1]}"
                lines[i] = new_line
                modified = True
    
    # Escribir el contenido actualizado si hubo cambios
    if modified:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("¡Plantilla actualizada exitosamente! Se ha agregado el atributo data-etapa a los elementos de área.")
    else:
        print("No se realizaron cambios en la plantilla. El atributo data-etapa ya existe o no se encontraron elementos para modificar.")

if __name__ == "__main__":
    update_template()
