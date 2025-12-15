def update_redirect_url():
    file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templates\digitalizacion\expedientes\detalle_expediente.html'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace the URL with the correct namespaced version
    new_content = content.replace(
        'window.location.href = \'{% url "lista_expedientes" %}\'',
        'window.location.href = \'{% url "expedientes:lista" %}\''
    )
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)

if __name__ == "__main__":
    update_redirect_url()
