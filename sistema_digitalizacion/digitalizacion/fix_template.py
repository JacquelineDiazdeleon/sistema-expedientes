def fix_template():
    # Ruta al archivo de plantilla
    template_path = 'templates/digitalizacion/expedientes/detalle_expediente.html'
    
    # Leer el contenido del archivo
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Definir el patrón a buscar y el reemplazo
    import re
    pattern = r'(<div class="area-item" data-area-id="\{\{ area\.id \}\}")(\s+onclick="cargarDocumentosArea\('\{\{ area\.id \}\}', '\{\{ area\.nombre \}\}'\)">)'
    replacement = r'\1 data-etapa="{{ area.etapa.slug|default:\'temporal\' }}"\2'
    
    # Realizar el reemplazo
    new_content = re.sub(pattern, replacement, content)
    
    # Escribir el contenido actualizado
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("¡Plantilla actualizada exitosamente! Se ha agregado el atributo data-etapa a los elementos de área.")

if __name__ == "__main__":
    fix_template()
