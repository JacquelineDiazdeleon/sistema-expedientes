import re

# 1. Actualizar las URLs en urls_expedientes.py
urls_file = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\urls_expedientes.py'

with open(urls_file, 'r', encoding='utf-8') as f:
    urls_content = f.read()

# Agregar la nueva ruta temporal
new_route = """
    # Ruta temporal para compatibilidad con el frontend existente
    path('<int:expediente_id>/subir-documento/', 
         views_expedientes.subir_documento_temporal, name='subir_documento_temporal'),
    
    # Rutas con etapa
    path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/', 
         views_expedientes.subir_documento, name='subir_documento'),
"""

# Insertar después de la primera coincidencia de 'subir-documento'
urls_content = re.sub(
    r"(path\('<int:expediente_id>/etapa/<str:etapa>/subir-documento/.*?\),\s*)",
    new_route,
    urls_content,
    count=1
)

with open(urls_file, 'w', encoding='utf-8') as f:
    f.write(urls_content)

# 2. Agregar la nueva vista a views_expedientes.py
views_file = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\views_expedientes.py'

with open(views_file, 'a', encoding='utf-8') as f:
    f.write("""

@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa del área desde el formulario y redirige a la vista principal.
    """
    try:
        if request.method == 'POST':
            # Obtener el área del formulario
            area_id = request.POST.get('area_id')
            if not area_id:
                return JsonResponse({'success': False, 'error': 'No se especificó el área'}, status=400)
                
            # Obtener el área para determinar la etapa
            try:
                area = AreaTipoExpediente.objects.get(id=area_id)
                etapa = area.etapa  # Asumiendo que el modelo AreaTipoExpediente tiene un campo 'etapa'
                
                # Llamar a la vista principal de subida de documentos
                return subir_documento(request, expediente_id, etapa)
                
            except AreaTipoExpediente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Área no encontrada'}, status=404)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error en subir_documento_temporal: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
""")

print("Los cambios se han aplicado correctamente. Por favor, reinicia el servidor para que los cambios surtan efecto.")
print("IMPORTANTE: Esta es una solución temporal. Asegúrate de actualizar el frontend para usar la URL con la etapa lo antes posible.")
