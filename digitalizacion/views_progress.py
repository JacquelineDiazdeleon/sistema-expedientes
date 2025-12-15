import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Expediente, AreaTipoExpediente, DocumentoExpediente
from .progress import ProgresoExpediente

# Configuración de logging
logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def obtener_progreso_expediente(request, expediente_id):
    """
    Vista para obtener el progreso actual de un expediente.
    Devuelve un JSON con el porcentaje de completado y detalles de áreas.
    """
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos del usuario
        if not request.user.is_staff and expediente.creado_por != request.user:
            return JsonResponse(
                {'success': False, 'error': 'No tienes permiso para ver este expediente.'}, 
                status=403
            )
        
        # Obtener o crear el registro de progreso
        progreso, _ = ProgresoExpediente.objects.get_or_create(
            expediente=expediente,
            defaults={
                'areas_totales': 0,
                'areas_completadas': 0,
                'porcentaje': 0
            }
        )
        
        # Obtener las áreas totales para este tipo de expediente
        areas_totales = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente
        ).count()
        
        # Obtener las áreas completadas (con al menos un documento)
        areas_completadas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            documentos_expediente__expediente=expediente
        ).distinct().count()
        
        # Actualizar el progreso
        progreso.areas_totales = areas_totales or 1  # Evitar división por cero
        progreso.areas_completadas = areas_completadas
        
        # Calcular porcentaje
        if progreso.areas_totales > 0:
            progreso.porcentaje = min(100, int((areas_completadas / progreso.areas_totales) * 100))
        else:
            progreso.porcentaje = 0
            
        progreso.save()
        
        # Obtener detalles de las áreas para el frontend
        areas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente
        ).order_by('orden')
        
        areas_detalle = []
        for area in areas:
            tiene_documentos = area.documentos_expediente.filter(expediente=expediente).exists()
            areas_detalle.append({
                'id': area.id,
                'nombre': area.nombre,
                'completada': tiene_documentos,
                'tipo': area.tipo_area
            })
        
        return JsonResponse({
            'success': True,
            'expediente_id': expediente.id,
            'porcentaje': progreso.porcentaje,
            'areas': {
                'completadas': areas_completadas,
                'totales': progreso.areas_totales,
                'detalle': areas_detalle
            },
            'fecha_actualizacion': progreso.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Error al obtener el progreso del expediente {expediente_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al calcular el progreso del expediente.'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def actualizar_progreso_documento(request, documento_id):
    """
    Vista para actualizar el progreso después de subir o eliminar un documento.
    Esta vista debe ser llamada después de cualquier operación que afecte el progreso.
    """
    try:
        # Obtener el documento
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        expediente = documento.expediente
        
        # Verificar permisos del usuario
        if not request.user.is_staff and expediente.creado_por != request.user:
            return JsonResponse(
                {'success': False, 'error': 'No tienes permiso para actualizar este expediente.'}, 
                status=403
            )
        
        # Obtener o crear el registro de progreso
        progreso, _ = ProgresoExpediente.objects.get_or_create(
            expediente=expediente,
            defaults={
                'areas_totales': 0,
                'areas_completadas': 0,
                'porcentaje': 0
            }
        )
        
        # Actualizar el progreso
        areas_totales = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente
        ).count()
        
        areas_completadas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            documentos_expediente__expediente=expediente
        ).distinct().count()
        
        progreso.areas_totales = areas_totales or 1  # Evitar división por cero
        progreso.areas_completadas = areas_completadas
        
        if progreso.areas_totales > 0:
            progreso.porcentaje = min(100, int((areas_completadas / progreso.areas_totales) * 100))
        else:
            progreso.porcentaje = 0
            
        progreso.save()
        
        return JsonResponse({
            'success': True,
            'expediente_id': expediente.id,
            'porcentaje': progreso.porcentaje,
            'areas_completadas': areas_completadas,
            'areas_totales': progreso.areas_totales
        })
        
    except Exception as e:
        logger.error(f"Error al actualizar progreso para documento {documento_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al actualizar el progreso.'
        }, status=500)
