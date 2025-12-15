"""
Vistas mejoradas para el manejo de documentos en el sistema de digitalización.
"""
import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils import timezone
from .models import Expediente, DocumentoExpediente, HistorialExpediente, AreaTipoExpediente
import os

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Obtiene la dirección IP del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
@require_http_methods(["POST"])
def subir_documento(request, expediente_id, etapa):
    """
    Vista mejorada para subir documentos a una etapa específica.
    
    Args:
        request: Objeto HttpRequest
        expediente_id: ID del expediente al que se adjuntará el documento
        etapa: Etapa del flujo de trabajo donde se sube el documento
        
    Returns:
        JsonResponse con el resultado de la operación
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        area = get_object_or_404(AreaTipoExpediente, id=request.POST.get('area_id'))

        archivo = request.FILES.get('documento')
        if not archivo:
            return JsonResponse({'success': False, 'error': 'No se proporcionó ningún archivo'}, status=400)

        # Obtener el nombre personalizado del documento
        # Priorizar nombre_documento, luego nombre, luego nombreDocumento, y finalmente el nombre del archivo
        nombre_personalizado = (
            request.POST.get('nombre_documento', '').strip() or  # Primero buscar con guión bajo
            request.POST.get('nombre', '').strip() or
            request.POST.get('nombreDocumento', '').strip() or
            archivo.name  # Usar el nombre del archivo como último recurso
        )
        
        logger.info(f"📝 Nombre del documento - Personalizado: '{nombre_personalizado}', Archivo original: '{archivo.name}'")

        descripcion = request.POST.get('descripcion', '').strip() or f"Documento subido para el área {area.descripcion or area.nombre}"

        # ✅ Crear el registro con nombre personalizado
        documento = DocumentoExpediente(
            expediente=expediente,
            area=area,
            archivo=archivo,
            nombre_documento=nombre_personalizado,
            descripcion=descripcion,
            subido_por=request.user,
            etapa=etapa,
            ip_origen=get_client_ip(request)
        )
        
        # Guardar explícitamente para asegurar que el nombre se guarde
        documento.save(force_insert=True)
        
        # Asegurarse de que el nombre personalizado se guardó correctamente
        if documento.nombre_documento != nombre_personalizado:
            documento.nombre_documento = nombre_personalizado
            documento.save(update_fields=['nombre_documento'])

        # Actualizar caché
        cache_key = f'expediente_{expediente.id}_ultima_actualizacion'
        cache.delete(cache_key)
        
        # Actualizar fecha de actualización del expediente
        expediente.fecha_actualizacion = timezone.now()
        expediente.save(update_fields=['fecha_actualizacion'])
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion='DOCUMENTO_SUBIDO',
            descripcion=f'Documento "{nombre_personalizado}" subido en etapa {etapa}',
            etapa_nueva=etapa,
            ip_origen=get_client_ip(request)
        )

        logger.info(f"📄 Documento '{nombre_personalizado}' subido por {request.user} para expediente {expediente.numero}")

        # Asegurarse de que el archivo se haya guardado correctamente
        if not documento.archivo:
            raise Exception("Error al guardar el archivo en el servidor")

        # Construir la respuesta con todos los campos necesarios
        response_data = {
            'success': True,
            'message': 'Documento subido exitosamente.',
            'documento': {
                'id': documento.id,
                'nombre': documento.nombre_documento,  # Nombre personalizado para mostrar
                'nombre_documento': documento.nombre_documento,  # Incluido explícitamente
                'nombre_archivo': os.path.basename(documento.archivo.name),
                'descripcion': documento.descripcion or f"Documento subido para el área {area.descripcion or area.nombre}",
                'fecha_subida': documento.fecha_subida.strftime('%Y-%m-%d'),
                'subido_por': request.user.get_full_name() or request.user.username,
                'archivo_url': documento.archivo.url,
                'tipo': archivo.content_type if hasattr(archivo, 'content_type') else '',
                'tamano_archivo': archivo.size if hasattr(archivo, 'size') else 0,
                'tamano_formateado': f'{(archivo.size / 1024):.2f} KB' if hasattr(archivo, 'size') else '0 KB',
                'fecha': timezone.now().strftime('%d/%m/%Y %H:%M')
            }
        }
        
        # Depuración: Mostrar la respuesta que se enviará
        import json
        logger.info(f"📤 Enviando respuesta al frontend: {json.dumps(response_data, indent=2, default=str)}")
        
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error al subir documento: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa directamente del formulario.
    """
    try:
        if request.method == 'POST':
            # Obtener la etapa del formulario
            etapa = request.POST.get('etapa')
            if not etapa:
                logger.warning(
                    f"Intento de subida sin especificar etapa - "
                    f"Usuario: {request.user.username}, "
                    f"Expediente: {expediente_id}"
                )
                return JsonResponse({
                    'success': False, 
                    'error': 'No se especificó la etapa del documento.'
                }, status=400)
                
            # Llamar a la vista principal de subida de documentos con la etapa
            return subir_documento(request, expediente_id, etapa)
        
        return JsonResponse({
            'success': False, 
            'error': 'Método no permitido. Se requiere una petición POST.'
        }, status=405)
    
    except Exception as e:
        logger.error(
            f"Error en subir_documento_temporal - "
            f"Usuario: {request.user.username if hasattr(request, 'user') else 'Anónimo'}, "
            f"Expediente: {expediente_id}, "
            f"Error: {str(e)}", 
            exc_info=True
        )
        return JsonResponse({
            'success': False, 
            'error': 'Error al procesar la solicitud de subida de documento.'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def eliminar_documento(request, documento_id):
    """
    Vista para eliminar un documento del sistema.
    
    Args:
        request: Objeto HttpRequest
        documento_id: ID del documento a eliminar
        
    Returns:
        JsonResponse con el resultado de la operación
    """
    try:
        # Obtener el documento o devolver 404 si no existe
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        
        # Verificar permisos (solo el propietario o un superusuario pueden eliminar)
        if not (request.user.is_superuser or documento.subido_por == request.user):
            return JsonResponse({
                'success': False,
                'message': 'No tienes permiso para eliminar este documento.'
            }, status=403)
        
        # Guardar información para el historial
        expediente = documento.expediente
        nombre_archivo = documento.archivo.name
        
        # Eliminar el archivo físico
        if os.path.isfile(documento.archivo.path):
            os.remove(documento.archivo.path)
        
        # Crear registro en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Documento eliminado: {nombre_archivo}',
            ip_origen=get_client_ip(request)
        )
        
        # Eliminar el registro de la base de datos
        documento.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Documento eliminado correctamente.'
        })
        
    except Exception as e:
        logger.error(f'Error al eliminar documento {documento_id}: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el documento: {str(e)}'
        }, status=500)
