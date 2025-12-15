"""
Vistas para el sistema de solicitudes de escaneo remoto.
Permite que cualquier dispositivo solicite un escaneo que será
procesado por el servicio de escaneo local.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from .models import Expediente, SolicitudEscaneo, DocumentoExpediente

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def crear_solicitud_escaneo(request):
    """
    Crea una nueva solicitud de escaneo.
    Esta solicitud será procesada por el servicio de escaneo local.
    """
    try:
        data = json.loads(request.body)
        
        expediente_id = data.get('expediente_id')
        area_id = data.get('area_id')
        nombre_documento = data.get('nombre_documento', '').strip()
        descripcion = data.get('descripcion', '').strip()
        duplex = data.get('duplex', False)
        
        # Validaciones
        if not expediente_id:
            return JsonResponse({'success': False, 'error': 'ID de expediente requerido'}, status=400)
        if not area_id:
            return JsonResponse({'success': False, 'error': 'ID de área requerido'}, status=400)
        if not nombre_documento:
            return JsonResponse({'success': False, 'error': 'Nombre del documento requerido'}, status=400)
        
        # Obtener expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Crear solicitud
        solicitud = SolicitudEscaneo.objects.create(
            expediente=expediente,
            area_id=int(area_id),
            nombre_documento=nombre_documento,
            descripcion=descripcion,
            duplex=duplex,
            solicitado_por=request.user,
            estado='pendiente'
        )
        
        logger.info(f"Solicitud de escaneo creada: {solicitud.id} por {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'solicitud_id': solicitud.id,
            'mensaje': 'Solicitud de escaneo creada. El documento será escaneado pronto.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error al crear solicitud de escaneo: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def estado_solicitud_escaneo(request, solicitud_id):
    """
    Obtiene el estado de una solicitud de escaneo.
    """
    try:
        solicitud = get_object_or_404(SolicitudEscaneo, id=solicitud_id)
        
        return JsonResponse({
            'success': True,
            'solicitud': {
                'id': solicitud.id,
                'estado': solicitud.estado,
                'nombre_documento': solicitud.nombre_documento,
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat(),
                'fecha_procesamiento': solicitud.fecha_procesamiento.isoformat() if solicitud.fecha_procesamiento else None,
                'fecha_completado': solicitud.fecha_completado.isoformat() if solicitud.fecha_completado else None,
                'mensaje_error': solicitud.mensaje_error,
                'documento_id': solicitud.documento_creado.id if solicitud.documento_creado else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error al obtener estado de solicitud: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cancelar_solicitud_escaneo(request, solicitud_id):
    """
    Cancela una solicitud de escaneo pendiente.
    """
    try:
        solicitud = get_object_or_404(SolicitudEscaneo, id=solicitud_id)
        
        if solicitud.solicitado_por != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'No tienes permiso para cancelar esta solicitud'}, status=403)
        
        if solicitud.cancelar():
            return JsonResponse({'success': True, 'mensaje': 'Solicitud cancelada'})
        else:
            return JsonResponse({'success': False, 'error': 'La solicitud ya no puede ser cancelada'}, status=400)
        
    except Exception as e:
        logger.error(f"Error al cancelar solicitud: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# ENDPOINTS PARA EL SERVICIO DE ESCANEO LOCAL
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def obtener_solicitudes_pendientes(request):
    """
    Endpoint para el servicio de escaneo local.
    Retorna las solicitudes pendientes de escaneo.
    Requiere token de autenticación.
    """
    # Verificar token
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({'success': False, 'error': 'Token requerido'}, status=401)
    
    token = auth_header.split(" ", 1)[1].strip()
    expected_token = getattr(settings, 'SCANNER_UPLOAD_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return JsonResponse({'success': False, 'error': 'Token inválido'}, status=401)
    
    try:
        # Obtener solicitudes pendientes (ordenadas por fecha, más antiguas primero)
        solicitudes = SolicitudEscaneo.objects.filter(
            estado='pendiente'
        ).order_by('fecha_solicitud')[:5]  # Máximo 5 a la vez
        
        solicitudes_data = []
        for sol in solicitudes:
            solicitudes_data.append({
                'id': sol.id,
                'expediente_id': sol.expediente.id,
                'area_id': sol.area_id,
                'nombre_documento': sol.nombre_documento,
                'descripcion': sol.descripcion or '',
                'duplex': sol.duplex,
                'solicitado_por': sol.solicitado_por.username if sol.solicitado_por else 'sistema'
            })
        
        return JsonResponse({
            'success': True,
            'count': len(solicitudes_data),
            'solicitudes': solicitudes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener solicitudes pendientes: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_solicitud_procesando(request, solicitud_id):
    """
    Marca una solicitud como "procesando".
    Llamado por el servicio de escaneo local cuando comienza a escanear.
    """
    # Verificar token
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({'success': False, 'error': 'Token requerido'}, status=401)
    
    token = auth_header.split(" ", 1)[1].strip()
    expected_token = getattr(settings, 'SCANNER_UPLOAD_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return JsonResponse({'success': False, 'error': 'Token inválido'}, status=401)
    
    try:
        solicitud = get_object_or_404(SolicitudEscaneo, id=solicitud_id)
        solicitud.marcar_procesando()
        
        logger.info(f"Solicitud {solicitud_id} marcada como procesando")
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error al marcar solicitud como procesando: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_solicitud_completada(request, solicitud_id):
    """
    Marca una solicitud como "completada".
    Llamado por el servicio de escaneo local después de subir el documento.
    """
    # Verificar token
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({'success': False, 'error': 'Token requerido'}, status=401)
    
    token = auth_header.split(" ", 1)[1].strip()
    expected_token = getattr(settings, 'SCANNER_UPLOAD_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return JsonResponse({'success': False, 'error': 'Token inválido'}, status=401)
    
    try:
        data = json.loads(request.body) if request.body else {}
        documento_id = data.get('documento_id')
        
        solicitud = get_object_or_404(SolicitudEscaneo, id=solicitud_id)
        
        documento = None
        if documento_id:
            try:
                documento = DocumentoExpediente.objects.get(id=documento_id)
            except DocumentoExpediente.DoesNotExist:
                pass
        
        solicitud.marcar_completado(documento)
        
        logger.info(f"Solicitud {solicitud_id} completada")
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error al marcar solicitud como completada: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_solicitud_error(request, solicitud_id):
    """
    Marca una solicitud con error.
    Llamado por el servicio de escaneo local si hay un error.
    """
    # Verificar token
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({'success': False, 'error': 'Token requerido'}, status=401)
    
    token = auth_header.split(" ", 1)[1].strip()
    expected_token = getattr(settings, 'SCANNER_UPLOAD_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return JsonResponse({'success': False, 'error': 'Token inválido'}, status=401)
    
    try:
        data = json.loads(request.body) if request.body else {}
        mensaje_error = data.get('error', 'Error desconocido')
        
        solicitud = get_object_or_404(SolicitudEscaneo, id=solicitud_id)
        solicitud.marcar_error(mensaje_error)
        
        logger.info(f"Solicitud {solicitud_id} marcada con error: {mensaje_error}")
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error al marcar solicitud con error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

