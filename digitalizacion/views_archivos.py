"""
Vistas para gestión de archivos y descarga a PC local.
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone

from .models import DocumentoExpediente, Documento

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def api_archivos_pendientes(request):
    """
    Endpoint para listar archivos que aún no tienen ruta_externa.
    Usado por el script de descarga para identificar archivos pendientes.
    """
    try:
        # Obtener documentos de expedientes que aún no tienen ruta_externa
        documentos_expediente = DocumentoExpediente.objects.filter(
            ruta_externa__isnull=True,
            archivo__isnull=False
        ).exclude(archivo='')
        
        # Obtener documentos del modelo antiguo (compatibilidad)
        documentos_antiguos = Documento.objects.filter(
            archivo_digital__isnull=False
        ).exclude(archivo_digital='')
        
        data = []
        
        # Agregar documentos de expedientes
        for doc in documentos_expediente:
            try:
                archivo_url = doc.archivo.url if doc.archivo else None
                if archivo_url:
                    data.append({
                        'id': doc.id,
                        'tipo': 'expediente',
                        'nombre': doc.archivo.name.split("/")[-1],
                        'nombre_documento': doc.nombre_documento,
                        'url': request.build_absolute_uri(archivo_url),
                        'expediente_id': doc.expediente.id,
                        'expediente_numero': doc.expediente.numero_expediente,
                        'fecha_subida': doc.fecha_subida.isoformat() if doc.fecha_subida else None,
                        'tamano': doc.tamano_archivo or 0
                    })
            except Exception as e:
                logger.warning(f"Error al procesar documento {doc.id}: {str(e)}")
                continue
        
        # Agregar documentos antiguos (compatibilidad)
        for doc in documentos_antiguos:
            try:
                archivo_url = doc.archivo_digital.url if doc.archivo_digital else None
                if archivo_url:
                    data.append({
                        'id': doc.id,
                        'tipo': 'documento',
                        'nombre': doc.archivo_digital.name.split("/")[-1],
                        'nombre_documento': doc.titulo,
                        'url': request.build_absolute_uri(archivo_url),
                        'fecha_subida': doc.fecha_creacion.isoformat() if doc.fecha_creacion else None,
                        'tamano': doc.tamaño_archivo or 0
                    })
            except Exception as e:
                logger.warning(f"Error al procesar documento antiguo {doc.id}: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'archivos': data
        }, safe=False)
        
    except Exception as e:
        logger.error(f"Error al obtener archivos pendientes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_marcar_descargado(request, documento_id):
    """
    Endpoint para marcar un documento como descargado.
    Usado por el script de descarga para actualizar el estado.
    """
    try:
        data = json.loads(request.body) if request.body else {}
        ruta_externa = data.get('ruta_externa', '')
        tipo = data.get('tipo', 'expediente')
        
        if not ruta_externa:
            return JsonResponse({
                'success': False,
                'error': 'ruta_externa es requerida'
            }, status=400)
        
        if tipo == 'expediente':
            documento = DocumentoExpediente.objects.get(id=documento_id)
            documento.ruta_externa = ruta_externa
            documento.fecha_descargado = timezone.now()
            documento.save()
        else:
            # Para documentos antiguos, no actualizamos porque no tienen el campo
            # pero podemos loggearlo
            logger.info(f"Documento antiguo {documento_id} descargado a {ruta_externa}")
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Documento marcado como descargado'
        })
        
    except DocumentoExpediente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Documento no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error al marcar documento como descargado: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

