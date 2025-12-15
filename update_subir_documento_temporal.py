def get_updated_subir_documento_temporal():
    return """
@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa del área desde el formulario y redirige a la vista principal.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido',
            'allowed_methods': ['POST']
        }, status=405)
            
    try:
        # Obtener el área del formulario
        area_id = request.POST.get('area_id')
        if not area_id:
            return JsonResponse({
                'success': False, 
                'error': 'No se especificó el área',
                'field': 'area_id'
            }, status=400)
            
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
            response = subir_documento(request, expediente_id, area.etapa)
            
            # Si la respuesta es un JsonResponse, devolverla directamente
            if hasattr(response, 'content_type') and 'application/json' in response.content_type:
                return response
                
            # Si no es un JsonResponse, devolver un error
            return JsonResponse({
                'success': False,
                'error': 'La respuesta del servidor no es un JSON válido',
                'content_type': getattr(response, 'content_type', 'desconocido')
            }, status=500)
            
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

# Actualizar el archivo views_expedientes.py
import re

# Leer el archivo actual
with open('sistema_digitalizacion/digitalizacion_2/views_expedientes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la función existente
new_function = get_updated_subir_documento_temporal()
pattern = r'@login_required\s+def subir_documento_temporal\([\s\S]*?\n\s+return JsonResponse\(\{\'success\': False, \'error\': str\(e\)\}, status=500\)\s+'

if re.search(pattern, content):
    updated_content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    # Escribir el archivo actualizado
    with open('sistema_digitalizacion/digitalizacion_2/views_expedientes.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("La función subir_documento_temporal ha sido actualizada exitosamente.")
else:
    print("No se encontró la función subir_documento_temporal para actualizar.")
    print("Asegúrate de que el archivo y la función existen.")

print("Por favor, reinicia el servidor para que los cambios surtan efecto.")
