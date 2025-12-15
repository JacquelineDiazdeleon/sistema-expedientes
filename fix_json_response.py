def fix_subir_documento_temporal():
    file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\views_expedientes.py'
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Definir la nueva implementación
    new_implementation = """
@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa del área desde el formulario y redirige a la vista principal.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
            
    try:
        # Obtener el área del formulario
        area_id = request.POST.get('area_id')
        if not area_id:
            return JsonResponse({'success': False, 'error': 'No se especificó el área'}, status=400)
            
        # Obtener el área para determinar la etapa
        try:
            area = AreaTipoExpediente.objects.get(id=area_id)
            
            # Verificar que el área tenga una etapa definida
            if not hasattr(area, 'etapa') or not area.etapa:
                return JsonResponse({
                    'success': False, 
                    'error': 'El área no tiene una etapa definida',
                    'area_id': area_id
                }, status=400)
            
            # Llamar a la vista principal de subida de documentos
            return subir_documento(request, expediente_id, area.etapa)
            
        except AreaTipoExpediente.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'No se encontró el área con ID {area_id}',
                'area_id': area_id
            }, status=404)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('Error en subir_documento_temporal')
        
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor al procesar la solicitud',
            'type': type(e).__name__,
            'message': str(e)
        }, status=500)
"""
    
    # Reemplazar la función existente
    import re
    pattern = r'@login_required\s+def subir_documento_temporal\([\s\S]*?\n\s+return JsonResponse\(\{\'success\': False, \'error\': str\(e\)\}, status=500\)\s+'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_implementation, content, flags=re.DOTALL)
        
        # Hacer una copia de seguridad
        import shutil
        shutil.copy2(file_path, file_path + '.bak')
        
        # Escribir el archivo actualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("La función subir_documento_temporal ha sido actualizada exitosamente.")
        print("Se ha creado una copia de seguridad en:", file_path + '.bak')
    else:
        print("No se pudo encontrar la función subir_documento_temporal para actualizar.")

if __name__ == "__main__":
    fix_subir_documento_temporal()
    print("Por favor, reinicia el servidor para que los cambios surtan efecto.")
