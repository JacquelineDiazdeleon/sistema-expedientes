# Código para arreglar el archivo views_expedientes.py

def update_views_expedientes():
    # Ruta al archivo original
    file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\views_expedientes.py'
    
    # Leer el contenido actual
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar la función subir_documento_temporal
    old_func = """@login_required
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
                # Llamar a la vista principal de subida de documentos con la etapa del área
                return subir_documento(request, expediente_id, area.etapa)
                
            except AreaTipoExpediente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Área no encontrada'}, status=404)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error en subir_documento_temporal: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
"""

    new_func = """@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa directamente del formulario.
    """
    try:
        if request.method == 'POST':
            # Obtener la etapa directamente del formulario
            etapa = request.POST.get('etapa')
            if not etapa:
                return JsonResponse({'success': False, 'error': 'No se especificó la etapa del documento'}, status=400)
                
            # Llamar a la vista principal de subida de documentos con la etapa
            return subir_documento(request, expediente_id, etapa)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error en subir_documento_temporal: {str(e)}')
        return JsonResponse({'success': False, 'error': 'Error al procesar la solicitud'}, status=500)

# Añadir la función subir_documento si no existe
subir_documento_func = """
@login_required
def subir_documento(request, expediente_id, etapa):
    """Vista para subir documentos a una etapa específica"""
    from django.core.cache import cache
    
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        nombre_documento = request.POST.get('nombre_documento')
        descripcion = request.POST.get('descripcion', '')
        
        if archivo and nombre_documento:
            # Obtener usuario (autenticado o demo)
            usuario = request.user if request.user.is_authenticated else get_demo_user()
            
            # Crear el documento
            DocumentoExpediente.objects.create(
                expediente=expediente,
                etapa=etapa,
                nombre_documento=nombre_documento,
                archivo=archivo,
                descripcion=descripcion,
                subido_por=usuario
            )
            
            # Limpiar la caché de última actualización
            cache_key = f'expediente_{expediente.id}_ultima_actualizacion'
            cache.delete(cache_key)
            
            # Actualizar manualmente la fecha de actualización del expediente
            ahora = timezone.now()
            expediente.fecha_actualizacion = ahora
            expediente.save(update_fields=['fecha_actualizacion'])
            
            # Crear entrada en el historial
            HistorialExpediente.objects.create(
                expediente=expediente,
                usuario=usuario,
                accion='Documento subido',
                descripcion=f'Documento "{nombre_documento}" subido en etapa {etapa}',
                etapa_nueva=etapa
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Documento subido exitosamente',
                'documento': {
                    'nombre': nombre_documento,
                    'fecha': ahora.strftime('%d/%m/%Y %H:%M'),
                    'usuario': usuario.get_full_name() or usuario.username
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Faltan campos requeridos: archivo y nombre_documento son obligatorios'
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
"""

    # Reemplazar la función existente
    content = content.replace(old_func, new_func)
    
    # Añadir la función subir_documento si no existe
    if 'def subir_documento(' not in content:
        # Encontrar la última línea antes de las importaciones
        import_end = content.find('from django.shortcuts')
        if import_end != -1:
            # Insertar después de los imports
            insert_pos = content.find('\n', import_end) + 1
            content = content[:insert_pos] + '\n' + subir_documento_func + '\n' + content[insert_pos:]
    
    # Escribir los cambios
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_views_expedientes()
