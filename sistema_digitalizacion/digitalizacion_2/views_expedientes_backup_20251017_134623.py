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
    Puede recibir un ID numérico o un slug como identificador del área.
    """
    try:
        print(f"[DEBUG] Iniciando obtener_documentos_por_area. Expediente ID: {expediente_id}, Área ID/Slug: {area_id}")
        
        # Obtener el expediente y forzar la actualización desde la base de datos
        expediente = Expediente.objects.get(pk=expediente_id)
        # Forzar la recarga del objeto desde la base de datos
        expediente.refresh_from_db()
        print(f"[DEBUG] Expediente encontrado: {expediente}")
        
        # Asegurarse de que el expediente tenga número
        if not hasattr(expediente, 'numero_expediente') or not expediente.numero_expediente:
            expediente.numero_expediente = f"EXP-{expediente.id}"
            expediente.save(update_fields=['numero_expediente'])
            expediente.refresh_from_db()  # Recargar después de guardar
        
        # Obtener el área - primero intentamos por ID numérico
        try:
            # Si area_id es un número, lo usamos directamente
            area_id_num = int(area_id)
            print(f"[DEBUG] Buscando área por ID: {area_id_num}")
            area = get_object_or_404(AreaTipoExpediente, id=area_id_num)
        except (ValueError, TypeError):
            # Si no es un número, asumimos que es un slug
            print(f"[DEBUG] Buscando área por slug: {area_id}")
            area = get_object_or_404(AreaTipoExpediente, slug=area_id)
        
        print(f"[DEBUG] Área encontrada: {area} (ID: {area.id}, Slug: {getattr(area, 'slug', 'No disponible')})")
        
        # Obtener los documentos del área
        print(f"[DEBUG] Buscando documentos para expediente {expediente.id} y área {area.id}")
        
        # Intentar con ambos nombres de campo posibles
        filter_params = {
            'expediente': expediente,
            'area_tipo': area  # Primero intentamos con area_tipo
        }
        
        documentos = DocumentoExpediente.objects.filter(**filter_params).select_related('subido_por', 'area_tipo').order_by('-fecha_subida')
        
        # Si no encontramos documentos, intentamos con 'area' en lugar de 'area_tipo'
        if not documentos.exists():
            print("[DEBUG] No se encontraron documentos con 'area_tipo', intentando con 'area'")
            filter_params = {
                'expediente': expediente,
                'area': area
            }
            documentos = DocumentoExpediente.objects.filter(**filter_params).select_related('subido_por', 'area').order_by('-fecha_subida')
        
        print(f"[DEBUG] Se encontraron {documentos.count()} documentos")
        
        # Formatear los documentos
        documentos_data = []
        for doc in documentos:
            try:
                doc_data = {
                    'id': doc.id,
                    'nombre': doc.nombre_documento or f"Documento {doc.id}",
                    'archivo': os.path.basename(doc.archivo.name) if doc.archivo else None,
                    'url': doc.archivo.url if doc.archivo else None,
                    'fecha_creacion': doc.fecha_subida.isoformat(),
                    'creado_por': {
                        'id': doc.subido_por.id if doc.subido_por else None,
                        'nombre': doc.subido_por.get_full_name() if doc.subido_por else 'Usuario desconocido',
                        'foto': doc.subido_por.perfil.foto.url if hasattr(doc.subido_por, 'perfil') and hasattr(doc.subido_por.perfil, 'foto') and doc.subido_por.perfil.foto else None
                    } if doc.subido_por else None,
                    'tamanio': doc.archivo.size if doc.archivo and hasattr(doc.archivo, 'size') else 0,
                    'tipo': os.path.splitext(doc.archivo.name)[1].lstrip('.').lower() if doc.archivo else '',
                    'area': {
                        'id': area.id,
                        'nombre': area.titulo if hasattr(area, 'titulo') else 'Área sin nombre',
                        'slug': getattr(area, 'slug', '')
                    }
                }
                documentos_data.append(doc_data)
            except Exception as e:
                print(f"[ERROR] Error procesando documento {getattr(doc, 'id', 'N/A')}: {str(e)}")
                continue
        
        # Asegurarse de que el expediente tenga número
        if not hasattr(expediente, 'numero_expediente') or not expediente.numero_expediente:
            expediente.numero_expediente = f"EXP-{expediente.id}"
            expediente.save(update_fields=['numero_expediente'])
            
        # Crear la respuesta con compatibilidad para 'numero' y 'numero_expediente'
        response_data = {
            'success': True,
            'documentos': documentos_data,
            'total': len(documentos_data),
            'expediente': {
                'id': expediente.id,
                'numero': expediente.numero_expediente,  # Usando numero_expediente
                'numero_expediente': expediente.numero_expediente,
                'titulo': getattr(expediente, 'titulo', 'Sin título')
            },
            'area': {
                'id': area.id,
                'nombre': getattr(area, 'titulo', getattr(area, 'nombre', 'Área sin nombre')),
                'slug': getattr(area, 'slug', '')
            },
            # Incluir también en la raíz para compatibilidad
            'expediente_id': expediente.id,
            'area_id': area.id,
            'area_nombre': getattr(area, 'titulo', getattr(area, 'nombre', 'Área sin nombre'))
        }
        
        return JsonResponse(response_data)
        
    except Expediente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Expediente no encontrado',
            'code': 'expediente_not_found'
        }, status=404)
        
    except AreaTipoExpediente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Área no encontrada',
            'code': 'area_not_found'
        }, status=404)
        
    except Exception as e:
        error_msg = f"Error en obtener_documentos_por_area: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener los documentos del área',
            'code': 'server_error',
            'detail': str(e)
        }, status=500)

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
                # Llamar a la vista principal de subida de documentos con la etapa del área
                return subir_documento(request, expediente_id, area.etapa)
                
            except AreaTipoExpediente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Área no encontrada'}, status=404)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error en subir_documento_temporal: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
