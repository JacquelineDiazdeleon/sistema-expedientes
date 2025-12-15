def update_redirect():
    file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templates\digitalizacion\expedientes\detalle_expediente.html'
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar la línea de éxito con la nueva lógica de redirección
    new_content = content.replace(
        "// Mostrar mensaje de éxito\n                showAlert('✅ Expediente guardado correctamente', 'success');",
        "// Mostrar mensaje de éxito y redirigir después de 1 segundo\n                showAlert('✅ Expediente guardado correctamente. Redirigiendo...', 'success');\n                \n                // Redirigir a la lista de expedientes después de 1 segundo\n                setTimeout(() => {\n                    window.location.href = '{% url \"lista_expedientes\" %}'\n                }, 1000);"
    )
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)

if __name__ == "__main__":
    update_redirect()
