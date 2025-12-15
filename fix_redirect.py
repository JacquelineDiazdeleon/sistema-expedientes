def fix_redirect_url():
    file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templates\digitalizacion\expedientes\detalle_expediente.html'
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar la URL con la versión correcta
    new_content = content.replace(
        'window.location.href = \'{% url "lista_expedientes" %}\'',
        'window.location.href = \'{% url "expedientes:lista" %}\''
    )
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("URL de redirección actualizada correctamente.")

if __name__ == "__main__":
    fix_redirect_url()
