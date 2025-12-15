def update_urls_file():
    # Ruta al archivo de URLs
    urls_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\urls_expedientes.py'
    
    # Leer el contenido del archivo
    with open(urls_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Actualizar las importaciones
    for i, line in enumerate(lines):
        if 'from . import views_expedientes, views_expedientes_updated' in line:
            lines[i] = 'from . import views_expedientes, views_expedientes_updated, fixed_views_expedientes\n'
    # Actualizar las rutas
    in_urlpatterns = False
    for i, line in enumerate(lines):
        if 'urlpatterns' in line:
            in_urlpatterns = True
        
        if in_urlpatterns and 'subir_documento_temporal' in line:
            lines[i] = '    path(\'<int:expediente_id>/subir-documento/, \n         fixed_views_expedientes.subir_documento_temporal, name=\'subir_documento_temporal\'),\n'
        if in_urlpatterns and 'etapa/<str:etapa>/subir-documento' in line:
            lines[i] = '    path(\'<int:expediente_id>/etapa/<str:etapa>/subir-documento/, \n         fixed_views_expedientes.subir_documento, name=\'subir_documento\'),\n'
    # Escribir el contenido actualizado
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Archivo de URLs actualizado exitosamente.")

if __name__ == "__main__":
    update_urls_file()
