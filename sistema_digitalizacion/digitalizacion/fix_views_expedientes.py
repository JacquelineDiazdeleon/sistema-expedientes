import re

def fix_subir_documento_temporal():
    # Ruta al archivo
    file_path = 'views_expedientes.py'
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Definir el patrón para encontrar la función subir_documento_temporal
    pattern = r'@login_required\s+def subir_documento_temporal\(request, expediente_id\):\s+'
    
    # Nueva implementación de la función
    new_function = """@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para mantener compatibilidad con el frontend.
    Obtiene la etapa del área actual y redirige a la vista subir_documento.
    """
    if request.method == 'POST':
        try:
            # Obtener el área actual del formulario
            area_id = request.POST.get('area_id')
            if not area_id:
                return JsonResponse({'error': 'No se especificó el área'}, status=400)
                
            # Obtener el área para determinar la etapa
            try:
                area = AreaTipoExpediente.objects.get(id=area_id)
                etapa = area.etapa.slug if area.etapa else 'temporal'
            except AreaTipoExpediente.DoesNotExist:
                etapa = 'temporal'
                
            # Llamar a la vista subir_documento con la etapa
            return subir_documento(request, expediente_id, etapa)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error al procesar la solicitud: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
"""
    
    # Reemplazar la función
    new_content = re.sub(pattern, new_function, content, flags=re.MULTILINE | re.DOTALL)
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("¡Función subir_documento_temporal actualizada exitosamente!")

if __name__ == "__main__":
    fix_subir_documento_temporal()
