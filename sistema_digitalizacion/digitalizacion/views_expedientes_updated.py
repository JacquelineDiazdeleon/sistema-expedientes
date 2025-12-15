from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, Value, IntegerField, F, ExpressionWrapper, FloatField
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
from .models import (
    Expediente, EtapaExpediente, DocumentoExpediente, ComentarioEtapa, 
    RequisitoEtapa, HistorialExpediente, Departamento, NotaExpediente, AreaTipoExpediente
)
from .forms import ExpedienteForm
import json
import zipfile
import os
import traceback
from django.conf import settings
# PDF libraries y conversión de documentos
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from docx import Document
from openpyxl import load_workbook
from PIL import Image as PILImage

@login_required
def obtener_documentos_por_area(request, expediente_id, area_id):
    """
    Vista para obtener los documentos de un área específica de un expediente.
    Compatible con ID numérico o slug como identificador del área.
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Solicitando documentos para expediente {expediente_id}, área {area_id}")
        
        # Obtener el expediente con manejo de errores mejorado
        try:
            expediente = Expediente.objects.get(pk=expediente_id)
            # Asegurarse de que el expediente tenga número
            if not hasattr(expediente, 'numero_expediente') or not expediente.numero_expediente:
                expediente.numero_expediente = f"EXP-{expediente.id}"
                expediente.save(update_fields=['numero_expediente'])
                logger.info(f"Generado número de expediente: {expediente.numero_expediente}")
        except Expediente.DoesNotExist:
            logger.error(f"Expediente {expediente_id} no encontrado")
            return JsonResponse({
                'success': False,
                'error': 'Expediente no encontrado',
                'message': 'El expediente solicitado no existe.'
            }, status=404)
        
        # Obtener el área (soporta ID numérico o slug)
        try:
            try:
                area_id_num = int(area_id)
                area = AreaTipoExpediente.objects.get(id=area_id_num)
            except (ValueError, TypeError):
                area = AreaTipoExpediente.objects.get(slug=area_id)
                
            logger.info(f"Área encontrada: {getattr(area, 'titulo', 'Sin título')} (ID: {area.id})")
            
        except AreaTipoExpediente.DoesNotExist:
            logger.error(f"Área {area_id} no encontrada")
            return JsonResponse({
                'success': False,
                'error': 'Área no encontrada',
                'message': 'El área solicitada no existe.'
            }, status=404)
        
        # Obtener documentos con manejo de errores
        try:
            documentos = DocumentoExpediente.objects.filter(
                expediente=expediente,
                etapa=area.slug
            ).select_related('subido_por').order_by('-fecha_subida')
            
            # Formatear documentos para la respuesta
            documentos_data = []
            for doc in documentos:
                try:
                    doc_data = {
                        'id': doc.id,
                        'nombre': doc.nombre_documento,
                        'archivo': os.path.basename(doc.archivo.name) if doc.archivo else None,
                        'archivo_url': doc.archivo.url if doc.archivo else None,
                        'fecha': doc.fecha_subida.isoformat(),
                        'tamaño': getattr(doc.archivo, 'size', 0) if doc.archivo else 0,
                        'tipo': os.path.splitext(doc.archivo.name)[1].lstrip('.').lower() if doc.archivo else '',
                        'subido_por': doc.subido_por.get_full_name() if doc.subido_por else 'Usuario desconocido',
                        'area_nombre': getattr(area, 'titulo', 'Área sin nombre')
                    }
                    documentos_data.append(doc_data)
                except Exception as doc_error:
                    logger.error(f"Error procesando documento {getattr(doc, 'id', 'N/A')}: {str(doc_error)}")
                    continue
            
            # Construir respuesta exitosa
            response_data = {
                'success': True,
                'documentos': documentos_data,
                'total': len(documentos_data),
                'expediente': {
                    'id': expediente.id,
                    'numero': expediente.numero_expediente,  # Usando la propiedad de compatibilidad
                    'numero_expediente': expediente.numero_expediente,
                    'titulo': getattr(expediente, 'titulo', 'Sin título')
                },
                'area': {
                    'id': area.id,
                    'nombre': getattr(area, 'titulo', getattr(area, 'nombre', 'Área sin nombre')),
                    'slug': getattr(area, 'slug', '')
                }
            }
            
            logger.info(f"Devolviendo {len(documentos_data)} documentos para el área {area.id}")
            return JsonResponse(response_data)
            
        except Exception as query_error:
            logger.error(f"Error al consultar documentos: {str(query_error)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Error al consultar la base de datos',
                'message': 'Ocurrió un error al recuperar los documentos.',
                'debug': str(query_error)
            }, status=500)
            
    except Exception as e:
        logger.critical(f"Error inesperado en obtener_documentos_por_area: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': 'Ha ocurrido un error inesperado al procesar la solicitud.'
        }, status=500)
