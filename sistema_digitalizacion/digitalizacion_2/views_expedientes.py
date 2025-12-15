from django.contrib.auth import get_user_model

def get_demo_user():
    """Obtener o crear un usuario demo para operaciones sin autenticación"""
    User = get_user_model()
    return User.objects.get_or_create(
        username='usuario_demo',
        defaults={'is_active': False, 'is_staff': False, 'is_superuser': False}
    )[0]

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
def detalle_expediente(request, pk):
    """Vista para mostrar los detalles de un expediente con sus etapas"""
    expediente = get_object_or_404(Expediente, pk=pk)
    
    # Definir el orden correcto de las etapas según el esquema solicitado
    orden_etapas = [
        'inicio',
        'solicitud_area',
        'cotizacion',
        'requisicion_sima',
        'suficiencia_presupuestal',
        'aprobacion_director',
        'aprobacion_secretario',
        'notificacion_compras',
        'valoracion_tipo',
        'adjudicacion',
        'formalizacion',
        'contrato',
        'recepcion_bien',
        'recepcion_facturacion',
        'generacion_evidencia',
        'envio_compras',
        'pago',
    ]
    
    # Obtener etapas en el orden correcto
    etapas_dict = {etapa.nombre_etapa: etapa for etapa in expediente.etapas.all()}
    etapas = [etapas_dict[nombre_etapa] for nombre_etapa in orden_etapas if nombre_etapa in etapas_dict]
    
    historial = expediente.historial.all()[:10]
    
    # Obtener requisitos según el tipo de expediente
    requisitos_por_etapa = {}
    for etapa in etapas:
        requisitos = obtener_requisitos_etapa(expediente, etapa.nombre_etapa)
        documentos = expediente.documentos.filter(etapa=etapa.nombre_etapa)
        comentarios = expediente.comentarios.filter(etapa=etapa.nombre_etapa)[:5]
        
        # Crear lista de nombres de documentos para verificación en template
        documentos_nombres = list(documentos.values_list('nombre_documento', flat=True))
        
        requisitos_por_etapa[etapa.nombre_etapa] = {
            'etapa': etapa,
            'requisitos': requisitos,
            'documentos': documentos,
            'documentos_nombres': documentos_nombres,
            'comentarios': comentarios,
            'puede_completar': puede_completar_etapa(expediente, etapa.nombre_etapa),
        }
    
    # Obtener el último documento subido
    ultimo_documento = expediente.documentos.order_by('-fecha_subida').first()
    
    # Obtener la última actualización (fecha del último documento o fecha de actualización del expediente)
    ultima_actualizacion = ultimo_documento.fecha_subida if ultimo_documento else expediente.fecha_actualizacion
    
    # Si hay un último documento y la fecha es más reciente que la de actualización del expediente
    if ultimo_documento and ultimo_documento.fecha_subida > expediente.fecha_actualizacion:
        expediente.fecha_actualizacion = ultimo_documento.fecha_subida
        expediente.save(update_fields=['fecha_actualizacion'])
    
    # Preparar datos para la respuesta JSON
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    if is_ajax:
        try:
            # Si es una petición AJAX, devolver JSON
            expediente_data = {
                'id': expediente.id,
                'numero_expediente': expediente.numero_expediente,
                'titulo': expediente.titulo,
                'descripcion': expediente.descripcion,
                'fecha_creacion': expediente.fecha_creacion.isoformat(),
                'estado_actual': expediente.estado_actual,
                'tipo_expediente': expediente.get_tipo_expediente_display(),
                'departamento': str(expediente.departamento) if expediente.departamento else None,
                'responsable': str(expediente.responsable) if expediente.responsable else None,
                'progreso': expediente.get_progreso(),
                'ultima_actualizacion': ultima_actualizacion.isoformat() if ultima_actualizacion else None,
            }
            return JsonResponse({
                'success': True,
                'expediente': expediente_data
            }, json_dumps_params={'ensure_ascii': False}, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # Si no es AJAX, renderizar la plantilla normal
    context = {
        'expediente': expediente,
        'etapas': etapas,
        'requisitos_por_etapa': requisitos_por_etapa,
        'historial': historial,
        'progreso': expediente.get_progreso(),
        'ultima_actualizacion': ultima_actualizacion,
        'ultimo_documento': ultimo_documento,
    }
    
    return render(request, 'digitalizacion/expedientes/detalle_expediente.html', context)

def obtener_requisitos_etapa(expediente, nombre_etapa):
    """Obtiene los requisitos para una etapa específica"""
    # Implementación básica - ajustar según tu modelo de RequisitoEtapa
    return []

def puede_completar_etapa(expediente, nombre_etapa):
    """Verifica si una etapa puede ser completada"""
    # Implementación básica - ajustar según tu lógica de negocio
    return False

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

