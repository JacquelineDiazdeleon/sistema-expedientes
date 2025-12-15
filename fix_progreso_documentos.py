from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import Expediente, AreaTipoExpediente, DocumentoExpediente, ValorAreaExpediente

def get_obtener_progreso_documentos():
    """Devuelve la función actualizada de obtener_progreso_documentos"""
    @login_required
    @require_http_methods(["GET"])
    def obtener_progreso_documentos(request, expediente_id):
        """Vista para obtener el progreso de documentos de un expediente"""
        try:
            # Obtener el expediente
            expediente = get_object_or_404(Expediente, id=expediente_id)
            
            # Verificar que el expediente tenga un número de expediente
            if not hasattr(expediente, 'numero_expediente') or not expediente.numero_expediente:
                return JsonResponse({
                    'success': False,
                    'error': 'El expediente no tiene un número de expediente asignado',
                    'code': 'missing_expediente_number'
                }, status=400)
            
            # Obtener todas las áreas configuradas para este tipo de expediente
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=expediente.tipo_expediente,
                activa=True
            ).order_by('orden')
            
            # Si hay un subtipo de expediente, filtrar por él
            if hasattr(expediente, 'subtipo_expediente') and expediente.subtipo_expediente:
                areas = areas.filter(
                    Q(subtipo_expediente=expediente.subtipo_expediente) | 
                    Q(subtipo_expediente__isnull=True)
                )
            
            # Obtener el conteo de documentos por área
            areas_data = []
            areas_completadas = 0
            
            for area in areas:
                # Contar documentos en esta área
                documentos_count = DocumentoExpediente.objects.filter(
                    expediente=expediente,
                    etapa=area.nombre
                ).count()
                
                # Verificar si el área está completada
                valor_area = ValorAreaExpediente.objects.filter(
                    expediente=expediente,
                    area=area
                ).first()
                
                completada = bool(valor_area and valor_area.completada)
                if completada:
                    areas_completadas += 1
                
                areas_data.append({
                    'id': str(area.id),
                    'nombre': area.nombre,
                    'titulo': area.titulo,
                    'completada': completada,
                    'documentos_count': documentos_count,
                    'obligatoria': area.obligatoria,
                    'fecha_completada': valor_area.fecha_completada if valor_area else None,
                    'completada_por': valor_area.completada_por.get_full_name() if valor_area and valor_area.completada_por else None
                })
            
            # Calcular el porcentaje de completado
            total_areas = len(areas_data)
            porcentaje_completo = 0
            if total_areas > 0:
                porcentaje_completo = int((areas_completadas / total_areas) * 100)
            
            # Devolver los datos en formato JSON
            return JsonResponse({
                'success': True,
                'expediente_id': expediente_id,
                'numero_expediente': expediente.numero_expediente,  # Asegurarse de incluir el número de expediente
                'areas': areas_data,
                'porcentaje_completo': porcentaje_completo,
                'areas_completadas': areas_completadas,
                'total_areas': total_areas,
                'ultima_actualizacion': timezone.now().isoformat()
            })
            
        except Exception as e:
            import traceback
            return JsonResponse({
                'success': False,
                'error': str(e),
                'trace': traceback.format_exc() if settings.DEBUG else None
            }, status=500)
    
    return obtener_progreso_documentos
