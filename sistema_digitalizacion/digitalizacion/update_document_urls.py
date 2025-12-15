def update_document_urls():
    # Ruta al archivo de URLs
    urls_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\urls_expedientes.py'
    
    # Leer el contenido actual
    with open(urls_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya se han actualizado las URLs
    if 'document_views' in content:
        print("Las URLs ya han sido actualizadas previamente.")
        return
    
    # Actualizar las importaciones
    import_line = 'from . import views_expedientes, views_expedientes_updated, fixed_views_expedientes'
    new_import_line = 'from . import views_expedientes, views_expedientes_updated, fixed_views_expedientes, document_views'
    
    content = content.replace(import_line, new_import_line)
    
    # Actualizar las rutas de subida de documentos
    old_route = """    # Gestión de etapas    # Ruta temporal para compatibilidad con el frontend existente
    path('<int:expediente_id>/subir-documento/', 
    path('<int:expediente_id>/subir-documento/, 
         fixed_views_expedientes.subir_documento_temporal, name='subir_documento_temporal'),

    # Rutas con etapa

    path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/, 
         fixed_views_expedientes.subir_documento, name='subir_documento'),
         views_expedientes.subir_documento, name='subir_documento'),"""
    
    new_route = """    # Gestión de etapas - Rutas para subida de documentos
    # Ruta temporal para compatibilidad con el frontend existente
    path('<int:expediente_id>/subir-documento/', 
         document_views.subir_documento_temporal, 
         name='subir_documento_temporal'),

    # Ruta mejorada con etapa en la URL
    path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/', 
         document_views.subir_documento, 
         name='subir_documento'),"""
    
    content = content.replace(old_route, new_route)
    
    # Escribir el contenido actualizado
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("URLs de documentos actualizadas exitosamente.")

if __name__ == "__main__":
    update_document_urls()
