def update_template():
    # Ruta al archivo de plantilla
    template_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\templates\digitalizacion\expedientes\detalle_expediente.html'
    
    # Leer el contenido del archivo
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Realizar el reemplazo de manera segura
    import re
    pattern = r'(<div class="area-item" data-area-id=\{\{ area\.id \}\})("\s+onclick=)'
    replacement = r'\1" data-etapa="{{ area.etapa.slug|default:\'temporal\' }}\2'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Escribir el contenido actualizado
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Plantilla actualizada exitosamente.")

if __name__ == "__main__":
    update_template()
