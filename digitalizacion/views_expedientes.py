# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportOperatorIssue=false
# Importaciones estándar de Django
import io
import os
import zipfile
import json
import logging
import traceback
import tempfile
import re
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages as django_messages
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction, DatabaseError
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
# Importaciones de modelos locales
from .models import (
    Expediente, 
    DocumentoExpediente, 
    ComentarioEtapa, 
    HistorialExpediente,
    AreaTipoExpediente, 
    ComentarioArea, 
    Notificacion, 
    EtapaExpediente, 
    TipoDocumento,
    Expediente  # Importación del modelo Expediente
)
from .role_utils import (
    puede_ver_expedientes, puede_crear_expedientes, puede_editar_expedientes,
    puede_eliminar_expedientes, puede_administrar_sistema, puede_aprobar_usuarios,
    es_visualizador, es_editor, es_administrador
)
logger = logging.getLogger(__name__)
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F, Value, CharField, Case, When, Value, BooleanField
from django.db.models.functions import Concat, Coalesce
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File
from django.apps import apps
from django.forms import modelformset_factory
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponseForbidden, FileResponse
from django.utils.encoding import smart_str
import mimetypes
import os
# Configuración de logging
logger = logging.getLogger(__name__)
# Importación de modelos usando get_model para evitar importaciones circulares
Expediente = apps.get_model('digitalizacion', 'Expediente')
DocumentoExpediente = apps.get_model('digitalizacion', 'DocumentoExpediente')
MensajeExpediente = apps.get_model('digitalizacion', 'MensajeExpediente')
AreaTipoExpediente = apps.get_model('digitalizacion', 'AreaTipoExpediente')
HistorialExpediente = apps.get_model('digitalizacion', 'HistorialExpediente')
User = apps.get_model('auth', 'User')
ComentarioArea = apps.get_model('digitalizacion', 'ComentarioArea')
Notificacion = apps.get_model('digitalizacion', 'Notificacion')
Departamento = apps.get_model('digitalizacion', 'Departamento')
# Importación de formularios
from .forms import ExpedienteForm
# Constantes
SUBTIPOS_LICITACION = {
    'licitacion_recurso_propio': 'licitacion',
    'licitacion_fondo_federal': 'licitacion'
}
# Intento de importar PyMuPDF para funcionalidad de PDF
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("Advertencia: PyMuPDF (fitz) no está instalado. Algunas funcionalidades de PDF podrían no estar disponibles.")
# Importaciones para el manejo de documentos de Word
try:
    from docx import Document
    from docx.shared import Inches, Mm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import RGBColor
except ImportError:
    print("Advertencia: python-docx no está instalado. Algunas funcionalidades de Word podrían no estar disponibles.")
# Importaciones para ReportLab (generación de PDFs)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Advertencia: ReportLab no está instalado. Algunas funcionalidades de PDF podrían no estar disponibles.")
    # Definir variables dummy para evitar errores
    letter = None  # type: ignore
    SimpleDocTemplate = None  # type: ignore
    Paragraph = None  # type: ignore
    Spacer = None  # type: ignore
    Table = None  # type: ignore
    TableStyle = None  # type: ignore
    PageBreak = None  # type: ignore
    getSampleStyleSheet = None  # type: ignore
    ParagraphStyle = None  # type: ignore
    TA_CENTER = None  # type: ignore
    TA_RIGHT = None  # type: ignore
    colors = None  # type: ignore
# Deshabilitar mensajes
@login_required
@require_http_methods(["POST"])
def guardar_expediente(request, expediente_id):
    """
    Vista para guardar los cambios de un expediente existente
    """
    try:
        # Obtener el expediente o devolver 404 si no existe
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos (solo el usuario que creó el expediente o superusuarios pueden editarlo)
        if not (request.user.is_superuser or expediente.creado_por == request.user):
            messages.error(request, 'No tienes permiso para editar este expediente.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Verificar que el expediente no esté en un estado que impida la edición
        if expediente.estado in ['aprobado', 'rechazado']:
            messages.error(request, 'No se puede editar un expediente que ya ha sido aprobado o rechazado.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Procesar el formulario
        form = ExpedienteForm(request.POST, request.FILES, instance=expediente)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar los cambios en el expediente
                    expediente = form.save(commit=False)
                    expediente.modificado_por = request.user
                    expediente.fecha_modificacion = timezone.now()
                    expediente.save()
                    form.save_m2m()  # Guardar relaciones many-to-many
                    
                    # Registrar en el historial
                    HistorialExpediente.crear_registro(
                        usuario=request.user,
                        accion='actualizar_expediente',
                        modelo='Expediente',
                        objeto_id=expediente.id,
                        detalles='Se actualizaron los datos del expediente.'
                    )
                    
                    messages.success(request, 'Los cambios en el expediente se han guardado correctamente.')
                    return redirect('expedientes:lista_expedientes')
                    
            except Exception as e:
                logger.error(f"Error al guardar el expediente {expediente_id}: {str(e)}")
                messages.error(request, f'Error al guardar los cambios: {str(e)}')
        else:
            # Si el formulario no es válido, mostrar los errores
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
            
        # Si hay errores, redirigir de vuelta al formulario de edición
        return redirect('expedientes:editar', expediente_id=expediente_id)
        
    except Exception as e:
        logger.error(f"Error en guardar_expediente: {str(e)}")
        messages.error(request, 'Ocurrió un error al procesar la solicitud.')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
@login_required
@login_required
@require_http_methods(["POST"])
@login_required
@require_http_methods(["POST"])
@login_required
@login_required
@require_http_methods(["POST"])
@login_required
@require_http_methods(["POST"])
@login_required
@login_required
def generar_pdf_completo(request, expediente_id):
    """
    Vista para generar un PDF con la información completa de un expediente
    """
    try:
        # Obtener el expediente con sus relaciones
        expediente = get_object_or_404(
            Expediente.objects.select_related(
                'creado_por', 'area', 'modificado_por', 'usuario_rechazo'
            ).prefetch_related(
                'documentos__tipo_documento',
                'documentos__subido_por',
                'historial__usuario',
                'comentarios__usuario',
                'etapas'
            ),
            id=expediente_id
        )
        
        # Verificar permisos
        if not (request.user.is_superuser or expediente.area in request.user.areas.all()):
            messages.error(request, 'No tienes permiso para ver este expediente.')
            return redirect('expedientes:detalle', pk=expediente_id)
        
        # Verificar que ReportLab esté disponible
        if not REPORTLAB_AVAILABLE:
            messages.error(request, 'La funcionalidad de generación de PDF no está disponible. Por favor, instale ReportLab.')
            return redirect('expedientes:detalle', pk=expediente_id)
        
        # Crear el objeto HttpResponse con los headers de PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="expediente_{expediente.numero_expediente}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        # Crear el objeto PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,  # type: ignore 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Estilos
        styles = getSampleStyleSheet()  # type: ignore
        styles.add(ParagraphStyle(  # type: ignore
            name='Titulo',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,  # type: ignore
            spaceAfter=20
        ))
        styles.add(ParagraphStyle(  # type: ignore
            name='Subtitulo',
            fontSize=12,
            leading=16,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(  # type: ignore
            name='Normal',
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        
        # Contenido del PDF
        elements = []
        
        # Título
        elements.append(Paragraph(f"Expediente: {expediente.numero_expediente}", styles['Title']))  # type: ignore
        elements.append(Spacer(1, 12))  # type: ignore
        
        # Información del expediente
        elements.append(Paragraph("Información General", styles['Heading2']))  # type: ignore
        data = [
            ['Tipo', expediente.get_tipo_display()],
            ['Estado', expediente.get_estado_display()],
            ['Área', str(expediente.area)],
            ['Creado por', f"{expediente.creado_por.get_full_name()} ({expediente.creado_por.username})"],
            ['Fecha de creación', expediente.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
            ['Última modificación', expediente.fecha_modificacion.strftime('%d/%m/%Y %H:%M') if expediente.fecha_modificacion else 'N/A'],
        ]
        
        if expediente.estado == 'rechazado' and expediente.usuario_rechazo:
            data.append(['Rechazado por', f"{expediente.usuario_rechazo.get_full_name()} ({expediente.usuario_rechazo.username})"])
            if expediente.razon_rechazo:
                data.append(['Razón de rechazo', expediente.razon_rechazo])
        
        t = Table(data, colWidths=[doc.width/3.0]*2)  # type: ignore
        t.setStyle(TableStyle([  # type: ignore
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),  # type: ignore
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # type: ignore
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # type: ignore
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))  # type: ignore
        
        # Documentos
        if expediente.documentos.exists():
            elements.append(Paragraph("Documentos", styles['Heading2']))  # type: ignore
            data = [['Tipo', 'Nombre', 'Subido por', 'Fecha', 'Tamaño']]
            
            for doc in expediente.documentos.all():
                data.append([
                    doc.tipo_documento.nombre if doc.tipo_documento else 'Sin tipo',
                    doc.nombre,
                    doc.subido_por.get_full_name() if hasattr(doc.subido_por, 'get_full_name') else str(doc.subido_por),
                    doc.fecha_subida.strftime('%d/%m/%Y %H:%M'),
                    f"{doc.tamano_bytes/1024:.1f} KB" if doc.tamano_bytes else 'N/A'
                ])
            
            t = Table(data, colWidths=[doc.width*0.2]*5)  # type: ignore
            t.setStyle(TableStyle([  # type: ignore
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),  # type: ignore
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # type: ignore
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # type: ignore
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))  # type: ignore
        
        # Historial
        if expediente.historial.exists():
            elements.append(Paragraph("Historial", styles['Heading2']))  # type: ignore
            data = [['Fecha', 'Usuario', 'Acción', 'Detalles']]
            
            for h in expediente.historial.order_by('-fecha_accion'):
                data.append([
                    h.fecha_accion.strftime('%d/%m/%Y %H:%M'),
                    h.usuario.get_full_name() if hasattr(h.usuario, 'get_full_name') else str(h.usuario),
                    h.get_accion_display(),
                    h.detalles[:100] + '...' if h.detalles and len(h.detalles) > 100 else (h.detalles or '')
                ])
            
            t = Table(data, colWidths=[doc.width*0.15, doc.width*0.2, doc.width*0.2, doc.width*0.45])  # type: ignore
            t.setStyle(TableStyle([  # type: ignore
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),  # type: ignore
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # type: ignore
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # type: ignore
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)
        
        # Pie de página
        elements.append(PageBreak())  # type: ignore
        elements.append(Paragraph(f"Generado el: {timezone.now().strftime('%d/%m/%Y %H:%M')} por {request.user.get_full_name() or request.user.username}",  # type: ignore
                               style=ParagraphStyle(name='Footer', fontSize=8, alignment=TA_RIGHT)))  # type: ignore
        
        # Construir el PDF
        doc.build(elements)  # type: ignore
        
        # Obtener el valor del buffer y enviar la respuesta
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        # Registrar en el historial
        HistorialExpediente.crear_registro(
            usuario=request.user,
            accion='generar_pdf',
            modelo='Expediente',
            objeto_id=expediente.id,
            detalles='Se generó el archivo PDF del expediente.'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error en generar_pdf_completo: {str(e)}")
        messages.error(request, 'Ocurrió un error al generar el PDF.')
        return redirect('expedientes:detalle', pk=expediente_id)
@login_required
def descargar_expediente(request, expediente_id):
    """
    Vista para descargar todos los documentos de un expediente en un archivo ZIP
    """
    logger.info(f"=== INICIO descargar_expediente ===")
    logger.info(f"Expediente ID: {expediente_id}")
    logger.info(f"Usuario: {request.user.get_full_name()} (ID: {request.user.id})")
    
    try:
        # Obtener el expediente
        try:
            expediente = Expediente.objects.get(id=expediente_id)
            logger.info(f"Expediente encontrado: {expediente.numero_expediente}")
        except Expediente.DoesNotExist:
            logger.error(f"Expediente no encontrado: {expediente_id}")
            messages.error(request, 'El expediente solicitado no existe.')
            return redirect('expedientes:listar')
        
        # Verificar permisos (solo superusuario o usuario que creó el expediente)
        if not (request.user.is_superuser or expediente.creado_por == request.user):
            logger.warning(f"Usuario {request.user.id} no tiene permiso para descargar el expediente {expediente_id}")
            messages.error(request, 'No tienes permiso para descargar este expediente.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Obtener documentos del expediente
        documentos = list(expediente.documentos.all())
        logger.info(f"Documentos encontrados: {len(documentos)}")
        
        if not documentos:
            logger.warning(f"El expediente {expediente_id} no tiene documentos para descargar")
            messages.warning(request, 'El expediente no contiene documentos para descargar.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Crear un archivo ZIP en memoria
        buffer = io.BytesIO()
        archivos_agregados = 0
        
        try:
            # Crear el archivo ZIP
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Obtener el departamento si existe
                departamento = ''
                if hasattr(expediente, 'departamento') and expediente.departamento:
                    departamento = expediente.departamento.nombre
                
                # Obtener giro si existe
                giro = getattr(expediente, 'giro', 'No especificado')
                
                # Obtener tipo de adquisición si existe
                tipo_adquisicion = getattr(expediente, 'tipo_adquisicion', 'No especificado')
                if hasattr(expediente, 'get_tipo_adquisicion_display'):
                    tipo_adquisicion = expediente.get_tipo_adquisicion_display()
                
                # Obtener fuente de financiamiento si existe
                fuente_financiamiento = getattr(expediente, 'fuente_financiamiento', 'No especificado')
                if hasattr(expediente, 'get_fuente_financiamiento_display'):
                    fuente_financiamiento = expediente.get_fuente_financiamiento_display()
                
                # Crear el contenido del archivo de información
                info_expediente = (
                    "=== INFORMACIÓN DEL EXPEDIENTE ===\n\n"
                    f"Número de Expediente: {expediente.numero_expediente}\n"
                    f"Título: {getattr(expediente, 'titulo', 'No especificado')}\n"
                    f"Tipo: {expediente.get_tipo_expediente_display() if hasattr(expediente, 'get_tipo_expediente_display') else 'No especificado'}\n"
                    f"Estado: {expediente.get_estado_display() if hasattr(expediente, 'get_estado_display') else 'No especificado'}\n"
                    f"Descripción: {getattr(expediente, 'descripcion', 'No especificada')}\n"
                    f"Creado por: {expediente.creado_por.get_full_name() if expediente.creado_por else 'Usuario desconocido'}\n"
                    f"Fecha de creación: {expediente.fecha_creacion.strftime('%Y-%m-%d') if hasattr(expediente, 'fecha_creacion') else 'No disponible'}\n"
                    f"Número SIMA: {getattr(expediente, 'numero_sima', 'No especificado')}\n"
                    f"Departamento: {departamento}\n"
                    f"Giro: {giro}\n"
                    f"Tipo de adquisición: {tipo_adquisicion}\n"
                    f"Fuente de financiamiento: {fuente_financiamiento}\n"
                    "\n=== DOCUMENTOS INCLUIDOS ===\n"
                )
                
                # Agregar lista de documentos
                for i, doc in enumerate(documentos, 1):
                    if doc.archivo:
                        nombre_archivo = os.path.basename(doc.archivo.name)
                        info_expediente += f"{i}. {nombre_archivo}\n"
                        # Agregar metadatos del documento si están disponibles
                        if hasattr(doc, 'fecha_subida'):
                            info_expediente += f"   - Subido el: {doc.fecha_subida.strftime('%Y-%m-%d')}\n"
                        if hasattr(doc, 'subido_por') and doc.subido_por:
                            info_expediente += f"   - Subido por: {doc.subido_por.get_full_name()}\n"
                        info_expediente += "\n"
                
                # Agregar el archivo de información al ZIP
                zipf.writestr("informacion_expediente.txt", info_expediente)
                archivos_agregados += 1
                logger.info("Archivo de información del expediente agregado al ZIP")
                
                # Agregar los documentos al ZIP
                for i, documento in enumerate(documentos, 1):
                    if not documento.archivo:
                        logger.warning(f"Documento {documento.id} no tiene archivo asociado")
                        continue
                            
                    try:
                        # Verificar si el archivo existe en el almacenamiento
                        if not documento.archivo.storage.exists(documento.archivo.name):
                            logger.warning(f"Archivo no encontrado: {documento.archivo.name}")
                            continue
                            
                        # Crear un nombre de archivo único para evitar colisiones
                        nombre_base = os.path.basename(documento.archivo.name)
                        nombre_archivo = f"documentos/{nombre_base}"  # Carpeta para organizar mejor los archivos
                        
                        # Leer el contenido del archivo y agregarlo al ZIP
                        try:
                            with documento.archivo.open('rb') as archivo:
                                contenido = archivo.read()
                                if not contenido:
                                    logger.warning(f"Archivo vacío: {documento.archivo.name}")
                                    continue
                                    
                                zipf.writestr(nombre_archivo, contenido)
                                archivos_agregados += 1
                                logger.info(f"Documento {i}/{len(documentos)} agregado al ZIP: {nombre_archivo}")
                                
                        except Exception as e:
                            logger.error(f"Error al leer el archivo {documento.archivo.name}: {str(e)}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error al procesar documento {documento.id}: {str(e)}")
                        continue
            
            if archivos_agregados == 0:
                buffer.close()
                logger.error("No se pudo agregar ningún archivo al ZIP")
                messages.error(request, 'No se pudo generar el archivo ZIP: no hay archivos válidos para descargar.')
                return redirect('expedientes:detalle', expediente_id=expediente_id)
            
            # Registrar en el historial
            try:
                HistorialExpediente.objects.create(
                    expediente=expediente,
                    usuario=request.user,
                    accion='descarga_expediente',
                    descripcion=f'Se descargaron {archivos_agregados} documentos del expediente.',
                    fecha=timezone.now()
                )
            except Exception as e:
                logger.error(f"Error al crear registro en el historial: {str(e)}")
            
            # Preparar la respuesta
            buffer.seek(0)
            zip_content = buffer.getvalue()
            buffer.close()
            
            # Obtener el estado actual del expediente
            estado_actual = getattr(expediente, 'estado_actual', 'en_proceso')
            
            # Obtener el nombre legible del estado
            if hasattr(expediente, 'get_estado_actual_display'):
                estado_nombre = expediente.get_estado_actual_display()
            else:
                # Si no existe get_estado_actual_display, intentar obtenerlo del diccionario de opciones
                estado_nombre = dict(Expediente.ESTADO_CHOICES).get(estado_actual, estado_actual.upper())
            
            # Crear el nombre del archivo con el estado actual
            estado_archivo = estado_nombre.upper().replace(' ', '_')
            response = HttpResponse(zip_content, content_type='application/zip')
            nombre_archivo = f"EXPEDIENTE_{expediente.numero_expediente}_{estado_archivo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
            response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
            response['Content-Length'] = len(zip_content)
            
            logger.info(f"Archivo ZIP generado correctamente: {nombre_archivo} ({len(zip_content)} bytes) - Estado: {estado_actual}")
            return response
            
        except Exception as e:
            buffer.close()
            logger.error(f"Error al crear el archivo ZIP: {str(e)}", exc_info=True)
            messages.error(request, f'Error al crear el archivo ZIP: {str(e)}')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
            
    except Exception as e:
        logger.error(f"Error en descargar_expediente: {str(e)}", exc_info=True)
        messages.error(request, 'Ocurrió un error inesperado al procesar la solicitud.')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
@login_required
@require_http_methods(["POST"])
def agregar_comentario(request, expediente_id, etapa):
    """
    Vista para agregar un comentario a una etapa específica de un expediente
    """
    try:
        # Obtener el expediente o devolver 404 si no existe
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos (usuario autenticado y con acceso al área del expediente o superusuario)
        if not (request.user.is_superuser or expediente.area in request.user.areas.all()):
            return JsonResponse({
                'success': False, 
                'error': 'No tienes permiso para agregar comentarios a este expediente.'
            }, status=403)
        
        # Obtener el texto del comentario del formulario
        texto = request.POST.get('texto', '').strip()
        if not texto:
            return JsonResponse({
                'success': False, 
                'error': 'El comentario no puede estar vacío.'
            }, status=400)
        
        # Validar la longitud del comentario
        if len(texto) > 1000:
            return JsonResponse({
                'success': False, 
                'error': 'El comentario no puede tener más de 1000 caracteres.'
            }, status=400)
        
        try:
            with transaction.atomic():
                # Crear el comentario
                comentario = ComentarioEtapa.objects.create(
                    expediente=expediente,
                    usuario=request.user,
                    etapa=etapa,
                    comentario=texto
                )
                
                # Registrar en el historial
                HistorialExpediente.crear_registro(
                    usuario=request.user,
                    accion='agregar_comentario',
                    modelo='ComentarioEtapa',
                    objeto_id=comentario.id,
                    detalles=f'Se agregó un comentario en la etapa {etapa}.'
                )
                
                # Si el comentario menciona un cambio de estado, actualizar el expediente
                if 'estado:' in texto.lower():
                    # Extraer el nuevo estado del comentario (ej: "estado:revision")
                    partes = texto.lower().split('estado:')
                    if len(partes) > 1:
                        nuevo_estado = partes[1].split()[0].strip()
                        if hasattr(Expediente, 'ESTADOS') and any(nuevo_estado == codigo for codigo, _ in Expediente.ESTADOS):
                            expediente.estado = nuevo_estado
                            expediente.save()
                
                # Obtener la URL para redirigir después de guardar
                redirect_url = reverse('expedientes:detalle', args=[expediente_id])
                
                return JsonResponse({
                    'success': True,
                    'comentario': {
                        'id': comentario.id,
                        'texto': comentario.texto,
                        'fecha_creacion': comentario.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                        'usuario': comentario.usuario.get_full_name() or comentario.usuario.username,
                        'etapa': comentario.etapa,
                        'es_propio': comentario.usuario == request.user
                    },
                    'redirect': redirect_url
                })
                
        except Exception as e:
            logger.error(f"Error al guardar el comentario: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Error al guardar el comentario: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error en agregar_comentario: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Ocurrió un error al procesar la solicitud.'
        }, status=500)
@csrf_exempt  # Exento de CSRF para permitir peticiones del servicio de escaneo
@require_http_methods(["POST"])
def subir_documento(request, expediente_id, etapa=None):
    """
    Vista para subir un documento a un expediente en una etapa específica
    
    Acepta subidas desde:
    - Usuarios autenticados (requiere @login_required)
    - Servicio de escaneo local (requiere token Bearer)
    
    Args:
        expediente_id: ID del expediente
        etapa: Etapa del expediente (opcional, se puede obtener del área)
    """
    # Importar el modelo Expediente aquí para evitar problemas de importación circular
    from .models import Expediente
    
    # Importar os y settings al inicio para que estén disponibles en todo el ámbito
    # (os y settings ya están importados globalmente, pero asegurémonos de que estén disponibles)
    import os
    from django.conf import settings
    
    # Verificar si viene del servicio de escaneo (por token Bearer)
    is_scanner_service = False
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    
    if auth_header.startswith("Bearer "):
        # Es una solicitud del servicio de escaneo
        token = auth_header.split(" ", 1)[1].strip()
        
        # Obtener token configurado
        expected_token = os.environ.get('SCANNER_UPLOAD_TOKEN', getattr(settings, 'SCANNER_UPLOAD_TOKEN', None))
        
        if expected_token and token == expected_token:
            is_scanner_service = True
            logger.info("Solicitud recibida del servicio de escaneo (token válido)")
        else:
            logger.warning("Intento de acceso con token inválido")
            return JsonResponse({'success': False, 'error': 'Token inválido'}, status=401)
    else:
        # Es una solicitud de usuario normal, requiere autenticación
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Autenticación requerida'}, status=401)
    
    try:
        # Obtener el expediente o devolver 404 si no existe
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos solo si NO es del servicio de escaneo
        if not is_scanner_service:
            # Verificar permisos (usuario autenticado y creador del expediente o superusuario)
            # Nota: El modelo Expediente puede no tener un campo 'area' directo
            tiene_permiso = request.user.is_superuser or expediente.creado_por == request.user
            if not tiene_permiso:
                # Verificar si el usuario tiene acceso al departamento del expediente
                if hasattr(expediente, 'departamento') and expediente.departamento:
                    # Aquí puedes agregar lógica adicional de permisos por departamento si es necesario
                    pass
                else:
                    messages.error(request, 'No tienes permiso para subir documentos a este expediente.')
                    return JsonResponse({'success': False, 'error': 'Permiso denegado'}, status=403)
        
        # Verificar que el expediente no esté en un estado que impida la edición
        if expediente.estado in ['aprobado', 'rechazado']:
            messages.error(request, 'No se pueden subir documentos a un expediente que ya ha sido aprobado o rechazado.')
            return JsonResponse({
                'success': False, 
                'error': 'Expediente no editable',
                'redirect': reverse('expedientes:detalle', args=[expediente_id])
            }, status=400)
        
        # Verificar que se haya enviado un archivo
        if 'documento' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se ha proporcionado ningún archivo'}, status=400)
        
        archivo = request.FILES['documento']
        
        # Validar el tipo de archivo
        extension_permitidas = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png']
        extension = archivo.name.split('.')[-1].lower()
        if extension not in extension_permitidas:
            return JsonResponse({
                'success': False, 
                'error': f'Tipo de archivo no permitido. Formatos aceptados: { ", ".join(extension_permitidas) }'
            }, status=400)
        
        # Validar tamaño del archivo (máximo 20MB)
        tamano_maximo = 20 * 1024 * 1024  # 20MB en bytes
        if archivo.size > tamano_maximo:
            return JsonResponse({
                'success': False, 
                'error': f'El archivo es demasiado grande. Tamaño máximo permitido: 20MB'
            }, status=400)
        
        # Obtener o crear el tipo de documento
        tipo_documento, creado = TipoDocumento.objects.get_or_create(
            nombre=request.POST.get('tipo_documento', 'Sin especificar'),
            defaults={
                'descripcion': f'Documento subido manualmente para {etapa}',
                'activo': True
            }
        )
        
        from .models import AreaTipoExpediente
        from django.core.validators import ValidationError
        
        try:
            # Obtener el ID del área desde el cuerpo de la petición si está disponible
            area_id = request.POST.get('area_id')
            if area_id is None:
                # Si no está en el cuerpo, usar el valor de la URL (compatibilidad con versiones anteriores)
                area_id = etapa
            
            # Validar que area_id no sea None antes de convertir
            if area_id is None:
                logger.error("ID de área no proporcionado")
                return JsonResponse({
                    'success': False, 
                    'error': 'ID de área no proporcionado. Por favor, especifique el área.'
                }, status=400)
            
            # Convertir a entero
            try:
                area_id = int(area_id)
            except (ValueError, TypeError) as e:
                logger.error(f"ID de área no válido: {area_id} - Error: {str(e)}")
                return JsonResponse({
                    'success': False, 
                    'error': f'ID de área no válido: {area_id}'
                }, status=400)
            
            # Obtener el área por su ID
            area_etapa = AreaTipoExpediente.objects.get(
                id=area_id,
                activa=True
            )
            
            # Obtener las opciones válidas para el campo etapa
            from .models import Expediente
            opciones_validas = [opcion[0] for opcion in Expediente.ESTADO_CHOICES]
            
            # Determinar el valor de etapa válido
            # Prioridad: 1) parámetro etapa de URL, 2) nombre del área, 3) valor por defecto
            etapa_valida = None
            
            # Primero intentar usar el parámetro etapa de la URL si es válido
            if etapa and etapa in opciones_validas:
                etapa_valida = etapa
                logger.debug(f"Usando etapa de URL: '{etapa_valida}'")
            
            # Si no hay etapa válida de la URL, intentar usar el nombre del área
            if not etapa_valida:
                etapa_valida = area_etapa.nombre.lower().replace(' ', '_')
                if etapa_valida not in opciones_validas:
                    logger.debug(f"El nombre del área '{area_etapa.nombre}' no es una opción válida para etapa.")
                    etapa_valida = None
            
            # Si aún no hay etapa válida, usar 'inicio' como valor por defecto seguro
            if not etapa_valida:
                etapa_valida = 'inicio'
                logger.debug(f"Usando etapa por defecto: '{etapa_valida}'")
            
            # Validar que etapa_valida sea realmente válida antes de continuar
            if etapa_valida not in opciones_validas:
                logger.error(f"Error crítico: etapa_valida '{etapa_valida}' no está en opciones válidas: {opciones_validas}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error: El valor de etapa "{etapa_valida}" no es válido. Opciones válidas: {", ".join(opciones_validas[:5])}...'
                }, status=400)
            
        except (ValueError, AreaTipoExpediente.DoesNotExist) as e:
            logger.error(f"No se encontró el área con ID {area_id} o no está activa: {str(e)}")
            # Obtener áreas disponibles para el tipo de expediente
            from .models import AreaTipoExpediente
            areas_disponibles = list(AreaTipoExpediente.objects.filter(
                activa=True
            ).values('id', 'nombre'))
            
            return JsonResponse({
                'success': False, 
                'error': 'Área no encontrada o no está activa.',
                'area_solicitada': area_id,
                'areas_disponibles': areas_disponibles
            }, status=400)
        # Crear el directorio de carga si no existe
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documentos', str(expediente_id))
        os.makedirs(upload_dir, exist_ok=True)
        # Crear el documento en la base de datos
        try:
            with transaction.atomic():
                # Obtener el nombre del documento del POST (obligatorio)
                nombre_documento = request.POST.get('nombre_documento', '').strip()
                if not nombre_documento:
                    return JsonResponse({
                        'success': False,
                        'error': 'El nombre del documento es obligatorio'
                    }, status=400)
                
                # Obtener usuario para subido_por
                # Si es del servicio de escaneo, usar o crear usuario 'servicio_local'
                if is_scanner_service:
                    try:
                        servicio_user = User.objects.get(username='servicio_local')
                    except User.DoesNotExist:
                        # Crear usuario del servicio si no existe
                        servicio_user = User.objects.create_user(
                            username='servicio_local',
                            email='servicio@local',
                            first_name='Servicio',
                            last_name='Escáner Local',
                            is_active=True,
                            is_staff=False
                        )
                        logger.info("Usuario 'servicio_local' creado automáticamente")
                    usuario_subida = servicio_user
                else:
                    usuario_subida = request.user
                
                # ============================================
                # INTEGRACIÓN CON GOOGLE DRIVE
                # ============================================
                drive_id = None
                path_temporal = None
                
                try:
                    from .drive_service import upload_to_drive, get_storage_usage
                    
                    # 1. VALIDACIÓN DE ESPACIO (Fase 4 y 5)
                    uso, limite = get_storage_usage()
                    if uso >= 14.5:  # Umbral de seguridad (14.5 GB de 15 GB)
                        return JsonResponse({
                            'success': False,
                            'error': 'Capacidad de almacenamiento llena. Contacte a sistemas.'
                        }, status=400)
                    
                    # 2. SUBIDA TEMPORAL Y ENVÍO A DRIVE
                    # Guardamos el archivo temporalmente para poder enviarlo a Drive
                    import tempfile
                    fecha = timezone.now()
                    ext = os.path.splitext(archivo.name)[1] if '.' in archivo.name else ''
                    filename_upload = f"{expediente.numero_expediente}_{fecha.strftime('%Y%m%d_%H%M%S')}{ext}"
                    
                    # Crear archivo temporal
                    archivo.seek(0)  # Asegurar que estamos al inicio del archivo
                    archivo_content = archivo.read()
                    
                    # Guardar en archivo temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                        temp_file.write(archivo_content)
                        path_temporal = temp_file.name
                    
                    # ID de la carpeta que compartiste con el robot (configurar en settings o variable de entorno)
                    FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
                    
                    if FOLDER_ID:
                        # Subir a Drive
                        drive_id = upload_to_drive(path_temporal, archivo.name, FOLDER_ID)
                        logger.info(f"Archivo subido a Google Drive con ID: {drive_id}")
                    else:
                        logger.warning("GOOGLE_DRIVE_FOLDER_ID no configurado, el archivo no se subirá a Drive")
                        
                except Exception as drive_error:
                    logger.error(f"Error al subir archivo a Google Drive: {str(drive_error)}", exc_info=True)
                    # Continuar con el guardado local aunque falle Drive
                    # No fallar la subida completa si Drive falla
                
                # Guardar el archivo físicamente ANTES de crear el modelo (backup local)
                # Esto asegura que el archivo exista en el disco antes de indexarlo
                fecha = timezone.now()
                ext = os.path.splitext(archivo.name)[1] if '.' in archivo.name else ''
                filename_upload = f"{expediente.numero_expediente}_{fecha.strftime('%Y%m%d_%H%M%S')}{ext}"
                upload_path = os.path.join('expedientes', str(fecha.year), str(fecha.month), filename_upload)
                
                # Leer el contenido del archivo (si no se leyó antes)
                if not archivo_content:
                    archivo.seek(0)
                    archivo_content = archivo.read()
                
                # Guardar el archivo usando default_storage (backup local)
                saved_path = default_storage.save(upload_path, ContentFile(archivo_content))
                logger.info(f"Archivo guardado físicamente en: {saved_path}")
                
                # Verificar que el archivo se guardó correctamente
                if not default_storage.exists(saved_path):
                    logger.error(f"Error: El archivo no se guardó correctamente en {saved_path}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Error al guardar el archivo en el servidor'
                    }, status=500)
                
                # Limpiar archivo temporal si existe
                if path_temporal and os.path.exists(path_temporal):
                    try:
                        os.remove(path_temporal)
                        logger.info(f"Archivo temporal eliminado: {path_temporal}")
                    except Exception as cleanup_error:
                        logger.warning(f"No se pudo eliminar archivo temporal: {str(cleanup_error)}")
                
                # Crear una instancia del modelo con la ruta del archivo guardado
                documento = DocumentoExpediente(
                    expediente=expediente,
                    area=area_etapa,
                    etapa=etapa_valida,  # Usamos el valor validado
                    nombre_documento=nombre_documento,
                    archivo=saved_path,  # Usar la ruta del archivo guardado (backup local)
                    archivo_drive_id=drive_id,  # ID del archivo en Google Drive
                    subido_por=usuario_subida,
                    tamano_archivo=len(archivo_content),
                    tipo_archivo=archivo.content_type,
                    descripcion=request.POST.get('descripcion', '').strip(),
                    validado=False
                )
                
                # Guardar el documento
                try:
                    documento.full_clean()  # Validar el modelo antes de guardar
                except ValidationError as ve:
                    logger.error(f"Error de validación al crear documento: {str(ve)}", exc_info=True)
                    error_dict = {}
                    if hasattr(ve, 'error_dict'):
                        error_dict = {k: [str(e) for e in v] for k, v in ve.error_dict.items()}
                    elif hasattr(ve, 'message_dict'):
                        error_dict = {k: [str(e) for e in v] for k, v in ve.message_dict.items()}
                    else:
                        error_dict = {'__all__': [str(ve)]}
                    
                    return JsonResponse({
                        'success': False,
                        'error': f'Error de validación: {str(ve)}',
                        'errors': error_dict
                    }, status=400)
                
                try:
                    documento.save()
                    logger.info(f"Documento guardado exitosamente: ID {documento.id}")
                    
                    # Indexar el documento manualmente después de guardarlo
                    # Esto asegura que el archivo esté completamente guardado antes de indexar
                    try:
                        from .search_utils import index_document
                        import time
                        # Esperar un momento para asegurar que el archivo esté completamente guardado
                        time.sleep(0.5)
                        # Refrescar el documento desde la BD para asegurar que tiene todos los datos
                        documento.refresh_from_db()
                        logger.info(f"Intentando indexar documento {documento.id} manualmente...")
                        # Intentar indexar
                        if index_document(documento):
                            logger.info(f"✓ Documento {documento.id} indexado correctamente después de guardar")
                        else:
                            logger.warning(f"⚠ No se pudo indexar documento {documento.id} inmediatamente, se intentará con el signal")
                    except Exception as index_error:
                        logger.error(f"✗ Error al indexar documento {documento.id} manualmente: {str(index_error)}", exc_info=True)
                        # No fallar la subida si la indexación falla, el signal lo intentará después
                        
                except Exception as save_error:
                    logger.error(f"Error al guardar documento: {str(save_error)}", exc_info=True)
                    return JsonResponse({
                        'success': False,
                        'error': f'Error al guardar el documento: {str(save_error)}'
                    }, status=500)
                
                # Registrar en el historial
                HistorialExpediente.objects.create(
                    expediente=expediente,
                    usuario=usuario_subida,
                    accion='subir_documento' if not is_scanner_service else 'subir_documento_escaneado',
                    descripcion=f'Se subió el documento {archivo.name} en la etapa {etapa}.' + (' (Escaneado automáticamente)' if is_scanner_service else ''),
                    etapa_nueva=etapa
                )
                
                # Actualizar la fecha de actualización del expediente
                expediente.fecha_actualizacion = timezone.now()
                expediente.save(update_fields=['fecha_actualizacion'])
                
                # Verificar si se completó la etapa/área
                try:
                    # Usar el area_etapa que ya se obtuvo anteriormente (línea 749)
                    # Verificar si hay documentos en esta área
                    tiene_documentos = expediente.documentos.filter(area=area_etapa).exists()
                    
                    # Actualizar el estado de la etapa si el modelo EtapaExpediente existe
                    try:
                        from .models import EtapaExpediente
                        etapa_obj, created = EtapaExpediente.objects.update_or_create(
                            expediente=expediente,
                            nombre_etapa=area_etapa.nombre,
                            defaults={
                                'completada': tiene_documentos,
                                'fecha_completada': timezone.now() if tiene_documentos else None,
                                'completada_por': usuario_subida if tiene_documentos else None,
                                'notas': f'Documento subido: {archivo.name}' if tiene_documentos else ''
                            }
                        )
                    except Exception as etapa_error:
                        # Si el modelo EtapaExpediente no existe o hay un error, solo loguear
                        logger.debug(f"No se pudo actualizar EtapaExpediente: {str(etapa_error)}")
                    
                except Exception as e:
                    logger.error(f"Error al actualizar el estado de la etapa: {str(e)}", exc_info=True)
                
                # Registrar éxito
                logger.info(f"Documento {archivo.name} subido exitosamente para el expediente {expediente_id}")
                
                # Recalcular el progreso usando el método del modelo
                try:
                    progreso_info = expediente.get_progreso()
                    if isinstance(progreso_info, dict):
                        progreso = progreso_info.get('porcentaje', 0)
                        etapas_completadas = progreso_info.get('completadas', 0)
                        total_etapas = progreso_info.get('total', 0)
                    else:
                        # Método alternativo: calcular directamente
                        areas_etapas = expediente.get_areas_configuradas()
                        total_etapas = areas_etapas.count()
                        etapas_completadas = 0
                        for area in areas_etapas:
                            try:
                                if area.etapa_completada(expediente):
                                    etapas_completadas += 1
                            except Exception:
                                continue
                        progreso = int((etapas_completadas / total_etapas) * 100) if total_etapas > 0 else 0
                    
                    # Actualizar el estado si el progreso es 100%
                    update_fields = ['fecha_actualizacion', 'progreso']
                    if progreso >= 100 and expediente.estado != 'completo':
                        expediente.estado = 'completo'
                        # También actualizar estado_actual a 'completado' para que se muestre correctamente en la lista
                        if expediente.estado_actual != 'completado':
                            expediente.estado_actual = 'completado'
                            update_fields.append('estado_actual')
                        update_fields.append('estado')
                        logger.info(f"[COMPLETO] Expediente {expediente_id} marcado como completo después de subir documento (progreso 100%)")
                    
                    expediente.progreso = progreso
                    expediente.fecha_actualizacion = timezone.now()
                    expediente.save(update_fields=update_fields)
                except Exception as progreso_error:
                    logger.error(f"Error al recalcular progreso: {str(progreso_error)}", exc_info=True)
                    # Continuar aunque falle el cálculo del progreso
                    progreso = getattr(expediente, 'progreso', 0)
                    etapas_completadas = 0
                    total_etapas = 0
                
                # Preparar respuesta
                try:
                    # Asegurar que todas las variables estén definidas
                    if 'progreso' not in locals():
                        progreso = getattr(expediente, 'progreso', 0)
                    if 'etapas_completadas' not in locals():
                        etapas_completadas = 0
                    if 'total_etapas' not in locals():
                        total_etapas = 0
                    if 'tiene_documentos' not in locals():
                        tiene_documentos = expediente.documentos.filter(area=area_etapa).exists()
                    
                    # Obtener nombre del área
                    nombre_area = ''
                    if area_etapa:
                        nombre_area = getattr(area_etapa, 'titulo', getattr(area_etapa, 'nombre', 'Sin nombre'))
                    
                    # Obtener URL del archivo de forma segura
                    # Priorizar Google Drive si tiene archivo_drive_id
                    archivo_url = ''
                    try:
                        if documento.archivo_drive_id:
                            # Usar la vista de Drive para ver el documento
                            from django.urls import reverse
                            archivo_url = reverse('expedientes:ver_documento_drive', args=[documento.id])
                        elif documento.archivo:
                            archivo_url = documento.archivo.url
                    except Exception as url_error:
                        logger.warning(f"No se pudo obtener URL del archivo: {str(url_error)}")
                        archivo_url = ''
                    
                    response_data = {
                        'success': True,
                        'documento': {
                            'id': documento.id,
                            'nombre': documento.nombre_documento,
                            'url': archivo_url,
                            'fecha_subida': documento.fecha_subida.strftime('%d/%m/%Y %H:%M') if documento.fecha_subida else '',
                            'subido_por': documento.subido_por.get_full_name() if documento.subido_por else 'Usuario desconocido',
                            'tipo': documento.tipo_archivo if documento.tipo_archivo else 'Sin especificar',
                            'tamano': f'{(documento.tamano_archivo / 1024):.1f} KB' if documento.tamano_archivo else '0 KB',
                            'estado': 'Validado' if documento.validado else 'Pendiente de validar'
                        },
                        'progreso': progreso,
                        'etapas_completadas': etapas_completadas,
                        'total_etapas': total_etapas,
                        'etapa_actual': nombre_area,
                        'etapa_completada': tiene_documentos
                    }
                    
                    return JsonResponse(response_data)
                except Exception as response_error:
                    logger.error(f"Error al preparar respuesta: {str(response_error)}", exc_info=True)
                    # Aún así devolver una respuesta básica de éxito
                    return JsonResponse({
                        'success': True,
                        'message': 'Documento subido exitosamente',
                        'documento_id': documento.id
                    })
                
        except ValidationError as e:
            logger.error(f"Error de validación al guardar el documento {archivo.name}: {str(e)}", exc_info=True)
            error_dict = {}
            if hasattr(e, 'error_dict'):
                error_dict = {k: [str(err) for err in v] for k, v in e.error_dict.items()}
            elif hasattr(e, 'message_dict'):
                error_dict = {k: [str(err) for err in v] for k, v in e.message_dict.items()}
            else:
                error_dict = {'__all__': [str(e)]}
            
            return JsonResponse({
                'success': False, 
                'error': f'Error de validación: {str(e)}',
                'errors': error_dict
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error al guardar el documento {archivo.name}: {str(e)}", exc_info=True)
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Traceback completo al guardar documento: {error_traceback}")
            return JsonResponse({
                'success': False, 
                'error': f'Error al procesar el archivo: {str(e)}',
                'type': type(e).__name__,
                'details': str(e) if settings.DEBUG else None
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error en subir_documento: {str(e)}", exc_info=True)
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Traceback completo: {error_traceback}")
        return JsonResponse({
            'success': False, 
            'error': f'Error al procesar la solicitud: {str(e)}',
            'type': type(e).__name__,
            'details': str(e) if settings.DEBUG else None
        }, status=500)
@login_required
def detalle_expediente(request, expediente_id):
    """
    Vista para ver el detalle de un expediente
    """
    logger.info(f"=== INICIO detalle_expediente ===")
    logger.info(f"Expediente ID: {expediente_id}")
    logger.info(f"Usuario: {request.user.get_full_name()} (ID: {request.user.id})")
    
    try:
        # Obtener el expediente con relaciones relacionadas para optimización de consultas
        expediente = get_object_or_404(
            Expediente.objects.select_related(
                'creado_por',
                'departamento'
            ).prefetch_related(
                'documentos',
                'documentos__subido_por',
                'historial'
            ),
            id=expediente_id
        )
        
        logger.info(f"Expediente encontrado: {expediente.numero_expediente}")
        logger.info(f"Tipo: {expediente.tipo_expediente}, Subtipo: {getattr(expediente, 'subtipo_expediente', 'No definido')}")
        
        # Verificar permisos - todos los usuarios autenticados pueden ver expedientes
        if not puede_ver_expedientes(request.user):
            logger.warning(f"Usuario {request.user.id} no tiene permiso para ver expedientes")
            messages.error(request, 'No tienes permiso para ver expedientes.')
            return redirect('expedientes:lista')
        
        # Inicializar variable de áreas (se llenará más adelante con la consulta completa)
        areas = []
        
        # Obtener documentos agrupados por tipo de archivo
        documentos_por_tipo = {}
        # Agrupar documentos por área
        documentos_por_area = {}
        for doc in expediente.documentos.all():
            # Agrupar por tipo de archivo
            tipo = doc.tipo_archivo or 'sin_tipo'
            if tipo not in documentos_por_tipo:
                documentos_por_tipo[tipo] = []
            documentos_por_tipo[tipo].append(doc)
            
            # Agrupar por área
            if hasattr(doc, 'area'):
                area_id = doc.area.id if doc.area else 'sin_area'
                if area_id not in documentos_por_area:
                    documentos_por_area[area_id] = []
                documentos_por_area[area_id].append(doc)
        
        # Obtener comentarios
        comentarios = ComentarioArea.objects.filter(
            expediente=expediente
        ).select_related('usuario').order_by('-fecha_creacion')
        
        # Obtener etapas pendientes
        tareas_pendientes = EtapaExpediente.objects.filter(
            expediente=expediente,
            completada=False
        ).select_related('completada_por').order_by('nombre_etapa')
        
        # Obtener historial de cambios
        historial = expediente.historial.all().order_by('-fecha')
        
        # Obtener archivos adjuntos de forma segura
        try:
            archivos_adjuntos = expediente.archivos_adjuntos.all() if hasattr(expediente, 'archivos_adjuntos') else []
        except Exception as e:
            logger.warning(f"Error al obtener archivos adjuntos: {str(e)}")
            archivos_adjuntos = []
        
        # Cargar áreas según tipo y subtipo
        areas_query = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            activa=True
        )

        # Si el expediente tiene subtipo, filtramos correctamente
        # IMPORTANTE: Buscar áreas con ambos formatos (con y sin prefijo 'licitacion_')
        if expediente.subtipo_expediente:
            # Normalizar el subtipo
            subtipo_exp = str(expediente.subtipo_expediente).strip().lower()
            
            # Lista de posibles formatos del subtipo para buscar
            subtipos_a_buscar = [subtipo_exp]
            
            # Si el subtipo no tiene prefijo 'licitacion_', agregar la versión con prefijo
            if expediente.tipo_expediente == 'licitacion' and not subtipo_exp.startswith('licitacion_'):
                subtipos_a_buscar.append(f'licitacion_{subtipo_exp}')
            
            # Si el subtipo tiene prefijo 'licitacion_', agregar la versión sin prefijo
            if expediente.tipo_expediente == 'licitacion' and subtipo_exp.startswith('licitacion_'):
                subtipos_a_buscar.append(subtipo_exp.replace('licitacion_', ''))
            
            # Eliminar duplicados
            subtipos_a_buscar = list(set(subtipos_a_buscar))
            
            # Construir query para buscar áreas con cualquiera de los formatos
            subtipo_query = Q()
            for st in subtipos_a_buscar:
                subtipo_query |= Q(subtipo_expediente=st)
            
            # También incluir áreas generales (sin subtipo)
            areas_query = areas_query.filter(
                subtipo_query | 
                Q(subtipo_expediente__isnull=True) |
                Q(subtipo_expediente='')
            )
        else:
            # Si NO tiene subtipo, traer solo las áreas sin subtipo
            areas_query = areas_query.filter(
                Q(subtipo_expediente__isnull=True) |
                Q(subtipo_expediente='')
            )
        
        # Ordenar las áreas
        areas_etapas = areas_query.order_by('orden', 'titulo')
        logger.info(f"Áreas encontradas: {areas_etapas.count()}")
        
        # Obtener el subtipo para el log
        subtipo_log = getattr(expediente, 'subtipo_expediente', None)
        logger.info(f"Áreas/etapas encontradas: {areas_etapas.count()} para tipo: {expediente.tipo_expediente}, subtipo: {subtipo_log or 'Ninguno'}")
        
        # Inicializar el diccionario de documentos por área
        documentos_por_area = {}
        
        # Obtener todos los documentos del expediente agrupados por área
        documentos_expediente = expediente.documentos.all().select_related('area')
        
        # Agrupar documentos por área
        for doc in documentos_expediente:
            if doc.area_id not in documentos_por_area:
                documentos_por_area[doc.area_id] = []
            documentos_por_area[doc.area_id].append(doc)
        
        # Asegurarse de que todas las áreas tengan una entrada en el diccionario
        for area in areas_etapas:
            if area.id not in documentos_por_area:
                documentos_por_area[area.id] = []
        
        # Obtener departamentos para el formulario
        departamentos = Departamento.objects.filter(activo=True).order_by('nombre')
        
        # Verificar permisos adicionales según el rol del usuario
        # Visualizador: solo puede ver, no puede editar, eliminar ni rechazar
        # Editor: puede editar, pero no eliminar ni rechazar
        # Administrador: puede hacer todo
        
        puede_editar_exp = puede_editar_expedientes(request.user)
        puede_eliminar_exp = puede_eliminar_expedientes(request.user)
        puede_adm_sistema = puede_administrar_sistema(request.user)
        
        # Solo visualizador: no puede hacer nada más que ver
        es_visual = es_visualizador(request.user)
        
        # Puede editar solo si tiene permiso de editar expedientes Y no es solo visualizador
        puede_editar = puede_editar_exp and not es_visual
        
        # Puede rechazar solo si es administrador
        puede_rechazar = puede_adm_sistema
        
        # Puede eliminar solo si tiene permiso Y no es visualizador
        puede_eliminar = puede_eliminar_exp and not es_visual and (
            request.user.is_superuser or 
            (expediente.creado_por == request.user and expediente.estado != 'aprobado')
        )
        
        # Obtener usuarios asignables (solo superusuarios o personal autorizado)
        usuarios_asignables = User.objects.filter(
            is_active=True,
            is_staff=True
        ).order_by('first_name', 'last_name')
        
        # Obtener departamentos para el formulario de transferencia
        departamentos = Departamento.objects.filter(activo=True).order_by('nombre')
        
        # Inicializar lista vacía de plantillas de documentos
        plantillas_documentos = []
        
        # Obtener el estado actual del expediente
        estado_actual = expediente.estado if hasattr(expediente, 'estado') else 'en_proceso'
        
        # Inicializar variables de progreso
        progreso = 0
        total_etapas = areas_etapas.count()
        etapas_completadas = 0
        
        # Solo calcular el progreso si el expediente no está en un estado final
        if estado_actual not in ['rechazado', 'completado', 'aprobado', 'finalizado']:
            # Obtener documentos del expediente para verificar el progreso
            documentos_expediente = list(expediente.documentos.all().values_list('area_id', flat=True).distinct())
            
            # Verificar cada área/etapa
            for area in areas_etapas:
                # Verificar si hay documentos en esta área
                if area.id in documentos_expediente:
                    etapas_completadas += 1
                    continue
                # Si no hay documentos, verificar si tiene una función personalizada
                if hasattr(area, 'etapa_completada') and callable(area.etapa_completada):
                    if area.etapa_completada(expediente):
                        etapas_completadas += 1
            
            if total_etapas > 0:
                progreso = min(100, int((etapas_completadas / total_etapas) * 100))
                
                # Actualizar el estado según el progreso
                if progreso >= 100 and expediente.estado != 'completo':
                    with transaction.atomic():
                        expediente.estado = 'completo'  # Usar 'completo' según ESTADOS_EXPEDIENTE
                        # También actualizar estado_actual a 'completado' para que se muestre correctamente en la lista
                        if expediente.estado_actual != 'completado':
                            expediente.estado_actual = 'completado'
                        expediente.fecha_actualizacion = timezone.now()
                        expediente.save(update_fields=['estado', 'estado_actual', 'fecha_actualizacion'])
                        logger.info(f"[COMPLETO] Expediente {expediente_id} marcado como completo (progreso 100%)")
                elif expediente.estado == 'rechazado' and estado_actual != 'rechazado':
                    # Si por alguna razón el estado es 'rechazado' pero no está marcado como tal
                    expediente.estado = 'rechazado'
                    # No actualizamos estado_actual ya que tiene su propio flujo
                    expediente.save(update_fields=['estado'])
            
            logger.info(f"Progreso del expediente: {progreso}% ({etapas_completadas}/{total_etapas} etapas completadas). Estado actual: {expediente.estado}")
        elif estado_actual == 'rechazado':
            # Si está rechazado, forzar el progreso a 0
            progreso = 0
            total_etapas = 0
            etapas_completadas = 0
        
        # Inicializar valores_areas como un diccionario vacío
        valores_areas = {}
        
        # Preparar contexto
        # Determinar si se debe mostrar el campo de fuente de financiamiento
        # Mostrar para: adjudicacion_directa, compra_directa, concurso_invitacion
        mostrar_fuente = expediente.tipo_expediente in ['adjudicacion_directa', 'compra_directa', 'concurso_invitacion']
        
        # Obtener el tipo de expediente para usar en la plantilla
        tipo_expediente = getattr(expediente, 'tipo_expediente', '')
        
        context = {
            'expediente': expediente,
            'tipo': tipo_expediente,
            'tipo_nombre': expediente.get_tipo_expediente_display(),
            'titulo': f'Expediente {expediente.numero_expediente}',
            'departamentos': departamentos,
            'mostrar_fuente_financiamiento': mostrar_fuente,
            'subtipo': getattr(expediente, 'subtipo_expediente', None),
            'estado_actual': estado_actual,
            'estado_display': expediente.get_estado_display() if hasattr(expediente, 'get_estado_display') else 'En Proceso',
            'estados_disponibles': Expediente.ESTADOS if hasattr(Expediente, 'ESTADOS') else [],
            'progreso': progreso,
            'etapas_completadas': etapas_completadas,
            'total_etapas': total_etapas,
            'progreso_detalle': {  
                'completadas': etapas_completadas,
                'total': total_etapas
            },
            'valores_areas': valores_areas,
            'documentos_por_tipo': documentos_por_tipo,
            'comentarios': comentarios,
            'tareas_pendientes': tareas_pendientes,
            'historial': historial,
            'archivos_adjuntos': archivos_adjuntos,
            'areas_etapas': areas_etapas,
            'documentos_por_area': documentos_por_area,  # Agregar documentos agrupados por área
            'puede_editar': puede_editar,
            'puede_rechazar': puede_rechazar and estado_actual != 'rechazado',  # No permitir rechazar si ya está rechazado
            'puede_eliminar': puede_eliminar,
            'usuarios_asignables': usuarios_asignables,
            'es_rechazado': estado_actual == 'rechazado',
            'motivo_rechazo': getattr(expediente, 'razon_rechazo', None) or getattr(expediente, 'motivo_rechazo', ''),
            # Variables de permisos según rol
            'puede_crear_expedientes': puede_crear_expedientes(request.user),
            'puede_administrar_sistema': puede_administrar_sistema(request.user),
            'puede_aprobar_usuarios': puede_aprobar_usuarios(request.user),
            'es_visualizador': es_visualizador(request.user),
            'es_editor': es_editor(request.user),
            'es_administrador': es_administrador(request.user),
        }
        
        logger.info("Renderizando plantilla...")
        response = render(request, 'digitalizacion/expedientes/detalle_expediente.html', context)
        response['Content-Type'] = 'text/html; charset=utf-8'
        response['Content-Language'] = 'es-mx'
        return response
        
    except Exception as e:
        logger.error(f"Error en detalle_expediente: {str(e)}", exc_info=True)
        messages.error(request, 'Ocurrió un error al cargar el expediente.')
        return redirect('expedientes:lista')

@login_required
def eliminar_expediente(request, expediente_id):
    """
    Vista para eliminar un expediente existente.
    Solo disponible para superusuarios o el creador del expediente.
    No se pueden eliminar expedientes aprobados.
    """
    from django.http import JsonResponse
    
    # Detectar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    logger.info(f"=== INICIO eliminar_expediente ===")
    logger.info(f"Expediente ID: {expediente_id}")
    logger.info(f"Usuario: {request.user.get_full_name()} (ID: {request.user.id})")
    logger.info(f"Es AJAX: {is_ajax}")
    
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos (solo superusuarios o el creador pueden eliminar)
        if not (request.user.is_superuser or expediente.creado_por == request.user):
            logger.warning(f"Usuario {request.user.id} no tiene permiso para eliminar el expediente {expediente_id}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permiso para eliminar este expediente.'
                }, status=403)
            messages.error(request, 'No tienes permiso para eliminar este expediente.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Verificar que el expediente no esté en un estado que impida la eliminación
        if expediente.estado == 'aprobado':
            logger.warning(f"Intento de eliminar expediente aprobado {expediente_id}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede eliminar un expediente que ya ha sido aprobado.'
                }, status=400)
            messages.error(request, 'No se puede eliminar un expediente que ya ha sido aprobado.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Eliminar el expediente con manejo de documentos
        with transaction.atomic():
            # Guardar información para el historial antes de eliminar
            expediente_info = {
                'numero': expediente.numero_expediente,
                'tipo': expediente.tipo_expediente if hasattr(expediente, 'tipo_expediente') else getattr(expediente, 'tipo', ''),
                'creado_por': expediente.creado_por.get_full_name() if expediente.creado_por else 'Usuario desconocido',
                'fecha_creacion': expediente.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
                'estado': expediente.estado
            }
            
            # Obtener documentos asociados para eliminación física de archivos
            documentos = DocumentoExpediente.objects.filter(expediente=expediente)
            documentos_info = []
            for doc in documentos:
                try:
                    doc_info = {
                        'id': doc.id,
                        'nombre': getattr(doc, 'nombre_documento', getattr(doc, 'nombre_archivo', 'Sin nombre')),
                        'tipo': doc.tipo_documento.nombre if hasattr(doc, 'tipo_documento') and doc.tipo_documento else 'Sin tipo',
                        'tamano': doc.archivo.size if doc.archivo and hasattr(doc.archivo, 'size') else 0
                    }
                    documentos_info.append(doc_info)
                except Exception as e:
                    logger.error(f"Error al obtener info del documento {doc.id}: {str(e)}")
            
            # Eliminar documentos físicos
            for doc in documentos:
                if doc.archivo and hasattr(doc.archivo, 'path'):
                    try:
                        if os.path.isfile(doc.archivo.path):
                            os.remove(doc.archivo.path)
                    except Exception as e:
                        logger.error(f"Error al eliminar archivo {doc.archivo.path}: {str(e)}")
            
            # Registrar en el historial antes de eliminar
            try:
                HistorialExpediente.crear_registro(
                    usuario=request.user,
                    accion='eliminar_expediente',
                    modelo='Expediente',
                    objeto_id=expediente.id,
                    detalles={
                        'expediente': expediente_info,
                        'documentos_eliminados': documentos_info,
                        'total_documentos': len(documentos_info),
                        'espacio_liberado': sum(doc.get('tamano', 0) for doc in documentos_info)
                    }
                )
            except Exception as e:
                logger.error(f"Error al crear registro de historial: {str(e)}")
            
            # Eliminar el expediente (esto también eliminará los documentos en CASCADE)
            numero_expediente = expediente.numero_expediente
            expediente.delete()
        
        logger.info(f"Expediente {numero_expediente} eliminado exitosamente")
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'El expediente {numero_expediente} ha sido eliminado correctamente.',
                'redirect': '/expedientes/lista/'
            })
        
        messages.success(request, f'El expediente {numero_expediente} ha sido eliminado correctamente.')
        return redirect('expedientes:lista')
        
    except Exception as e:
        logger.error(f"Error al eliminar expediente {expediente_id}: {str(e)}", exc_info=True)
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': f'Ocurrió un error al intentar eliminar el expediente: {str(e)}'
            }, status=500)
        messages.error(request, 'Ocurrió un error al intentar eliminar el expediente.')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
@login_required
@require_http_methods(["POST"])
def rechazar_expediente(request, expediente_id):
    """
    Vista para rechazar un expediente
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    def json_response(success, message, redirect_url=None):
        response_data = {'success': success, 'message': message}
        if redirect_url:
            response_data['redirect'] = redirect_url
        return JsonResponse(response_data)
    
    try:
        with transaction.atomic():
            # Obtener el expediente con bloqueo para evitar condiciones de carrera
            expediente = Expediente.objects.select_for_update().get(id=expediente_id)
            
            # Verificar permisos (solo superusuarios o usuarios con permiso específico pueden rechazar)
            if not (request.user.is_superuser or request.user.has_perm('digitalizacion.rechazar_expediente')):
                error_msg = 'No tienes permiso para rechazar este expediente.'
                if is_ajax:
                    return json_response(False, error_msg)
                messages.error(request, error_msg)
                return redirect('expedientes:detalle', pk=expediente_id)
            
            # Verificar que el expediente no esté ya rechazado
            if expediente.estado == 'rechazado':
                warning_msg = 'Este expediente ya ha sido rechazado anteriormente.'
                if is_ajax:
                    return json_response(False, warning_msg)
                messages.warning(request, warning_msg)
                return redirect('expedientes:detalle', pk=expediente_id)
                
            # Obtener la razón del rechazo (opcional, usar razón por defecto si no se proporciona)
            razon_rechazo = request.POST.get('razon_rechazo', '').strip()
            if not razon_rechazo:
                razon_rechazo = 'Expediente rechazado desde el sistema'
            
            # Guardar el estado anterior para el historial
            estado_anterior = expediente.estado
            
            # Actualizar el estado del expediente
            expediente.estado = 'rechazado'
            expediente.estado_actual = 'rechazado'
            
            # Solo actualizar campos que existen en el modelo
            if hasattr(expediente, 'fecha_rechazo'):
                expediente.fecha_rechazo = timezone.now()
            if hasattr(expediente, 'usuario_rechazo'):
                expediente.usuario_rechazo = request.user
            if hasattr(expediente, 'razon_rechazo'):
                expediente.razon_rechazo = razon_rechazo
            
            # Guardar los cambios
            expediente.save()
            
            # Forzar recarga desde la base de datos
            expediente.refresh_from_db()
            logger.info(f"Expediente {expediente.numero_expediente} rechazado. Estado actual: {expediente.estado}")
            
            # Registrar en el historial
            HistorialExpediente.objects.create(
                expediente=expediente,
                usuario=request.user,
                accion='rechazo',
                descripcion=f'Expediente rechazado. Razón: {razon_rechazo}. Estado anterior: {estado_anterior}',
                etapa_anterior=estado_anterior,
                etapa_nueva='rechazado'
            )
            
            # Enviar notificación
            if expediente.creado_por and expediente.creado_por != request.user:
                try:
                    Notificacion.objects.create(
                        usuario=expediente.creado_por,
                        titulo=f'Expediente {expediente.numero_expediente} Rechazado',
                        mensaje=f'Tu expediente ha sido rechazado. Razón: {razon_rechazo}',
                        tipo='rechazo',
                        url=reverse('expedientes:detalle', args=[expediente.id])
                    )
                except Exception as e:
                    logger.error(f"Error al crear notificación: {str(e)}")
            
            success_msg = 'El expediente ha sido rechazado correctamente.'
            if is_ajax:
                return json_response(True, success_msg, reverse('expedientes:detalle', args=[expediente_id]))
                
            messages.success(request, success_msg)
            return redirect('expedientes:detalle', expediente_id=expediente_id)
            
    except Exception as e:
        logger.error(f"Error en rechazar_expediente: {str(e)}", exc_info=True)
        error_msg = 'Ocurrió un error inesperado al procesar la solicitud.'
        if is_ajax:
            return json_response(False, error_msg)
        messages.error(request, error_msg)
        return redirect('expedientes:lista')
@login_required
def obtener_documentos_expediente_api(request, expediente_id):
    """
    Vista API para obtener los documentos de un expediente en formato JSON
    """
    from django.http import JsonResponse
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos - todos los usuarios autenticados pueden ver documentos
        if not puede_ver_expedientes(request.user):
            logger.warning(f'Intento de acceso no autorizado a documentos del expediente {expediente_id} por el usuario {request.user.username}')
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para ver documentos de expedientes'}, 
                status=403
            )
        
        # Obtener documentos del expediente
        try:
            documentos = expediente.documentos.all().select_related('area', 'subido_por')
            
            # Formatear los documentos
            documentos_data = []
            for doc in documentos:
                try:
                    # Debug: Mostrar campos del modelo
                    print('\n📄 Documento:', doc.id)
                    for field in doc._meta.fields:
                        valor = getattr(doc, field.name, None)
                        print(f"  {field.name} → {type(valor).__name__} = {valor}")
                    
                    doc_data = {
                        'id': doc.id,
                        'nombre': doc.nombre_documento,
                        'tipo': os.path.splitext(doc.archivo.name)[1].lstrip('.').lower() if doc.archivo else '',
                        'fecha_subida': timezone.localtime(doc.fecha_subida).strftime('%Y-%m-%d %H:%M:%S') if doc.fecha_subida else None,
                        'tamano': doc.tamano_archivo if doc.tamano_archivo is not None else (doc.archivo.size if doc.archivo else 0),
                        'url': doc.archivo.url if doc.archivo else None,
                        'area': {
                            'id': doc.area.id,
                            'nombre': doc.area.nombre
                        } if doc.area else None,
                        'subido_por': {
                            'id': doc.subido_por.id,
                            'username': doc.subido_por.username,
                            'nombre_completo': doc.subido_por.get_full_name() or doc.subido_por.username
                        } if doc.subido_por else None
                    }
                    documentos_data.append(doc_data)
                except Exception as e:
                    logger.error(f'Error al procesar documento {getattr(doc, "id", "desconocido")}: {str(e)}')
                    continue
            
            return JsonResponse({
                'success': True,
                'documentos': documentos_data,
                'total': len(documentos_data)
            })
            
        except Exception as e:
            logger.error(f'Error al obtener documentos del expediente {expediente_id}: {str(e)}', exc_info=True)
            return JsonResponse(
                {'success': False, 'error': 'Error al obtener los documentos del expediente'}, 
                status=500
            )
            
    except Expediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Expediente no encontrado'}, 
            status=404
        )
    except Exception as e:
        logger.error(f'Error inesperado en obtener_documentos_expediente_api: {str(e)}', exc_info=True)
        return JsonResponse(
            {'success': False, 'error': 'Error interno del servidor al procesar la solicitud'}, 
            status=500
        )

@login_required
def ver_documentos_expediente(request, expediente_id):
    """
    Vista para ver los documentos de un expediente en una sola vista
    """
    logger.info(f'=== INICIO ver_documentos_expediente ===')
    logger.info(f'Expediente ID: {expediente_id}')
    logger.info(f'Usuario: {request.user} (ID: {request.user.id})')
    
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos - todos los usuarios autenticados pueden ver documentos
        if not puede_ver_expedientes(request.user):
            messages.error(request, 'No tiene permiso para ver expedientes.')
            return redirect('expedientes:lista')
        
        # Obtener documentos del expediente ordenados por fecha de subida
        documentos = expediente.documentos.all().order_by('fecha_subida')
        
        # Obtener áreas de documentos disponibles para este tipo de expediente
        areas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente
        ).order_by('orden')
        
        # Preparar los documentos para la vista
        documentos_con_info = []
        for doc in documentos:
            # Determinar el tipo de documento
            ext = os.path.splitext(doc.archivo.name)[1].lower()
            es_pdf = ext == '.pdf'
            es_imagen = ext in ['.jpg', '.jpeg', '.png', '.gif']
            es_documento = ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
            
            # Agregar información adicional para la vista
            documentos_con_info.append({
                'documento': doc,
                'es_pdf': es_pdf,
                'es_imagen': es_imagen,
                'es_documento': es_documento,
                'tipo': 'pdf' if es_pdf else 'imagen' if es_imagen else 'documento' if es_documento else 'otro',
                'url': doc.archivo.url,
                'nombre': os.path.basename(doc.archivo.name)
            })
        
        context = {
            'expediente': expediente,
            'documentos': documentos_con_info,
            'areas': areas,
            'titulo': f'Documentos del expediente {expediente.numero_expediente}'
        }
        
        logger.info(f'Renderizando plantilla ver_documentos.html con {len(documentos_con_info)} documentos')
        return render(request, 'digitalizacion/expedientes/ver_documentos.html', context)
        
    except Exception as e:
        logger.error(f'Error en ver_documentos_expediente: {str(e)}', exc_info=True)
        messages.error(request, 'Ocurrió un error al cargar los documentos del expediente.')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
@require_http_methods(["POST"])
def eliminar_comentario(request, expediente_id, comentario_id):
    """
    Vista para eliminar un comentario de un expediente
    """
    try:
        # Obtener el comentario
        comentario = get_object_or_404(ComentarioArea, id=comentario_id, expediente_id=expediente_id)
        
        # Verificar permisos (solo el autor o un superusuario pueden eliminar)
        if not (request.user.is_superuser or request.user == comentario.usuario):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para eliminar este comentario'},
                    status=403
                )
            messages.error(request, 'No tiene permiso para eliminar este comentario')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Guardar información para el historial
        expediente_id = comentario.expediente.id
        comentario_texto = comentario.texto[:50] + '...' if len(comentario.texto) > 50 else comentario.texto
        
        # Eliminar el comentario
        comentario.delete()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente_id=expediente_id,
            usuario=request.user,
            accion='Comentario eliminado',
            detalles=f'Se eliminó el comentario: "{comentario_texto}"'
        )
        
        # Responder según el tipo de solicitud
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Comentario eliminado correctamente',
                'redirect_url': reverse('expedientes:detalle', args=[expediente_id])
            })
            
        messages.success(request, 'Comentario eliminado correctamente')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
        
    except ComentarioArea.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'El comentario no existe'},
                status=404
            )
        messages.error(request, 'El comentario no existe')
        return redirect('expedientes:lista')
        
    except Exception as e:
        logger.error(f'Error al eliminar comentario {comentario_id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': f'Error al eliminar el comentario: {str(e)}'},
                status=500
            )
        messages.error(request, 'Ocurrió un error al intentar eliminar el comentario')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
@require_http_methods(["POST"])
def cambiar_estado_expediente(request, expediente_id):
    """
    Vista para cambiar el estado de un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.change_expediente', expediente):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para cambiar el estado de este expediente'},
                    status=403
                )
            messages.error(request, 'No tiene permiso para cambiar el estado de este expediente')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Obtener el nuevo estado del formulario
        nuevo_estado = request.POST.get('estado', '').strip()
        
        # Validar que el estado no esté vacío
        if not nuevo_estado:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Debe especificar un estado'},
                    status=400
                )
            messages.error(request, 'Debe especificar un estado')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Guardar el estado anterior para el historial
        estado_anterior = expediente.estado_actual
        
        # Actualizar el estado del expediente
        expediente.estado_actual = nuevo_estado
        expediente.fecha_modificacion = timezone.now()
        expediente.modificado_por = request.user
        expediente.save()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Cambio de estado: {estado_anterior} → {nuevo_estado}',
            detalles=f'El usuario {request.user.get_full_name()} cambió el estado del expediente.'
        )
        
        # Responder según el tipo de solicitud
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Estado del expediente actualizado correctamente',
                'estado_actual': nuevo_estado,
                'fecha_actualizacion': expediente.fecha_modificacion.strftime('%d/%m/%Y %H:%M')
            })
            
        messages.success(request, 'Estado del expediente actualizado correctamente')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
        
    except Expediente.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'El expediente no existe'},
                status=404
            )
        messages.error(request, 'El expediente no existe')
        return redirect('expedientes:lista')
        
    except Exception as e:
        logger.error(f'Error al cambiar estado del expediente {expediente_id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': f'Error al cambiar el estado del expediente: {str(e)}'},
                status=500
            )
        messages.error(request, 'Ocurrió un error al intentar cambiar el estado del expediente')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
@require_http_methods(["POST"])
def asignar_expediente(request, expediente_id):
    """
    Vista para asignar un expediente a un usuario
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.change_expediente', expediente):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para asignar este expediente'},
                    status=403
                )
            messages.error(request, 'No tiene permiso para asignar este expediente')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Obtener el ID del usuario al que se asignará el expediente
        usuario_id = request.POST.get('usuario_id')
        if not usuario_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Debe especificar un usuario'},
                    status=400
                )
            messages.error(request, 'Debe especificar un usuario')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'El usuario especificado no existe'},
                    status=404
                )
            messages.error(request, 'El usuario especificado no existe')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Guardar el usuario asignado anterior para el historial
        usuario_anterior = expediente.asignado_a
        
        # Asignar el expediente al nuevo usuario
        expediente.asignado_a = usuario
        expediente.fecha_modificacion = timezone.now()
        expediente.modificado_por = request.user
        expediente.save()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Expediente asignado a {usuario.get_full_name() or usuario.username}',
            detalles=f'El usuario {request.user.get_full_name()} asignó el expediente a {usuario.get_full_name() or usuario.username}.'
        )
        
        # Crear notificación para el usuario asignado
        Notificacion.objects.create(
            usuario=usuario,
            titulo=f'Se te ha asignado el expediente {expediente.numero_expediente}',
            mensaje=f'El usuario {request.user.get_full_name()} te ha asignado el expediente {expediente.numero_expediente}.',
            url=reverse('expedientes:detalle', args=[expediente.id])
        )
        
        # Responder según el tipo de solicitud
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Expediente asignado correctamente',
                'usuario_asignado': {
                    'id': usuario.id,
                    'nombre': usuario.get_full_name() or usuario.username,
                    'username': usuario.username
                },
                'fecha_asignacion': expediente.fecha_modificacion.strftime('%d/%m/%Y %H:%M')
            })
            
        messages.success(request, f'Expediente asignado correctamente a {usuario.get_full_name() or usuario.username}')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
        
    except Expediente.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'El expediente no existe'},
                status=404
            )
        messages.error(request, 'El expediente no existe')
        return redirect('expedientes:lista')
        
    except Exception as e:
        logger.error(f'Error al asignar expediente {expediente_id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': f'Error al asignar el expediente: {str(e)}'},
                status=500
            )
        messages.error(request, 'Ocurrió un error al intentar asignar el expediente')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
@require_http_methods(["POST"])
def transferir_expediente(request, expediente_id):
    """
    Vista para transferir un expediente a otra área
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.transferir_expediente', expediente):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para transferir este expediente'},
                    status=403
                )
            messages.error(request, 'No tiene permiso para transferir este expediente')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Obtener el ID del área de destino
        area_destino_id = request.POST.get('area_destino_id')
        if not area_destino_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Debe especificar un área de destino'},
                    status=400
                )
            messages.error(request, 'Debe especificar un área de destino')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        try:
            area_destino = AreaTipoExpediente.objects.get(id=area_destino_id)
        except AreaTipoExpediente.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'El área de destino especificada no existe'},
                    status=404
                )
            messages.error(request, 'El área de destino especificada no existe')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Guardar el área anterior para el historial
        area_anterior = expediente.area_actual
        
        # Transferir el expediente al área de destino
        expediente.area_anterior = expediente.area_actual
        expediente.area_actual = area_destino
        expediente.fecha_modificacion = timezone.now()
        expediente.modificado_por = request.user
        
        # Si el área de destino es diferente, reiniciamos el estado
        if area_anterior != area_destino:
            expediente.estado_actual = 'Pendiente de revisión'
            
        expediente.save()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Expediente transferido a {area_destino.nombre}',
            detalles=f'El usuario {request.user.get_full_name()} transfirió el expediente de {area_anterior.nombre} a {area_destino.nombre}.'
        )
        
        # Crear notificación para los usuarios del área de destino con permisos
        usuarios_destino = User.objects.filter(
            groups__in=area_destino.grupos_usuarios.all(),
            is_active=True
        ).distinct()
        
        for usuario in usuarios_destino:
            if usuario != request.user:  # No notificar al usuario que realiza la transferencia
                Notificacion.objects.create(
                    usuario=usuario,
                    titulo=f'Nuevo expediente transferido a {area_destino.nombre}',
                    mensaje=f'El usuario {request.user.get_full_name()} ha transferido el expediente {expediente.numero_expediente} a tu área.',
                    url=reverse('expedientes:detalle', args=[expediente.id])
                )
        
        # Responder según el tipo de solicitud
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Expediente transferido correctamente',
                'area_destino': {
                    'id': area_destino.id,
                    'nombre': area_destino.nombre,
                    'codigo': area_destino.codigo
                },
                'nuevo_estado': expediente.estado_actual,
                'fecha_transferencia': expediente.fecha_modificacion.strftime('%d/%m/%Y %H:%M')
            })
            
        messages.success(request, f'Expediente transferido correctamente a {area_destino.nombre}')
        return redirect('expedientes:detalle', expediente_id=expediente_id)
        
    except Expediente.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'El expediente no existe'},
                status=404
            )
        messages.error(request, 'El expediente no existe')
        return redirect('expedientes:lista')
        
    except Exception as e:
        logger.error(f'Error al transferir expediente {expediente_id}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': f'Error al transferir el expediente: {str(e)}'},
                status=500
            )
@login_required
def editar_expediente(request, expediente_id):
    """
    Vista para editar un expediente existente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos (solo el usuario que creó el expediente o superusuarios pueden editarlo)
        if not (request.user.is_superuser or expediente.creado_por == request.user):
            messages.error(request, 'No tienes permiso para editar este expediente.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Verificar que el expediente no esté en un estado que impida la edición
        if expediente.estado in ['aprobado', 'rechazado']:
            messages.error(request, 'No se puede editar un expediente que ya ha sido aprobado o rechazado.')
            return redirect('expedientes:detalle', expediente_id=expediente_id)
        
        # Obtener el tipo y subtipo del expediente para el formulario
        tipo_expediente = expediente.tipo_expediente
        subtipo_expediente = getattr(expediente, 'subtipo_expediente', None)
        
        if request.method == 'POST':
            # Crear el formulario con los datos del POST
            form = ExpedienteForm(
                request.POST, 
                request.FILES, 
                instance=expediente,
                user=request.user,
                tipo_expediente=tipo_expediente,
                subtipo_expediente=subtipo_expediente
            )
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Guardar los cambios en el expediente
                        expediente = form.save(commit=False)
                        expediente.modificado_por = request.user
                        expediente.fecha_modificacion = timezone.now()
                        expediente.save()
                        form.save_m2m()  # Guardar relaciones many-to-many
                        
                        # Registrar en el historial
                        HistorialExpediente.objects.create(
                            expediente=expediente,
                            usuario=request.user,
                            accion='actualizar_expediente',
                            descripcion='Se actualizaron los datos del expediente.',
                            fecha=timezone.now()
                        )
                        
                        messages.success(request, 'Los cambios en el expediente se han guardado correctamente.')
                        return redirect('expedientes:detalle', expediente_id=expediente_id)
                        
                except Exception as e:
                    logger.error(f"Error al guardar el expediente {expediente_id}: {str(e)}")
                    messages.error(request, f'Error al guardar los cambios: {str(e)}')
            else:
                # Si el formulario no es válido, mostrar los errores
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en {field}: {error}")
        else:
            # Crear el formulario con la instancia del expediente
            form = ExpedienteForm(
                instance=expediente,
                user=request.user,
                tipo_expediente=tipo_expediente,
                subtipo_expediente=subtipo_expediente
            )
        
        # Obtener documentos del expediente
        documentos = expediente.documentos.all().order_by('fecha_subida')
        
        return render(request, 'digitalizacion/expedientes/crear_expediente.html', {
            'form': form,
            'expediente': expediente,
            'documentos': documentos,
            'tipo': tipo_expediente,
            'subtipo': subtipo_expediente,
            'modo_edicion': True
        })
        
    except Exception as e:
        logger.error(f'Error al editar expediente {expediente_id}: {str(e)}', exc_info=True)
        messages.error(request, 'Ocurrió un error al intentar editar el expediente.')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
def crear_expediente(request, tipo_id):
    """
    Vista para crear un nuevo expediente de un tipo específico
    """
    # Configuración inicial de logging
    logger.debug("\n=== INICIO crear_expediente ===")
    logger.debug(f"Usuario: {request.user} (ID: {request.user.id})")
    logger.debug(f"Tipo ID recibido: {tipo_id}")
    logger.debug(f"Método: {request.method}")
    logger.debug(f"Permiso add_expediente: {request.user.has_perm('digitalizacion.add_expediente')}")
    # Verificar permisos - solo editor y administrador pueden crear expedientes
    if not puede_crear_expedientes(request.user):
        messages.error(request, 'No tienes permisos para crear expedientes.')
        return redirect('expedientes:lista')
    # Validar tipo de expediente
    tipo_opciones = dict(Expediente.TIPO_CHOICES)
    tipo_valido = False
    tipo_nombre = ''
    subtipo = None
    tipo_principal = None
    # Verificar si es un tipo principal
    if tipo_id in tipo_opciones:
        tipo_valido = True
        tipo_principal = tipo_id
        tipo_nombre = tipo_opciones.get(tipo_id, tipo_id)
    # Verificar si es un subtipo de licitación
    elif ':' in tipo_id:
        tipo_principal, subtipo = tipo_id.split(':', 1)
        if tipo_principal == 'licitacion' and subtipo in dict(Expediente.SUBTIPO_LICITACION_CHOICES):
            tipo_valido = True
            tipo_nombre = f"{tipo_opciones.get('licitacion', 'Licitación')} - {dict(Expediente.SUBTIPO_LICITACION_CHOICES).get(subtipo, subtipo)}"
    if not tipo_valido:
        error_msg = f'Tipo de expediente no válido: {tipo_id}'
        logger.warning(error_msg)
        messages.error(request, 'Tipo de expediente no válido')
        return redirect('expedientes:seleccionar_tipo')
    # Procesar formulario si es POST
    if request.method == 'POST':
        logger.debug("\n=== PROCESANDO FORMULARIO ===")
        logger.debug(f"Datos POST: {request.POST}")
        logger.debug(f"Archivos adjuntos: {request.FILES}")
        logger.debug(f"Usuario autenticado: {request.user} (ID: {request.user.id})")
        logger.debug(f"Tipo principal: {tipo_principal}, Subtipo: {subtipo}")
        # Crear una copia mutable de los datos POST
        post_data = request.POST.copy()
        
        # Inicializar variables
        tipo_principal = None
        subtipo = None
        
        # Procesar el tipo de expediente
        if ':' in tipo_id:
            tipo_principal, subtipo = tipo_id.split(':', 1)
            post_data['tipo_expediente'] = tipo_principal
            post_data['subtipo_expediente'] = subtipo
        else:
            post_data['tipo_expediente'] = tipo_id
            tipo_principal = tipo_id
            subtipo = ''
        
        # Solo establecer valores por defecto si no hay datos POST
        if not request.POST:
            if 'fuente_financiamiento' not in post_data:
                if tipo_principal == 'licitacion':
                    if subtipo == 'recurso_propio':
                        post_data['fuente_financiamiento'] = 'propio_municipal'
                    elif subtipo == 'fondo_federal':
                        post_data['fuente_financiamiento'] = 'federal'
                else:
                    post_data['fuente_financiamiento'] = 'propio_municipal'
            
            if 'tipo_adquisicion' not in post_data:
                post_data['tipo_adquisicion'] = 'bienes'
        
        # Determinar el tipo y subtipo finales
        tipo_final = tipo_principal if tipo_principal else tipo_id
        subtipo_final = subtipo if subtipo else ''
        
        # Asegurarse de que el subtipo esté en el formato correcto (sin espacios, minúsculas, etc.)
        if subtipo_final:
            subtipo_final = subtipo_final.strip().lower().replace(' ', '_')
        
        # Asegurarse de que el tipo y subtipo estén en los datos POST
        if request.method == 'POST':
            post_data = request.POST.copy()
            post_data['tipo_expediente'] = tipo_final
            post_data['subtipo_expediente'] = subtipo_final
        
        # Crear el formulario con los datos procesados y parámetros adicionales
        form_kwargs = {
            'data': post_data,
            'files': request.FILES,
            'tipo_expediente': tipo_final,
            'subtipo_expediente': subtipo_final,
            'user': request.user
        }
        
        # Crear el formulario con los parámetros
        form = ExpedienteForm(**form_kwargs)
        
        # Determinar si es un envío de formulario
        is_form_submission = request.method == 'POST'
        
        # NOTA: No crear campos dinámicos para áreas aquí
        # Las áreas NO se muestran en el formulario de creación, solo en el detalle del expediente
        
        # Agregar logs detallados para depuración
        logger.debug("\n=== INFORMACIÓN DEL FORMULARIO ===")
        logger.debug(f"[TIPO] {tipo_final}")
        logger.debug(f"[SUBTIPO] {subtipo_final or 'Ninguno'}")
        logger.debug(f"[USUARIO] {request.user} (ID: {request.user.id})")
        logger.debug(f"[MÉTODO] {request.method}")
        logger.debug(f"[ES ENVÍO] {is_form_submission}")
        
        if hasattr(form, 'areas'):
            logger.debug("\n=== ÁREAS ENCONTRADAS ===")
            if form.areas:
                for i, area in enumerate(form.areas, 1):
                    logger.debug(f"{i}. {area.titulo} (Tipo: {area.tipo_area}, Obligatoria: {area.obligatoria})")
                    logger.debug(f"   - ID: {area.id}")
                    logger.debug(f"   - Descripción: {area.descripcion}")
                    logger.debug(f"   - Tipos de archivo permitidos: {area.tipos_archivo_permitidos}")
            else:
                # Cambiar a debug ya que puede ser normal si el tipo de expediente no tiene áreas configuradas aún
                logger.debug("No se encontraron áreas para este tipo de expediente")
        
        logger.debug("\n=== CAMPOS DEL FORMULARIO ===")
        for field_name, field in form.fields.items():
            logger.debug(f"- {field_name}: {field.__class__.__name__} (Requerido: {field.required})")
        
        logger.debug(f"Formulario data: {form.data}")
        logger.debug(f"Valores iniciales: {form.initial}")
        
        # Validar el formulario
        is_valid = form.is_valid()
        logger.debug(f"\n=== VALIDACIÓN DEL FORMULARIO ===")
        logger.debug(f"Válido: {is_valid}")
        
        if not is_valid:
            logger.error("Errores de validación:")
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"- {field}: {error}")
        
        if is_valid:
            try:
                with transaction.atomic():
                    # Obtener valores directamente de request.POST
                    fuente_financiamiento = request.POST.get('fuente_financiamiento', 'propio_municipal')
                    tipo_adquisicion = request.POST.get('tipo_adquisicion', 'bienes')
                    
                    # Crear el expediente con los valores del formulario
                    expediente = form.save(commit=False)
                    expediente.creado_por = request.user
                    expediente.fuente_financiamiento = fuente_financiamiento
                    expediente.tipo_adquisicion = tipo_adquisicion
                    
                    # Asegurarse de que el subtipo se guarde correctamente
                    if subtipo_final:
                        expediente.subtipo_expediente = subtipo_final
                    
                    # Guardar el expediente
                    expediente.save()
                    
                    
                    # Procesar archivos adjuntos
                    if 'archivos' in request.FILES:
                        for archivo in request.FILES.getlist('archivos'):
                            try:
                                DocumentoExpediente.objects.create(
                                    expediente=expediente,
                                    archivo=archivo,
                                    nombre=archivo.name,
                                    subido_por=request.user,
                                    tipo_documento=TipoDocumento.objects.get_or_create(nombre='General')[0]
                                )
                            except Exception as e:
                                logger.error(f'Error al guardar archivo {archivo.name}: {str(e)}')
                                raise ValidationError(f'Error al procesar el archivo {archivo.name}: {str(e)}')
                    
                    # NOTA: Las áreas NO se procesan aquí porque no se muestran en el formulario de creación
                    # Las áreas se gestionan en el detalle del expediente, no en la creación
                    
                    # Registrar en el historial
                    HistorialExpediente.objects.create(
                        expediente=expediente,
                        usuario=request.user,
                        accion='CREACION',
                        descripcion=f'Expediente creado por {request.user.get_full_name() or request.user.username}'
                    )
                    
                    logger.info(f"Expediente creado correctamente. ID: {expediente.id}")
                    
                    # Redirigir al detalle del expediente
                    return redirect('expedientes:detalle', expediente_id=expediente.id)
                    
            except (ValidationError, Exception) as e:
                # Capturar cualquier error al crear el expediente
                error_msg = f'Error al guardar el expediente: {str(e)}'
                logger.error(error_msg, exc_info=True)
                messages.error(request, 'Ocurrió un error al guardar el expediente. Por favor, inténtalo de nuevo.')
        else:
            # Mostrar errores del formulario
            logger.error("El formulario no es válido")
            for field, errors in form.errors.items():
                for error in errors:
                    msg = f"Error en {field}: {error}"
                    messages.error(request, msg)
                    logger.error(msg)
    else:
        # Método GET - Mostrar formulario vacío
        # Extraer tipo y subtipo del tipo_id
        if ':' in tipo_id:
            tipo_principal_get, subtipo_get = tipo_id.split(':', 1)
        else:
            tipo_principal_get = tipo_id
            subtipo_get = None
        
        # Normalizar el subtipo si existe
        if subtipo_get:
            subtipo_get = subtipo_get.strip().lower().replace(' ', '_')
        
        initial_data = {'tipo_expediente': tipo_principal_get}
        if subtipo_get:
            initial_data['subtipo_expediente'] = subtipo_get
        
        # IMPORTANTE: Pasar tipo_expediente y subtipo_expediente como kwargs para que get_areas_for_expediente funcione
        form = ExpedienteForm(
            initial=initial_data, 
            user=request.user,
            tipo_expediente=tipo_principal_get,
            subtipo_expediente=subtipo_get
        )
    # Obtener todos los departamentos activos
    departamentos = Departamento.objects.filter(activo=True).order_by('nombre')
    
    # Determinar si se debe mostrar el campo de fuente de financiamiento
    # Mostrar para todos los tipos excepto licitaciones
    mostrar_fuente_financiamiento = not tipo_id.startswith('licitacion')
    
    # Inicializar el formulario con los datos correspondientes
    if request.method == 'POST':
        # Crear una copia mutable de los datos POST
        post_data = request.POST.copy()
        
        # Asegurarse de que tipo_expediente esté correctamente formateado
        if ':' in tipo_id:
            tipo_principal, subtipo = tipo_id.split(':', 1)
            post_data['tipo_expediente'] = tipo_principal
            post_data['subtipo_expediente'] = subtipo
        else:
            post_data['tipo_expediente'] = tipo_id
            
        # Asegurarse de que tipo_adquisicion tenga un valor por defecto si no está presente
        if 'tipo_adquisicion' not in post_data or not post_data['tipo_adquisicion']:
            post_data['tipo_adquisicion'] = 'bienes'
        
        # Si no se debe mostrar fuente_financiamiento, asegurarse de que no esté en los datos
        if not mostrar_fuente_financiamiento:
            if 'fuente_financiamiento' in post_data:
                del post_data['fuente_financiamiento']
            # Establecer un valor por defecto para licitaciones
            if 'licitacion:recurso_propio' in tipo_id:
                post_data['fuente_financiamiento'] = 'propio_municipal'
            elif 'licitacion:fondo_federal' in tipo_id:
                post_data['fuente_financiamiento'] = 'federal'
        
        # Extraer tipo y subtipo para pasarlos como kwargs
        tipo_principal_post = post_data.get('tipo_expediente', tipo_id.split(':')[0] if ':' in tipo_id else tipo_id)
        subtipo_post = post_data.get('subtipo_expediente', None)
        if subtipo_post:
            subtipo_post = subtipo_post.strip().lower().replace(' ', '_')
        
        # Crear el formulario con los datos procesados y los parámetros tipo/subtipo
        form = ExpedienteForm(
            post_data, 
            request.FILES, 
            user=request.user,
            tipo_expediente=tipo_principal_post,
            subtipo_expediente=subtipo_post
        )
        
        # Validar el formulario
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear el expediente manualmente
                    expediente = Expediente(
                        titulo=form.cleaned_data.get('titulo'),
                        descripcion=form.cleaned_data.get('descripcion'),
                        tipo_expediente=form.cleaned_data.get('tipo_expediente'),
                        subtipo_expediente=form.cleaned_data.get('subtipo_expediente', ''),
                        departamento=form.cleaned_data.get('departamento'),
                        giro=form.cleaned_data.get('giro'),
                        fuente_financiamiento=form.cleaned_data.get('fuente_financiamiento'),
                        tipo_adquisicion=form.cleaned_data.get('tipo_adquisicion', 'bienes'),
                        modalidad_monto=form.cleaned_data.get('modalidad_monto'),
                        creado_por=request.user
                    )
                    expediente.save()
                    
                    # Procesar archivos adjuntos si los hay
                    if 'archivos' in request.FILES:
                        for archivo in request.FILES.getlist('archivos'):
                            DocumentoExpediente.objects.create(
                                expediente=expediente,
                                archivo=archivo,
                                nombre=archivo.name,
                                subido_por=request.user
                            )
                    
                    messages.success(request, 'Expediente creado exitosamente')
                    return redirect('expedientes:detalle', expediente_id=expediente.id)
                    
            except Exception as e:
                logger.error(f'Error al guardar el expediente: {str(e)}', exc_info=True)
                messages.error(request, f'Error al guardar el expediente: {str(e)}')
        else:
            logger.error(f'Error de validación del formulario: {form.errors}')
            # Agregar los errores a los mensajes para mostrarlos al usuario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        # Para GET, establecer valores iniciales
        # Extraer tipo y subtipo del tipo_id
        if ':' in tipo_id:
            tipo_principal_get, subtipo_get = tipo_id.split(':', 1)
        else:
            tipo_principal_get = tipo_id
            subtipo_get = None
        
        # Normalizar el subtipo si existe
        if subtipo_get:
            subtipo_get = subtipo_get.strip().lower().replace(' ', '_')
        
        initial_data = {}
        initial_data['tipo_expediente'] = tipo_principal_get
        if subtipo_get:
            initial_data['subtipo_expediente'] = subtipo_get
        initial_data['tipo_adquisicion'] = 'bienes'
        if mostrar_fuente_financiamiento:
            initial_data['fuente_financiamiento'] = 'propio_municipal'
        
        # IMPORTANTE: Pasar tipo_expediente y subtipo_expediente como kwargs para que get_areas_for_expediente funcione
        form = ExpedienteForm(
            initial=initial_data, 
            user=request.user,
            tipo_expediente=tipo_principal_get,
            subtipo_expediente=subtipo_get
        )
    
    # Si hay errores de validación, mostrarlos en los logs
    if request.method == 'POST' and not form.is_valid():
        logger.error(f'Error de validación al crear expediente: {form.errors}')
    
    context = {
        'form': form,
        'tipo': tipo_id,
        'tipo_nombre': tipo_nombre,
        'titulo': f'Nuevo Expediente - {tipo_nombre}',
        'departamentos': departamentos,
        'mostrar_fuente_financiamiento': mostrar_fuente_financiamiento,
        'subtipo': subtipo if ':' in tipo_id else None
    }
    
    return render(request, 'digitalizacion/expedientes/crear_expediente.html', context)

@login_required
def seleccionar_tipo_expediente(request):
    """
    Vista para seleccionar el tipo de expediente antes de crearlo
    """
    try:
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.add_expediente'):
            return redirect('expedientes:lista')
        
        # Tipos principales de expediente basados en el modelo
        tipos = [
            {
                'key': 'licitacion',
                'title': 'Licitación',
                'description': 'Proceso de contratación pública para adquisiciones de bienes y servicios',
                'tiene_subtipos': True,
                'subtipos': [
                    {
                        'key': 'recurso_propio',
                        'title': 'Recurso Propio',
                        'description': 'Proceso de contratación con recursos propios',
                        'icon': 'bi bi-cash-coin'
                    },
                    {
                        'key': 'fondo_federal',
                        'title': 'Fondo Federal',
                        'description': 'Proceso de contratación con fondos federales',
                        'icon': 'bi bi-bank2'
                    },
                    {
                        'key': 'otros',
                        'title': 'Otros',
                        'description': 'Otros tipos de licitación',
                        'icon': 'bi bi-three-dots'
                    }
                ]
            },
            {
                'key': 'adjudicacion_directa',
                'title': 'Adjudicación Directa',
                'description': 'Adjudicación directa en casos excepcionales según la normativa aplicable',
                'tiene_subtipos': False,
                'icon': 'bi bi-check2-circle'
            },
            {
                'key': 'compra_directa',
                'title': 'Compra Directa',
                'description': 'Adquisición directa de bienes y servicios hasta el monto límite establecido',
                'tiene_subtipos': False,
                'icon': 'bi bi-cart-plus'
            },
            {
                'key': 'concurso_invitacion',
                'title': 'Concurso por Invitación',
                'description': 'Proceso de contratación para cuando se invita a cuando menos a tres proveedores',
                'tiene_subtipos': False,
                'icon': 'bi bi-trophy'
            }
        ]
        
        # Manejar petición AJAX para obtener subtipos
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            tipo = request.GET.get('tipo')
            if tipo:
                tipo_seleccionado = next((t for t in tipos if t['key'] == tipo), None)
                if tipo_seleccionado and tipo_seleccionado.get('tiene_subtipos'):
                    return JsonResponse({
                        'tiene_subtipos': True,
                        'subtipos': tipo_seleccionado.get('subtipos', [])
                    })
                return JsonResponse({'tiene_subtipos': False})
            return JsonResponse({'error': 'Tipo no especificado'}, status=400)
        
        if request.method == 'POST':
            tipo_id = request.POST.get('tipo_expediente')
            subtipo_id = request.POST.get('subtipo')
            
            if tipo_id:
                # Si tiene subtipos y no se seleccionó uno, mostrar error
                tipo_seleccionado = next((t for t in tipos if t['key'] == tipo_id), None)
                if tipo_seleccionado and tipo_seleccionado.get('tiene_subtipos') and not subtipo_id:
                    django_messages.error(request, 'Debe seleccionar un tipo de licitación')
                else:
                    # Si es un subtipo de licitación, usar el formato tipo:subtipo
                    if tipo_id == 'licitacion' and subtipo_id:
                        tipo_a_usar = f"{tipo_id}:{subtipo_id}"
                    else:
                        tipo_a_usar = tipo_id
                    return redirect('expedientes:crear', tipo_id=tipo_a_usar)
            else:
                django_messages.error(request, 'Debe seleccionar un tipo de expediente')
        
        context = {
            'tipos': tipos,
            'titulo': 'Seleccionar Tipo de Expediente'
        }
        
        return render(request, 'digitalizacion/expedientes/seleccionar_tipo.html', context)
        
    except Exception as e:
        logger.error(f'Error al seleccionar tipo de expediente: {str(e)}', exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Ocurrió un error al cargar los tipos de expediente'}, status=500)
        django_messages.error(request, 'Ocurrió un error al cargar los tipos de expediente')
        return redirect('expedientes:lista')

@login_required
def lista_expedientes(request):
    """
    Vista para listar todos los expedientes con opciones de filtrado y búsqueda
    """
    try:
        # Obtener parámetros de filtrado
        filtros_actuales = {
            'busqueda': request.GET.get('q', ''),
            'numero_sima': request.GET.get('numero_sima', ''),
            'tipo': request.GET.get('tipo', ''),
            'departamento': request.GET.get('departamento', ''),
            'estado': request.GET.get('estado', ''),
            'orden': request.GET.get('orden', '-fecha_creacion')
        }
        
        # Construir consulta base
        expedientes = Expediente.objects.select_related('departamento', 'creado_por')
        
        # Aplicar filtros
        if filtros_actuales['busqueda']:
            busqueda = filtros_actuales['busqueda']
            expedientes = expedientes.filter(
                Q(numero_expediente__icontains=busqueda) |
                Q(titulo__icontains=busqueda) |
                Q(descripcion__icontains=busqueda) |
                Q(observaciones__icontains=busqueda)
            )
            
        if filtros_actuales['numero_sima']:
            expedientes = expedientes.filter(numero_sima__icontains=filtros_actuales['numero_sima'])
            
        if filtros_actuales['tipo']:
            tipo = filtros_actuales['tipo']
            # Mapear los tipos a sus respectivos valores en el modelo
            tipo_mapping = {
                'licitacion_recurso_propio': {'tipo': 'licitacion', 'subtipo': 'recurso_propio'},
                'licitacion_fondo_federal': {'tipo': 'licitacion', 'subtipo': 'fondo_federal'},
                'adjudicacion_directa': {'tipo': 'adjudicacion_directa', 'subtipo': ''},
                'compra_directa': {'tipo': 'compra_directa', 'subtipo': ''},
                'concurso_invitacion': {'tipo': 'concurso_invitacion', 'subtipo': ''},
            }
            
            if tipo in tipo_mapping:
                filtro = tipo_mapping[tipo]
                expedientes = expedientes.filter(tipo_expediente=filtro['tipo'])
                if filtro['subtipo']:
                    expedientes = expedientes.filter(subtipo_expediente=filtro['subtipo'])
            
        if filtros_actuales['departamento']:
            expedientes = expedientes.filter(departamento_id=filtros_actuales['departamento'])
            
        if filtros_actuales['estado']:
            estado_filtro = filtros_actuales['estado']
            # Mapear 'completado' a 'completo' para el campo estado
            # También buscar en estado_actual para asegurar que se encuentren todos los expedientes completados
            if estado_filtro == 'completado':
                # Buscar expedientes completados en ambos campos
                expedientes = expedientes.filter(
                    Q(estado='completo') | Q(estado_actual='completado')
                )
            else:
                # Para otros estados, usar el campo 'estado'
                expedientes = expedientes.filter(estado=estado_filtro)
        
        # Ordenar
        expedientes = expedientes.order_by(filtros_actuales['orden'])
        
        # Obtener opciones para los filtros
        departamentos = Departamento.objects.all().order_by('nombre')
        
        # Definir los estados posibles
        estados = [
            ('en_proceso', 'En Proceso'),
            ('rechazado', 'Rechazado'),
            ('completado', 'Completado')
        ]
        
        # Paginación
        page = request.GET.get('page', 1)
        paginator = Paginator(expedientes, 25)  # 25 expedientes por página
        
        try:
            expedientes_pagina = paginator.page(page)
        except PageNotAnInteger:
            expedientes_pagina = paginator.page(1)
        except EmptyPage:
            expedientes_pagina = paginator.page(paginator.num_pages)
        
        # Calcular el progreso real para cada expediente en la página usando método directo y confiable
        def calcular_progreso_avanzado(expediente):
            """
            Calcula el progreso de un expediente contando directamente las áreas completadas.
            Retorna un entero entre 0 y 100.
            """
            try:
                # 1. Verificar estado del expediente primero
                estado_actual = getattr(expediente, 'estado_actual', None) or getattr(expediente, 'estado', None)
                
                # Si está completado, el progreso es 100%
                if estado_actual in ['completado', 'completo', 'finalizado']:
                    logger.info(f'[PROGRESO] Expediente {expediente.id}: Estado completado, retornando 100%')
                    return 100
                
                # Si está rechazado, el progreso es 0%
                if estado_actual == 'rechazado':
                    logger.info(f'[PROGRESO] Expediente {expediente.id}: Estado rechazado, retornando 0%')
                    return 0
                
                # 2. Calcular directamente contando áreas completadas (método más confiable)
                # Obtener áreas configuradas para este expediente
                try:
                    areas = expediente.get_areas_configuradas()
                    total_areas = areas.count()
                except Exception as areas_error:
                    logger.error(f'[PROGRESO] Expediente {expediente.id}: Error al obtener áreas: {str(areas_error)}', exc_info=True)
                    return 0
                
                logger.info(f'[PROGRESO] Expediente {expediente.id} ({expediente.numero_expediente}): Total áreas configuradas: {total_areas}')
                
                if total_areas == 0:
                    logger.warning(f'[PROGRESO] Expediente {expediente.id}: No hay áreas configuradas, retornando 0%')
                    return 0
                
                # Contar áreas completadas - método directo contando documentos
                areas_completadas = 0
                areas_detalle = []
                
                # Obtener todas las áreas que tienen documentos para este expediente
                areas_con_documentos = DocumentoExpediente.objects.filter(
                    expediente=expediente
                ).values_list('area_id', flat=True).distinct()
                
                logger.info(f'[PROGRESO] Expediente {expediente.id}: Áreas con documentos: {list(areas_con_documentos)}')
                
                for area in areas:
                    try:
                        area_id = area.id
                        area_titulo = getattr(area, 'titulo', getattr(area, 'nombre', 'Sin nombre'))
                        
                        # Verificar directamente si hay documentos para esta área
                        tiene_docs = area_id in areas_con_documentos
                        
                        # También verificar usando el método etapa_completada
                        completada_metodo = False
                        try:
                            completada_metodo = area.etapa_completada(expediente)
                        except Exception as metodo_error:
                            logger.warning(f'[PROGRESO] Expediente {expediente.id}: Error en etapa_completada para área {area_id}: {str(metodo_error)}')
                        
                        # Si tiene documentos O el método dice que está completada, considerar completada
                        completada = tiene_docs or completada_metodo
                        
                        if completada:
                            areas_completadas += 1
                            logger.debug(f'[PROGRESO] Expediente {expediente.id}: Área {area_id} ({area_titulo}) COMPLETADA (tiene_docs: {tiene_docs}, metodo: {completada_metodo})')
                        else:
                            logger.debug(f'[PROGRESO] Expediente {expediente.id}: Área {area_id} ({area_titulo}) NO completada')
                        
                        areas_detalle.append({
                            'id': area_id,
                            'titulo': area_titulo,
                            'completada': completada,
                            'tiene_docs': tiene_docs,
                            'completada_metodo': completada_metodo
                        })
                        
                    except Exception as area_error:
                        logger.error(f'[PROGRESO] Expediente {expediente.id}: Error al verificar área {area.id}: {str(area_error)}', exc_info=True)
                        continue
                
                # Calcular porcentaje
                progreso_calculado = int((areas_completadas / total_areas) * 100) if total_areas > 0 else 0
                progreso_calculado = max(0, min(100, progreso_calculado))
                
                logger.info(f'[PROGRESO] Expediente {expediente.id} ({expediente.numero_expediente}): Progreso calculado: {progreso_calculado}% ({areas_completadas}/{total_areas} áreas completadas)')
                
                # Log detallado de áreas
                for detalle in areas_detalle:
                    if detalle['completada']:
                        logger.debug(f'[PROGRESO] Expediente {expediente.id}: Área completada: {detalle["titulo"]} (tiene_docs: {detalle["tiene_docs"]})')
                
                return progreso_calculado
                
            except Exception as e:
                logger.error(f'[PROGRESO] Error general al calcular progreso para expediente {expediente.id}: {str(e)}', exc_info=True)
                return 0
        
        # Aplicar el cálculo de progreso a cada expediente
        for expediente in expedientes_pagina:
            try:
                progreso_calculado = calcular_progreso_avanzado(expediente)
                
                # Asegurar que el progreso sea un entero
                progreso_calculado = int(progreso_calculado) if progreso_calculado is not None else 0
                progreso_calculado = max(0, min(100, progreso_calculado))
                
                # Asignar el progreso calculado al objeto de múltiples formas para asegurar que se muestre
                expediente.progreso = progreso_calculado
                # También asignar como atributo dinámico por si acaso
                setattr(expediente, 'progreso_calculado', progreso_calculado)
                
                # Verificar que se asignó correctamente
                progreso_verificado = getattr(expediente, 'progreso', None)
                if progreso_verificado != progreso_calculado:
                    logger.warning(f'[PROGRESO] Expediente {expediente.id}: El progreso no se asignó correctamente. Esperado: {progreso_calculado}, Actual: {progreso_verificado}')
                    # Forzar la asignación de múltiples formas
                    expediente.progreso = progreso_calculado
                    setattr(expediente, 'progreso', progreso_calculado)
                else:
                    logger.info(f'[PROGRESO] Expediente {expediente.id} ({expediente.numero_expediente}): Progreso asignado: {expediente.progreso}% (verificado: {progreso_verificado})')
                
            except Exception as e:
                logger.error(f'[PROGRESO] Error al procesar expediente {expediente.id}: {str(e)}', exc_info=True)
                expediente.progreso = 0
                setattr(expediente, 'progreso_calculado', 0)
        
        # Asegurar que todos los expedientes tengan el progreso asignado correctamente
        for expediente in expedientes_pagina:
            # Obtener el progreso que ya fue calculado
            progreso_final = getattr(expediente, 'progreso', None)
            
            # Si no existe, usar progreso_calculado
            if progreso_final is None:
                progreso_final = getattr(expediente, 'progreso_calculado', 0)
            
            # Asegurar que sea un entero válido
            if progreso_final is None:
                progreso_final = 0
            else:
                try:
                    progreso_final = int(float(progreso_final))
                    progreso_final = max(0, min(100, progreso_final))
                except (ValueError, TypeError):
                    progreso_final = 0
            
            # Asignar el progreso final de múltiples formas para asegurar que el template lo vea
            expediente.progreso = progreso_final
            expediente.progreso_display = progreso_final
            setattr(expediente, 'progreso_mostrar', progreso_final)
            
            # Verificar que se asignó
            progreso_verificado = getattr(expediente, 'progreso', None)
            logger.info(f'[PROGRESO] Expediente {expediente.id} ({expediente.numero_expediente}): Progreso final asignado: {progreso_final}% (verificado: {progreso_verificado})')
        
        # Preparar el contexto
        context = {
            'expedientes': expedientes_pagina,
            'departamentos': departamentos,
            'estados': estados,
            'filtros_actuales': filtros_actuales,
            'titulo': 'Lista de Expedientes',
            'orden_actual': filtros_actuales['orden']
        }
        
        return render(request, 'digitalizacion/expedientes/lista.html', context)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f'Error al listar expedientes: {str(e)}\n{error_trace}')
        messages.error(request, f'Ocurrió un error al cargar la lista de expedientes: {str(e)}')
        # En desarrollo, mostrar más detalles
        if settings.DEBUG:
            logger.error(f'Traceback completo: {error_trace}')
        return redirect('digitalizacion:dashboard')

@login_required
def dashboard_expedientes(request):
    """
    Vista para el dashboard de expedientes
    """
    try:
        # Obtener estadísticas generales
        total_expedientes = Expediente.objects.count()
        expedientes_activos = Expediente.objects.filter(estado='activo').count()
        expedientes_completados = Expediente.objects.filter(
            Q(estado='completo') | Q(estado_actual='completado')
        ).count()
        
        # Obtener los últimos expedientes
        ultimos_expedientes = Expediente.objects.select_related('creado_por').order_by('-fecha_creacion')[:10]
        
        # Obtener actividades recientes
        actividades_recientes = HistorialExpediente.objects.select_related('usuario', 'expediente')\
            .order_by('-fecha')[:15]
        
        context = {
            'titulo': 'Panel de Control de Expedientes',
            'total_expedientes': total_expedientes,
            'expedientes_activos': expedientes_activos,
            'expedientes_completados': expedientes_completados,
            'ultimos_expedientes': ultimos_expedientes,
            'actividades_recientes': actividades_recientes,
        }
        
        return render(request, 'digitalizacion/expedientes/dashboard.html', context)
        
    except Exception as e:
        logger.error(f'Error en el dashboard de expedientes: {str(e)}')
        messages.error(request, 'Ocurrió un error al cargar el panel de control')
        return redirect('digitalizacion:inicio')
@login_required
def ver_historial(request, expediente_id):
    """
    Vista para ver el historial de un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.view_expediente', expediente):
            messages.error(request, 'No tiene permiso para ver el historial de este expediente')
            return redirect('expedientes:lista')
        
        # Obtener el historial del expediente
        historial = HistorialExpediente.objects.filter(
            expediente=expediente
        ).select_related('usuario').order_by('-fecha_accion')
        
        # Paginación
        page = request.GET.get('page', 1)
        paginator = Paginator(historial, 20)  # 20 registros por página
        
        try:
            historial_pagina = paginator.page(page)
        except PageNotAnInteger:
            historial_pagina = paginator.page(1)
        except EmptyPage:
            historial_pagina = paginator.page(paginator.num_pages)
        
        context = {
            'expediente': expediente,
            'historial': historial_pagina,
            'titulo': f'Historial - {expediente.numero}'
        }
        
        return render(request, 'digitalizacion/expedientes/historial.html', context)
        
    except Expediente.DoesNotExist:
        messages.error(request, 'El expediente solicitado no existe')
        return redirect('expedientes:lista')
    except Exception as e:
        logger.error(f'Error al cargar el historial del expediente {expediente_id}: {str(e)}')
        messages.error(request, 'Ocurrió un error al cargar el historial del expediente')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
@require_http_methods(["POST"])
def completar_etapa(request, expediente_id):
    """
    Vista para marcar una etapa como completada en un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        etapa = request.POST.get('etapa')
        
        if not etapa:
            return JsonResponse({'success': False, 'error': 'No se especificó la etapa a completar'}, status=400)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.change_expediente', expediente):
            return JsonResponse({'success': False, 'error': 'No tiene permiso para completar esta etapa'}, status=403)
        
        # Actualizar el estado del expediente según la etapa completada
        if hasattr(expediente, f'marcar_{etapa}_completada'):
            getattr(expediente, f'marcar_{etapa}_completada')(request.user)
        else:
            # Si no hay un método específico, actualizar el campo correspondiente
            campo_etapa = f'{etapa}_completada'
            if hasattr(expediente, campo_etapa):
                setattr(expediente, campo_etapa, True)
                expediente.save()
            else:
                return JsonResponse({'success': False, 'error': f'Etapa {etapa} no válida'}, status=400)
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'ETAPA_COMPLETADA_{etapa.upper()}',
            detalles=f'Se marcó como completada la etapa: {etapa}'
        )
        
        return JsonResponse({'success': True})
        
    except Expediente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expediente no encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Error al completar etapa: {str(e)}')
        return JsonResponse({'success': False, 'error': 'Error al completar la etapa'}, status=500)

@login_required
def obtener_documentos_area(request, expediente_id, area_id):
    """
    Vista para obtener los documentos de un área específica de un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        area = get_object_or_404(AreaTipoExpediente, id=area_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.view_expediente', expediente):
            return JsonResponse({
                'success': False,
                'error': 'No tiene permiso para ver los documentos de este expediente'
            }, status=403)
        
        # Obtener documentos del área específica con relaciones optimizadas
        documentos = DocumentoExpediente.objects.filter(
            expediente=expediente,
            area=area
        ).select_related('subido_por', 'area', 'expediente').order_by('-fecha_subida')
        
        # Preparar datos para la respuesta
        documentos_data = []
        for doc in documentos:
            try:
                # Verificar que el documento tenga archivo
                if not doc.archivo:
                    logger.warning(f'Documento {doc.id} no tiene archivo asociado, omitiendo')
                    continue
                
                # Obtener el nombre del archivo
                nombre_archivo = os.path.basename(doc.archivo.name) if doc.archivo and hasattr(doc.archivo, 'name') else 'documento'
                
                # Formatear la fecha de subida con fecha y hora (convertir a zona horaria local)
                fecha_subida = ''
                fecha_subida_completa = ''
                if doc.fecha_subida:
                    try:
                        # Convertir a zona horaria local antes de formatear
                        fecha_local = timezone.localtime(doc.fecha_subida)
                        fecha_subida = fecha_local.strftime('%Y-%m-%d')
                        fecha_subida_completa = fecha_local.strftime('%d/%m/%Y %H:%M')
                    except Exception as e:
                        logger.error(f'Error formateando fecha del documento {doc.id}: {str(e)}')
                        fecha_subida = str(doc.fecha_subida)
                        fecha_subida_completa = str(doc.fecha_subida)
                
                # Obtener el nombre del usuario que subió el documento
                usuario = 'Usuario desconocido'
                try:
                    if hasattr(doc, 'subido_por') and doc.subido_por:
                        if hasattr(doc.subido_por, 'get_full_name') and callable(doc.subido_por.get_full_name):
                            nombre_completo = doc.subido_por.get_full_name()
                            usuario = nombre_completo if nombre_completo else doc.subido_por.username
                        elif hasattr(doc.subido_por, 'username'):
                            usuario = doc.subido_por.username
                except Exception as e:
                    logger.warning(f'Error obteniendo usuario del documento {doc.id}: {str(e)}')
                    usuario = 'Usuario desconocido'
                
                # Obtener el tamaño del archivo
                tamano_archivo = 0
                if doc.archivo:
                    # Primero intentar con el campo tamano_archivo del modelo
                    if hasattr(doc, 'tamano_archivo') and doc.tamano_archivo and doc.tamano_archivo > 0:
                        tamano_archivo = doc.tamano_archivo
                    # Si no está disponible, intentar obtenerlo del archivo directamente
                    elif hasattr(doc.archivo, 'size') and doc.archivo.size:
                        tamano_archivo = doc.archivo.size
                        # Actualizar el campo tamano_archivo para futuras consultas
                        if hasattr(doc, 'tamano_archivo'):
                            doc.tamano_archivo = tamano_archivo
                            doc.save(update_fields=['tamano_archivo'])
                
                # Obtener el tipo de archivo basado en la extensión si no está definido
                tipo_archivo = getattr(doc, 'tipo_archivo', None)
                if not tipo_archivo and doc.archivo and hasattr(doc.archivo, 'name'):
                    extension = os.path.splitext(doc.archivo.name)[1][1:].lower()
                    # Mapear extensiones a tipos más legibles
                    tipo_map = {
                        'pdf': 'PDF',
                        'doc': 'DOC',
                        'docx': 'DOCX',
                        'xls': 'XLS',
                        'xlsx': 'XLSX',
                        'jpg': 'JPG',
                        'jpeg': 'JPG',
                        'png': 'PNG',
                        'gif': 'GIF',
                        'txt': 'TXT',
                        'rtf': 'RTF'
                    }
                    tipo_archivo = tipo_map.get(extension, extension.upper() if extension else 'ARCHIVO')
                
                # Si aún no hay tipo, intentar obtenerlo del content_type
                if not tipo_archivo or tipo_archivo == 'ARCHIVO':
                    if hasattr(doc, 'tipo_archivo') and doc.tipo_archivo:
                        content_type = doc.tipo_archivo.lower()
                        if 'pdf' in content_type:
                            tipo_archivo = 'PDF'
                        elif 'word' in content_type or 'document' in content_type:
                            tipo_archivo = 'DOCX' if 'openxml' in content_type else 'DOC'
                        elif 'excel' in content_type or 'spreadsheet' in content_type:
                            tipo_archivo = 'XLSX' if 'openxml' in content_type else 'XLS'
                        elif 'image' in content_type:
                            if 'jpeg' in content_type or 'jpg' in content_type:
                                tipo_archivo = 'JPG'
                            elif 'png' in content_type:
                                tipo_archivo = 'PNG'
                            else:
                                tipo_archivo = 'IMAGEN'
                
                # Construir el objeto de documento
                doc_data = {
                    'id': doc.id,
                    'nombre': doc.nombre_documento or nombre_archivo,
                    'nombre_archivo': nombre_archivo,
                    'descripcion': doc.descripcion or '',
                    'observaciones': doc.descripcion or '',  # Alias para observaciones
                    'fecha_subida': fecha_subida,  # Fecha en formato YYYY-MM-DD para ordenamiento
                    'fecha_subida_completa': fecha_subida_completa,  # Fecha y hora formateada
                    'subido_por': usuario,  # Nombre del usuario que subió el documento
                    'archivo_url': reverse('expedientes:ver_documento_drive', args=[doc.id]) if doc.archivo_drive_id else (doc.archivo.url if doc.archivo and hasattr(doc.archivo, 'url') else None),
                    'tipo': tipo_archivo or 'ARCHIVO',
                    'tipo_archivo': tipo_archivo or 'ARCHIVO',  # Alias para compatibilidad
                    'tamano_archivo': tamano_archivo,  # Tamaño en bytes
                    'tamano_formateado': formatear_tamano(tamano_archivo)  # Tamaño formateado (KB, MB, etc.)
                }
                
                documentos_data.append(doc_data)
                
            except Exception as e:
                logger.error(f'Error al procesar documento {doc.id}: {str(e)}')
                logger.error(f'Traceback: {traceback.format_exc()}')
                continue
        
        return JsonResponse({
            'success': True,
            'expediente': {
                'id': expediente.id,
                'numero': expediente.numero_expediente,
                'descripcion': expediente.descripcion
            },
            'area': {
                'id': area.id,
                'nombre': area.nombre,
                'descripcion': area.descripcion
            },
            'documentos': documentos_data,
            'total': len(documentos_data)
        })
        
    except Expediente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expediente no encontrado'}, status=404)
    except AreaTipoExpediente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Área no encontrada'}, status=404)
    except Exception as e:
        logger.error(f'Error al obtener documentos del área: {str(e)}')
        return JsonResponse({
            'success': False, 
            'error': 'Error al obtener los documentos del área',
            'debug': str(e) if settings.DEBUG else None
        }, status=500)

@login_required
@require_http_methods(["POST"])
def eliminar_documento_area(request, documento_id):
    """
    Vista para eliminar un documento de un área específica de un expediente
    """
    try:
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        expediente = documento.expediente
        
        # Verificar permisos
        if not (request.user == expediente.creado_por or 
                request.user.is_staff or 
                request.user.has_perm('digitalizacion.delete_documentoexpediente')):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para eliminar este documento.'}, 
                status=403
            )
        
        # Obtener el nombre del área para el mensaje del historial
        nombre_area = documento.area.nombre if documento.area else "Sin área específica"
        
        # Eliminar el archivo físico si existe
        if documento.archivo:
            if os.path.isfile(documento.archivo.path):
                try:
                    os.remove(documento.archivo.path)
                except Exception as e:
                    logger.error(f"Error al eliminar archivo físico {documento.archivo.path}: {str(e)}")
        
        # Registrar la acción en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Documento eliminado: {documento.nombre_documento} (Área: {nombre_area})',
            detalles=f'Documento eliminado: {documento.nombre_documento}'
        )
        
        # Eliminar el registro de la base de datos
        documento_nombre = documento.nombre_documento
        documento.delete()
        
        # Actualizar el progreso del expediente después de eliminar el documento
        # Esto cambiará el estado de 'completo' a 'en_proceso' si el progreso baja del 100%
        nuevo_progreso = expediente.actualizar_progreso()
        logger.info(f"Progreso del expediente {expediente.id} actualizado a {nuevo_progreso}% después de eliminar documento")
        
        return JsonResponse({
            'success': True, 
            'message': f'Documento "{documento_nombre}" eliminado correctamente del área.',
            'progreso': nuevo_progreso,
            'estado': expediente.estado
        })
        
    except Exception as e:
        logger.error(f"Error en eliminar_documento_area: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': f'Ocurrió un error al intentar eliminar el documento: {str(e)}'
        }, status=500)

@login_required
def obtener_detalles_expediente(request, expediente_id):
    """
    Obtiene los detalles de un expediente en formato JSON
    """
    try:
        from django.core.exceptions import PermissionDenied
        from django.http import JsonResponse
        from django.shortcuts import get_object_or_404
        from django.db.models import Q
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Obtener el expediente
        try:
            expediente = get_object_or_404(Expediente, id=expediente_id)
        except Exception as e:
            logger.error(f'Error al buscar expediente {expediente_id}: {str(e)}')
            return JsonResponse(
                {'success': False, 'error': 'Error al buscar el expediente'}, 
                status=500
            )
        
        # Verificar permisos - todos los usuarios autenticados pueden ver expedientes
        if not puede_ver_expedientes(request.user):
            logger.warning(f'Intento de acceso no autorizado al expediente {expediente_id} por el usuario {request.user.username}')
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para ver expedientes'}, 
                status=403
            )
        
        # Obtener documentos agrupados por área
        documentos_por_area = {}
        try:
            for doc in expediente.documentos.all().select_related('area'):
                try:
                    area_nombre = doc.area.nombre if doc.area else 'Sin asignar'
                    if area_nombre not in documentos_por_area:
                        documentos_por_area[area_nombre] = []
                    
                    doc_data = {
                        'id': doc.id,
                        'nombre': doc.nombre_documento,  # Changed from nombre_archivo to nombre_documento
                        'tipo': doc.tipo_archivo or 'Documento',  # Changed to use tipo_archivo field
                        'fecha_subida': doc.fecha_subida.strftime('%d/%m/%Y %H:%M') if hasattr(doc, 'fecha_subida') and doc.fecha_subida else 'Fecha no disponible',
                        'tamano': f"{(doc.tamano_archivo / 1024):.1f} KB" if hasattr(doc, 'tamano_archivo') and doc.tamano_archivo else '0 KB',
                        'url': doc.archivo.url if hasattr(doc, 'archivo') and doc.archivo else '#',
                        'puede_eliminar': request.user.has_perm('digitalizacion.delete_documentoexpediente') or request.user == getattr(doc, 'subido_por', None)
                    }
                    documentos_por_area[area_nombre].append(doc_data)
                except Exception as e:
                    logger.error(f'Error al procesar documento {getattr(doc, "id", "desconocido")}: {str(e)}')
                    continue
        except Exception as e:
            logger.error(f'Error al obtener documentos del expediente {expediente_id}: {str(e)}')
            documentos_por_area = {'Error': ['No se pudieron cargar los documentos']}
        
        # Obtener historial de cambios
        historial_data = []
        try:
            from .models import HistorialExpediente
            historial = HistorialExpediente.objects.filter(
                expediente=expediente
            ).select_related('usuario').order_by('-fecha')[:50]
            
            historial_data = [{
                'fecha': h.fecha.strftime('%d/%m/%Y %H:%M') if hasattr(h, 'fecha') and h.fecha else 'Fecha no disponible',
                'usuario': h.usuario.get_full_name() or getattr(h.usuario, 'username', 'Usuario desconocido'),
                'accion': getattr(h, 'accion', 'Acción no especificada'),
                'detalles': getattr(h, 'comentario', getattr(h, 'observaciones', '')) or ''
            } for h in historial]
        except Exception as e:
            logger.error(f'Error al obtener historial del expediente {expediente_id}: {str(e)}')
            historial_data = [{'error': 'No se pudo cargar el historial'}]
        
        # Datos del expediente
        try:
            creado_por = {
                'id': expediente.creado_por.id,
                'nombre': expediente.creado_por.get_full_name() or expediente.creado_por.username,
                'username': expediente.creado_por.username
            } if hasattr(expediente, 'creado_por') and expediente.creado_por else None
            
            asignado_a = None
            if hasattr(expediente, 'asignado_a') and expediente.asignado_a:
                asignado_a = {
                    'id': expediente.asignado_a.id,
                    'nombre': expediente.asignado_a.get_full_name() or expediente.asignado_a.username,
                    'username': expediente.asignado_a.username
                }
                
            area_actual = None
            if hasattr(expediente, 'area_actual') and expediente.area_actual:
                area_actual = {
                    'id': expediente.area_actual.id,
                    'nombre': expediente.area_actual.nombre
                }
            
            # Obtener el departamento y el usuario creador con valores por defecto seguros
            departamento_nombre = getattr(expediente.departamento, 'nombre', 'No asignado') if hasattr(expediente, 'departamento') and expediente.departamento else 'No asignado'
            creado_por_nombre = getattr(expediente.creado_por, 'get_full_name', lambda: getattr(expediente.creado_por, 'username', 'Usuario desconocido'))() if hasattr(expediente, 'creado_por') and expediente.creado_por else 'Usuario desconocido'
            
            # Construir los datos del expediente en el formato que espera la plantilla
            expediente_data = {
                'id': expediente.id,
                'numero_expediente': getattr(expediente, 'numero_expediente', 'N/A'),
                'titulo': getattr(expediente, 'titulo', 'Sin título'),
                'descripcion': getattr(expediente, 'descripcion', 'Sin descripción'),
                'estado_actual': getattr(expediente, 'get_estado_display', lambda: 'En proceso')(),
                'fecha_creacion': expediente.fecha_creacion.isoformat() if hasattr(expediente, 'fecha_creacion') else None,
                'departamento': departamento_nombre,
                'creado_por': creado_por_nombre,
                'documentos_count': expediente.documentos.count() if hasattr(expediente, 'documentos') else 0,
                'etapas_count': len(set(doc.area_id for doc in expediente.documentos.all() if hasattr(doc, 'area_id') and doc.area_id is not None)) if hasattr(expediente, 'documentos') else 0,
                'tipo_expediente': getattr(expediente, 'get_tipo_expediente_display', lambda: 'No especificado')(),
                'subtipo_expediente': getattr(expediente, 'get_subtipo_expediente_display', lambda: 'No especificado')(),
                'documentos_por_area': documentos_por_area,
                'historial': historial_data,
                'permisos': {
                    'editar': request.user.has_perm('digitalizacion.change_expediente', expediente),
                    'eliminar': request.user.has_perm('digitalizacion.delete_expediente', expediente),
                    'cambiar_estado': request.user.has_perm('digitalizacion.change_estado_expediente', expediente),
                    'subir_documentos': request.user.has_perm('digitalizacion.add_documentoexpediente')
                }
            }
            
            return JsonResponse({
                'success': True,
                'expediente': expediente_data
            })
            
        except Exception as e:
            logger.error(f'Error al procesar datos del expediente {expediente_id}: {str(e)}', exc_info=True)
            return JsonResponse(
                {'success': False, 'error': 'Error al procesar los datos del expediente'}, 
                status=500
            )
            
    except Exception as e:
        logger.error(f'Error inesperado en obtener_detalles_expediente: {str(e)}', exc_info=True)
        return JsonResponse(
            {'success': False, 'error': 'Error interno del servidor al procesar la solicitud'}, 
            status=500
        )

def obtener_usuarios_mencion(request):
    """
    Busca usuarios para mencionar en comentarios o notificaciones
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({
                'success': True,
                'usuarios': []
            })
        
        # Buscar usuarios que coincidan con la consulta
        usuarios = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id).distinct()[:10]
        
        # Formatear la respuesta
        usuarios_data = [{
            'id': usuario.id,
            'username': usuario.username,
            'nombre_completo': f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username,
            'iniciales': f"{usuario.first_name[0] if usuario.first_name else ''}{usuario.last_name[0] if usuario.last_name else ''}".upper() or usuario.username[0].upper(),
            'email': usuario.email,
            'foto': usuario.perfil.foto.url if hasattr(usuario, 'perfil') and usuario.perfil.foto else None
        } for usuario in usuarios]
        
        return JsonResponse({
            'success': True,
            'usuarios': usuarios_data
        })
        
    except Exception as e:
        logger.error(f'Error al buscar usuarios para mención: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al buscar usuarios'}, 
            status=500
        )

@login_required
def obtener_notificaciones(request):
    """
    Obtiene las notificaciones del usuario actual
    """
    try:
        # Obtener las últimas 20 notificaciones no leídas
        notificaciones = Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).select_related('expediente').order_by('-fecha_creacion')[:20]
        
        # Formatear las notificaciones
        notificaciones_data = [{
            'id': notif.id,
            'mensaje': notif.mensaje,
            'fecha_creacion': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'leida': notif.leida,
            'tipo': notif.tipo,
            'url': notif.get_absolute_url() if hasattr(notif, 'get_absolute_url') else '#'
        } for notif in notificaciones]
        
        # Contar notificaciones no leídas
        total_no_leidas = Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'notificaciones': notificaciones_data,
            'total_no_leidas': total_no_leidas
        })
        
    except Exception as e:
        logger.error(f'Error al obtener notificaciones: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al cargar las notificaciones'}, 
            status=500
        )

def listar_areas(request):
    """
    Vista para listar todas las áreas disponibles
    """
    try:
        # Obtener todas las áreas activas
        areas = AreaTipoExpediente.objects.filter(activo=True).order_by('nombre')
        
        # Preparar la respuesta
        areas_data = [{
            'id': area.id,
            'nombre': area.nombre,
            'descripcion': area.descripcion,
            'icono': area.icono if hasattr(area, 'icono') else 'folder',
            'color': area.color if hasattr(area, 'color') else '#6c757d'
        } for area in areas]
        
        return JsonResponse({
            'success': True,
            'areas': areas_data
        })
        
    except Exception as e:
        logger.error(f'Error al listar áreas: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al obtener la lista de áreas'}, 
            status=500
        )

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación como leída
    """
    try:
        # Obtener la notificación
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        
        # Verificar que la notificación pertenezca al usuario actual
        if notificacion.usuario != request.user and not request.user.is_staff:
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para marcar esta notificación'}, 
                status=403
            )
        
        # Marcar como leída
        notificacion.leida = True
        notificacion.fecha_leida = timezone.now()
        notificacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída',
            'notificacion_id': notificacion.id
        })
        
    except Notificacion.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Notificación no encontrada'}, 
            status=404
        )
    except Exception as e:
        logger.error(f'Error al marcar notificación como leída: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al procesar la solicitud'}, 
            status=500
        )

@login_required
def crear_comentario_area(request, expediente_id):
    """
    Vista para crear un comentario en un área específica de un expediente
    """
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Método no permitido'}, 
            status=405
        )
    
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        data = json.loads(request.body)
        
        # Validar que el usuario tenga permiso para comentar
        if not (request.user.has_perm('digitalizacion.comment_expediente', expediente) or 
                request.user.is_staff or 
                request.user == expediente.creado_por):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para comentar en este expediente'}, 
                status=403
            )
        
        # Validar datos del comentario
        contenido = data.get('contenido', '').strip()
        area_id = data.get('area_id')
        
        if not contenido:
            return JsonResponse(
                {'success': False, 'error': 'El contenido del comentario es requerido'}, 
                status=400
            )
        
        # Crear el comentario
        comentario = ComentarioArea.objects.create(
            expediente=expediente,
            area_id=area_id,
            usuario=request.user,
            contenido=contenido
        )
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=f'Comentario agregado en área: {comentario.area.nombre if comentario.area else "General"}',
            detalles=contenido[:100]  # Guardar los primeros 100 caracteres
        )
        
        # Preparar datos de respuesta
        response_data = {
            'success': True,
            'comentario': {
                'id': comentario.id,
                'contenido': comentario.contenido,
                'fecha_creacion': comentario.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'usuario': {
                    'id': request.user.id,
                    'nombre': request.user.get_full_name() or request.user.username,
                    'foto': request.user.perfil.foto.url if hasattr(request.user, 'perfil') and request.user.perfil.foto else None
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Formato de datos inválido'}, 
            status=400
        )
    except Expediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Expediente no encontrado'}, 
            status=404
        )
    except Exception as e:
        logger.error(f'Error al crear comentario: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al crear el comentario'}, 
            status=500
        )

@login_required
@require_http_methods(["POST"])
def enviar_mensaje_expediente(request, expediente_id):
    """
    Vista para enviar un mensaje en un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        data = json.loads(request.body)
        
        # Verificar que el usuario tenga permiso para ver el expediente
        if not request.user.has_perm('digitalizacion.view_expediente', expediente):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para ver este expediente'}, 
                status=403
            )
        
        # Validar el contenido del mensaje
        contenido = data.get('contenido', '').strip()
        if not contenido:
            return JsonResponse(
                {'success': False, 'error': 'El contenido del mensaje es requerido'}, 
                status=400
            )
        
        # Crear el mensaje
        mensaje = MensajeExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            contenido=contenido
        )
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion='Nuevo mensaje en el expediente',
            detalles=f'Mensaje: {contenido[:100]}...'
        )
        
        # Notificar a los usuarios mencionados
        mencionados = re.findall(r'@(\w+)', contenido)
        if mencionados:
            for username in mencionados:
                try:
                    usuario_men = User.objects.get(username=username)
                    if usuario_men != request.user:  # No notificar al remitente
                        Notificacion.objects.create(
                            usuario=usuario_men,
                            titulo=f'Mencionado en expediente {expediente.numero_expediente}',
                            mensaje=f'{request.user.get_full_name()} te mencionó en un mensaje: {contenido[:100]}...',
                            url=reverse('expedientes:detalle', args=[expediente.id])
                        )
                except User.DoesNotExist:
                    continue
        
        # Notificar a los participantes del expediente (excepto al remitente)
        participantes = set()
        
        # Agregar creador del expediente
        if expediente.creado_por != request.user:
            participantes.add(expediente.creado_por)
            
        # Agregar usuario asignado si existe
        if expediente.asignado_a and expediente.asignado_a != request.user:
            participantes.add(expediente.asignado_a)
            
        # Notificar a los participantes
        for participante in participantes:
            Notificacion.objects.create(
                usuario=participante,
                titulo=f'Nuevo mensaje en expediente {expediente.numero_expediente}',
                mensaje=f'{request.user.get_full_name()} ha enviado un mensaje en el expediente: {contenido[:100]}...',
                url=reverse('expedientes:detalle', args=[expediente.id])
            )
        
        return JsonResponse({
            'success': True,
            'mensaje': {
                'id': mensaje.id,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%d/%m/%Y %H:%M'),
                'usuario': {
                    'id': request.user.id,
                    'nombre': request.user.get_full_name() or request.user.username,
                    'foto': request.user.perfil.foto.url if hasattr(request.user, 'perfil') and request.user.perfil.foto else None
                }
            }
        })
        
    except Expediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Expediente no encontrado'}, 
            status=404
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Formato de datos inválido'}, 
            status=400
        )
    except Exception as e:
        logger.error(f'Error al enviar mensaje en expediente {expediente_id}: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al enviar el mensaje'}, 
            status=500
        )

@login_required
def obtener_mensajes_expediente(request, expediente_id):
    """
    Vista para obtener los mensajes de un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar que el usuario tenga permiso para ver el expediente
        if not request.user.has_perm('digitalizacion.view_expediente', expediente):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para ver este expediente'}, 
                status=403
            )
        
        # Obtener los últimos 50 mensajes del expediente
        mensajes = MensajeExpediente.objects.filter(
            expediente=expediente
        ).select_related('usuario').order_by('fecha_envio')[:50]
        
        # Formatear los mensajes
        mensajes_data = []
        for mensaje in mensajes:
            mensajes_data.append({
                'id': mensaje.id,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%d/%m/%Y %H:%M'),
                'es_mio': mensaje.usuario == request.user,
                'usuario': {
                    'id': mensaje.usuario.id,
                    'nombre': mensaje.usuario.get_full_name() or mensaje.usuario.username,
                    'foto': mensaje.usuario.perfil.foto.url if hasattr(mensaje.usuario, 'perfil') and mensaje.usuario.perfil.foto else None
                }
            })
        
        return JsonResponse({
            'success': True,
            'mensajes': mensajes_data
        })
        
    except Expediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Expediente no encontrado'}, 
            status=404
        )
    except Exception as e:
        logger.error(f'Error al obtener mensajes del expediente {expediente_id}: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al cargar los mensajes'}, 
            status=500
        )

@login_required
@require_http_methods(["POST"])
def enviar_mensaje_usuario(request):
    """
    Vista para enviar un mensaje directo a otro usuario
    """
    try:
        data = json.loads(request.body)
        
        # Validar datos del formulario
        usuario_destino_id = data.get('usuario_id')
        asunto = data.get('asunto', '').strip()
        contenido = data.get('contenido', '').strip()
        
        if not usuario_destino_id or not contenido:
            return JsonResponse(
                {'success': False, 'error': 'Usuario destino y contenido son requeridos'}, 
                status=400
            )
        
        # Verificar que el usuario destino exista
        try:
            usuario_destino = User.objects.get(id=usuario_destino_id)
        except User.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': 'Usuario destino no encontrado'}, 
                status=404
            )
        
        # Crear el mensaje
        mensaje = MensajeExpediente.objects.create(
            remitente=request.user,
            destinatario=usuario_destino,
            asunto=asunto,
            contenido=contenido
        )
        
        # Notificar al usuario
        Notificacion.objects.create(
            usuario=usuario_destino,
            titulo=f'Nuevo mensaje de {request.user.get_full_name()}',
            mensaje=f'Asunto: {asunto}\n{contenido[:100]}...',
            tipo='mensaje_privado',
            url=reverse('mensajes:ver', args=[mensaje.id])
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Mensaje enviado correctamente',
            'mensaje_id': mensaje.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Formato de datos inválido'}, 
            status=400
        )
    except Exception as e:
        logger.error(f'Error al enviar mensaje privado: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al enviar el mensaje'}, 
            status=500
        )

@login_required
@require_http_methods(["POST"])
def agregar_sima(request, expediente_id):
    """
    Vista para agregar un número SIMA a un expediente
    """
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        data = json.loads(request.body)
        
        # Verificar permisos (solo administradores o usuarios con permiso específico pueden agregar SIMA)
        if not (request.user.is_staff or request.user.has_perm('digitalizacion.add_sima')):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para realizar esta acción'}, 
                status=403
            )
        
        # Validar el número SIMA
        numero_sima = data.get('numero_sima', '').strip()
        if not numero_sima:
            return JsonResponse(
                {'success': False, 'error': 'El número SIMA es requerido'}, 
                status=400
            )
        
        # Verificar si el número SIMA ya está en uso
        if Expediente.objects.filter(numero_sima=numero_sima).exclude(id=expediente_id).exists():
            return JsonResponse(
                {'success': False, 'error': 'Este número SIMA ya está siendo utilizado por otro expediente'}, 
                status=400
            )
        
        # Guardar el número SIMA
        expediente.numero_sima = numero_sima
        expediente.fecha_actualizacion = timezone.now()
        expediente.save()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion='Número SIMA actualizado',
            descripcion=f'Nuevo número SIMA asignado: {numero_sima}'
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Número SIMA actualizado correctamente',
            'numero_sima': numero_sima,
            'fecha_actualizacion': expediente.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')
        })
        
    except Expediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Expediente no encontrado'}, 
            status=404
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Formato de datos inválido'}, 
            status=400
        )
    except Exception as e:
        logger.error(f'Error al actualizar número SIMA para el expediente {expediente_id}: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error al actualizar el número SIMA'}, 
            status=500
        )

@login_required
def buscar_expedientes(request):
    """
    Vista para buscar expedientes según diferentes criterios
    """
    try:
        query = request.GET.get('q', '').strip()
        tipo = request.GET.get('tipo', '')
        estado = request.GET.get('estado', '')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        creado_por = request.GET.get('creado_por', '')
        asignado_a = request.GET.get('asignado_a', '')
        
        # Construir la consulta base
        expedientes = Expediente.objects.all()
        
        # Aplicar filtros según los parámetros recibidos
        if query:
            expedientes = expedientes.filter(
                Q(numero_expediente__icontains=query) |
                Q(asunto__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(numero_sima__icontains=query)
            )
            
        if tipo:
            expedientes = expedientes.filter(tipo=tipo)
            
        if estado:
            expedientes = expedientes.filter(estado=estado)
            
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                expedientes = expedientes.filter(fecha_creacion__date__gte=fecha_desde_dt)
            except ValueError:
                pass
                
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                expedientes = expedientes.filter(fecha_creacion__date__lte=fecha_hasta_dt)
            except ValueError:
                pass
                
        if creado_por:
            expedientes = expedientes.filter(creado_por__username__icontains=creado_por)
            
        if asignado_a:
            expedientes = expedientes.filter(asignado_a__username__icontains=asignado_a)
        
        # Ordenar por fecha de creación descendente
        expedientes = expedientes.order_by('-fecha_creacion')
        
        # Paginación
        page = request.GET.get('page', 1)
        paginator = Paginator(expedientes, 20)  # 20 expedientes por página
        
        try:
            expedientes_pagina = paginator.page(page)
        except PageNotAnInteger:
            expedientes_pagina = paginator.page(1)
        except EmptyPage:
            expedientes_pagina = paginator.page(paginator.num_pages)
        
        # Preparar los datos para la respuesta
        expedientes_data = []
        for exp in expedientes_pagina:
            expedientes_data.append({
                'id': exp.id,
                'numero_expediente': exp.numero_expediente,
                'tipo': exp.get_tipo_display(),
                'asunto': exp.asunto,
                'estado': exp.get_estado_display(),
                'fecha_creacion': exp.fecha_creacion.strftime('%d/%m/%Y'),
                'creado_por': exp.creado_por.get_full_name() or exp.creado_por.username,
                'asignado_a': exp.asignado_a.get_full_name() if exp.asignado_a else 'No asignado',
                'url': reverse('expedientes:detalle_expediente', args=[exp.id])
            })
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'expedientes': expedientes_data,
                'has_next': expedientes_pagina.has_next(),
                'has_previous': expedientes_pagina.has_previous(),
                'page_number': expedientes_pagina.number,
                'num_pages': paginator.num_pages,
                'count': paginator.count
            })
            
        # Si no es AJAX, renderizar la plantilla
        return render(request, 'expedientes/buscar_expedientes.html', {
            'expedientes': expedientes_pagina,
            'query': query,
            'tipos': Expediente.TIPO_CHOICES,
            'estados': Expediente.ESTADO_CHOICES,
            'filtros': {
                'tipo': tipo,
                'estado': estado,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'creado_por': creado_por,
                'asignado_a': asignado_a
            }
        })
        
    except Exception as e:
        logger.error(f'Error al buscar expedientes: {str(e)}')
        
        # Si es AJAX, devolver error en JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Error al realizar la búsqueda'
            }, status=500)
            
        # Si no es AJAX, mostrar mensaje de error
        messages.error(request, 'Ocurrió un error al realizar la búsqueda')
        return redirect('expedientes:lista_expedientes')

def obtener_mensajes_usuario(request, usuario_id):
    """Vista AJAX para obtener mensajes entre dos usuarios"""
    try:
        usuario = User.objects.get(id=usuario_id)
        # Buscar expedientes que contengan conversaciones entre los dos usuarios
        expedientes = Expediente.objects.filter(
            Q(creado_por=request.user) |
            Q(creado_por=usuario)
        )
        mensajes = MensajeExpediente.objects.filter(
            expediente__in=expedientes
        ).select_related('usuario').order_by('fecha_envio')
        mensajes_data = []
        for mensaje in mensajes:
            mensajes_data.append({
                'id': mensaje.id,
                'contenido': mensaje.contenido,
                'usuario': mensaje.usuario.get_full_name() or mensaje.usuario.username,
                'fecha_envio': mensaje.fecha_envio.strftime('%H:%M'),
                'es_mio': mensaje.usuario == request.user
            })
        return JsonResponse({'success': True, 'mensajes': mensajes_data})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
@require_http_methods(["POST"])
def eliminar_documento_expediente(request, expediente_id, documento_id):
    """
    Vista para eliminar un documento de un expediente
    """
    try:
        # Obtener el documento y verificar que pertenezca al expediente
        documento = get_object_or_404(
            DocumentoExpediente, 
            id=documento_id, 
            expediente_id=expediente_id
        )
        
        expediente = documento.expediente
        
        # Verificar permisos
        if not (request.user.has_perm('digitalizacion.delete_documentoexpediente') or 
                request.user == documento.subido_por or
                request.user == expediente.creado_por):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para eliminar este documento.'},
                    status=403
                )
            messages.error(request, 'No tiene permiso para eliminar este documento.')
            return redirect('expedientes:detalle_expediente', expediente_id=expediente_id)
        
        # Guardar información para el historial
        doc_nombre = documento.nombre_documento
        area = documento.area if hasattr(documento, 'area') else None
        
        # Eliminar el archivo físico si existe
        if documento.archivo and hasattr(documento.archivo, 'path') and os.path.isfile(documento.archivo.path):
            try:
                os.remove(documento.archivo.path)
            except Exception as e:
                logger.error(f'Error al eliminar archivo físico {documento.archivo.path}: {str(e)}')
        
        # Eliminar el registro de la base de datos
        documento.delete()
        
        # Recalcular el progreso
        from .models import AreaTipoExpediente, EtapaExpediente
        
        # Obtener todas las áreas para este tipo de expediente
        areas_etapas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            activa=True
        )
        
        if getattr(expediente, 'subtipo_expediente', None):
            areas_etapas = areas_etapas.filter(
                Q(subtipo_expediente=expediente.subtipo_expediente) |
                Q(subtipo_expediente__isnull=True) |
                Q(subtipo_expediente='')
            )
        
        total_etapas = areas_etapas.count()
        etapas_completadas = 0
        
        # Verificar cada área para ver si está completada
        for area_etapa in areas_etapas:
            # Verificar si el área tiene documentos
            tiene_documentos = expediente.documentos.filter(area=area_etapa).exists()
            
            # Obtener el nombre de la etapa desde el área
            nombre_etapa = area_etapa.nombre  # Ajusta esto según el campo correcto en AreaTipoExpediente
            
            # Actualizar o crear registro de EtapaExpediente
            etapa, created = EtapaExpediente.objects.update_or_create(
                expediente=expediente,
                nombre_etapa=nombre_etapa,
                defaults={
                    'completada': tiene_documentos,
                    'fecha_completada': timezone.now() if tiene_documentos else None,
                    'completada_por': request.user if tiene_documentos else None
                }
            )
            
            if tiene_documentos:
                etapas_completadas += 1
        
        # Calcular progreso
        progreso = int((etapas_completadas / total_etapas) * 100) if total_etapas > 0 else 0
        
        # Actualizar el progreso y el estado del expediente usando el método del modelo
        # Esto automáticamente cambiará el estado de 'completo' a 'en_proceso' si el progreso baja del 100%
        nuevo_progreso = expediente.actualizar_progreso()
        logger.info(f"Expediente {expediente.id} - Progreso actualizado a {nuevo_progreso}% después de eliminar documento")
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion='Documento eliminado',
            descripcion=f'Se eliminó el documento: {doc_nombre}'
        )
        
        # Si es una petición AJAX, devolver respuesta JSON con datos de progreso
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Documento eliminado correctamente',
                'documento_id': documento_id,
                'progreso': progreso,
                'etapas_completadas': etapas_completadas,
                'total_etapas': total_etapas
            })
        
        messages.success(request, f'Documento "{doc_nombre}" eliminado correctamente.')
        return redirect('expedientes:editar_expediente', expediente_id=expediente_id)
        
    except DocumentoExpediente.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'El documento no existe o no pertenece a este expediente'},
                status=404
            )
        messages.error(request, 'El documento no existe o no pertenece a este expediente')
        return redirect('expedientes:detalle_expediente', expediente_id=expediente_id)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f'Error al eliminar documento {documento_id} del expediente {expediente_id}: {str(e)}\n{error_trace}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # In development, return detailed error information
            if settings.DEBUG:
                return JsonResponse({
                    'success': False, 
                    'error': f'Error al eliminar el documento: {str(e)}',
                    'trace': error_trace
                }, status=500)
            # In production, return a generic error message
            return JsonResponse(
                {'success': False, 'error': 'Ocurrió un error al intentar eliminar el documento'},
                status=500
            )
        messages.error(request, f'Ocurrió un error al intentar eliminar el documento: {str(e)}')
        return redirect('expedientes:editar_expediente', expediente_id=expediente_id)

@login_required
def ver_documento_expediente(request, documento_id):
    """
    Vista para ver los detalles de un documento de un expediente
    """
    try:
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.view_documentoexpediente', documento):
            return HttpResponseForbidden(b"No tiene permiso para ver este documento")
            
        context = {
            'documento': documento,
            'expediente': documento.expediente,
            'puede_editar': request.user.has_perm('digitalizacion.change_documentoexpediente', documento),
            'puede_eliminar': request.user.has_perm('digitalizacion.delete_documentoexpediente', documento),
        }
        
        return render(request, 'digitalizacion/expedientes/ver_documento.html', context)
        
    except Exception as e:
        logger.error(f'Error al ver documento {documento_id}: {str(e)}')
        messages.error(request, 'Ocurrió un error al intentar ver el documento')
        return redirect('expedientes:lista')

@login_required
def ver_documento_drive(request, documento_id):
    """
    Vista para ver un documento desde Google Drive
    Redirige al usuario al visor de Google Drive
    """
    try:
        # Buscamos el documento en la base de datos de Neon
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        
        # Verificar permisos básicos
        if not puede_ver_expedientes(request.user):
            messages.error(request, 'No tienes permiso para ver este documento')
            return redirect('expedientes:lista')
        
        if documento.archivo_drive_id:
            try:
                from .drive_service import get_view_link
                # Pedimos el link a Google
                link = get_view_link(documento.archivo_drive_id)
                # Redirigimos al usuario al visor de Google Drive
                return redirect(link)
            except Exception as e:
                logger.error(f"Error al obtener enlace de Drive para documento {documento_id}: {str(e)}", exc_info=True)
                messages.error(request, 'Error al obtener el enlace del documento desde Google Drive')
                return redirect('expedientes:detalle', expediente_id=documento.expediente.id)
        else:
            # Si no tiene ID de Drive, intentar usar el archivo local como fallback
            if documento.archivo:
                # Redirigir al archivo local
                return redirect(documento.archivo.url)
            else:
                messages.warning(request, 'Este documento no tiene un ID de Drive asociado ni archivo local.')
                return redirect('expedientes:detalle', expediente_id=documento.expediente.id)
                
    except Exception as e:
        logger.error(f'Error al ver documento Drive {documento_id}: {str(e)}', exc_info=True)
        messages.error(request, 'Ocurrió un error al intentar ver el documento')
        return redirect('expedientes:lista')

@login_required
@require_http_methods(["GET", "POST"])
def editar_documento_expediente(request, expediente_id, documento_id):
    """
    Vista para editar los metadatos de un documento de un expediente
    """
    documento = get_object_or_404(DocumentoExpediente, id=documento_id, expediente_id=expediente_id)
    
    # Verificar permisos
    if not request.user.has_perm('digitalizacion.change_documentoexpediente', documento):
        return HttpResponseForbidden(b"No tiene permiso para editar este documento")
    
    if request.method == 'POST':
        # Actualizar los campos del documento
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if nombre:
            documento.nombre = nombre
            documento.descripcion = descripcion
            documento.modificado_por = request.user
            documento.fecha_modificacion = timezone.now()
            documento.save()
            
            # Registrar en el historial
            HistorialExpediente.objects.create(
                expediente=documento.expediente,
                usuario=request.user,
                accion=f'Documento actualizado: {documento.nombre}',
                detalles=f'Se actualizaron los metadatos del documento {documento.nombre}.'
            )
            
            messages.success(request, 'Documento actualizado correctamente')
            return redirect('expedientes:ver_documento_expediente', documento_id=documento.id)
        else:
            messages.error(request, 'El nombre del documento es obligatorio')
    
    return render(request, 'digitalizacion/expedientes/editar_documento.html', {
        'documento': documento,
        'expediente': documento.expediente,
        'titulo': f'Editar documento: {documento.nombre}'
    })

@login_required
@require_http_methods(["GET", "POST"])
@permission_required('digitalizacion.view_expediente', raise_exception=True)
def descargar_documento_expediente(request, expediente_id, documento_id):
    """
    Vista para descargar un documento de un expediente
    """
    try:
        documento = get_object_or_404(DocumentoExpediente, id=documento_id, expediente_id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.view_documentoexpediente', documento):
            return HttpResponseForbidden(b"No tiene permiso para descargar este documento")
        
        # Verificar que el archivo existe
        if not documento.archivo or not os.path.isfile(documento.archivo.path):
            raise Http404("El archivo solicitado no existe")
        
        # Obtener el tipo MIME del archivo
        content_type, encoding = mimetypes.guess_type(documento.archivo.name)
        if content_type is None:
            content_type = 'application/octet-stream'
            
        # Configurar la respuesta para la descarga
        response = FileResponse(open(documento.archivo.path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(documento.archivo.name)}"'
        response['Content-Length'] = documento.archivo.size
        
        # Registrar la descarga en el historial
        HistorialExpediente.objects.create(
            expediente=documento.expediente,
            usuario=request.user,
            accion=f'Documento descargado: {documento.nombre}',
            detalles=f'Se descargó el documento {documento.nombre}.'
        )
        
        return response
        
    except DocumentoExpediente.DoesNotExist:
        raise Http404("El documento solicitado no existe")
    except Exception as e:
        logger.error(f'Error al descargar documento {documento_id}: {str(e)}')
        messages.error(request, 'Ocurrió un error al intentar descargar el documento')
        return redirect('expedientes:detalle', expediente_id=expediente_id)

@login_required
def obtener_progreso_expediente(request, expediente_id):
    """
    Vista para obtener el progreso actual de un expediente (usada para actualizaciones en tiempo real)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"[INICIO] Obteniendo progreso para expediente {expediente_id}")
    
    try:
        # Usar select_for_update para bloquear el registro y evitar condiciones de carrera
        with transaction.atomic():
            # Obtener el expediente con bloqueo para evitar condiciones de carrera
            expediente = get_object_or_404(
                Expediente.objects.select_related('departamento', 'creado_por')
                                .select_for_update(nowait=True),
                id=expediente_id
            )
            
            # Verificar permisos
            if not request.user.has_perm('digitalizacion.view_expediente', expediente):
                logger.warning(f"Usuario {request.user.id} no tiene permiso para ver el expediente {expediente_id}")
                return JsonResponse({'error': 'No tiene permiso para ver este expediente.'}, status=403)
            
            # Obtener el tipo de expediente (es un campo, no una relación)
            tipo_expediente = expediente.tipo_expediente
            if not tipo_expediente:
                logger.warning(f"Expediente {expediente_id} no tiene tipo_expediente asignado")
                return JsonResponse({
                    'error': 'El expediente no tiene un tipo de expediente asignado.',
                    'porcentaje': 0,
                    'completadas': 0,
                    'total': 0,
                    'fecha_actualizacion': expediente.fecha_actualizacion.strftime('%d/%m/%Y %H:%M') if expediente.fecha_actualizacion else None
                })
            
            # Obtener todas las áreas/etapas configuradas para este tipo de expediente
            areas_etapas = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_expediente,
                activa=True
            )
            
            # Filtrar por subtipo si existe
            subtipo = getattr(expediente, 'subtipo_expediente', None)
            if subtipo:
                # Obtener áreas específicas para el subtipo o las genéricas (sin subtipo)
                areas_etapas = areas_etapas.filter(
                    Q(subtipo_expediente=subtipo) | 
                    Q(subtipo_expediente__isnull=True) | 
                    Q(subtipo_expediente='')
                )
            else:
                # Si no hay subtipo, solo obtener áreas genéricas
                areas_etapas = areas_etapas.filter(
                    Q(subtipo_expediente__isnull=True) | 
                    Q(subtipo_expediente='')
                )
            
            # Ordenar por orden
            areas_etapas = areas_etapas.order_by('orden')
            
            # Obtener todos los documentos del expediente en una sola consulta
            documentos_expediente = list(expediente.documentos.all().values_list('area_id', flat=True))
            
            # Calcular el progreso
            total_etapas = areas_etapas.count()
            etapas_completadas = 0
            
            # Verificar cada área/etapa
            for area in areas_etapas:
                try:
                    # Verificar si hay documentos en esta área
                    if area.id in documentos_expediente:
                        etapas_completadas += 1
                        continue
                        
                    # Si no hay documentos, verificar si tiene una función personalizada
                    if hasattr(area, 'etapa_completada') and callable(area.etapa_completada):
                        if area.etapa_completada(expediente):
                            etapas_completadas += 1
                except Exception as e:
                    logger.error(f"Error al verificar progreso para área {area.id}: {str(e)}")
            
            # Calcular porcentaje
            progreso = 0
            if total_etapas > 0:
                progreso = min(100, int((etapas_completadas / total_etapas) * 100))
            
            # Obtener la fecha de actualización actual
            fecha_actual = timezone.localtime(timezone.now())
            
            # Verificar si el progreso es 100% y actualizar el estado si es necesario
            if progreso == 100 and expediente.estado != 'completo':
                expediente.estado = 'completo'  # Using 'completo' to match ESTADOS_EXPEDIENTE choices
                # También actualizar estado_actual a 'completado' para que se muestre correctamente en la lista
                if expediente.estado_actual != 'completado':
                    expediente.estado_actual = 'completado'
                update_fields = ['progreso', 'estado', 'estado_actual', 'fecha_actualizacion']
                logger.info(f"[COMPLETO] Expediente {expediente_id} marcado como completo (progreso 100%)")
            # Actualizar el progreso solo si hay cambios
            elif expediente.progreso != progreso:
                update_fields = ['progreso', 'fecha_actualizacion']
            
            # Si hay campos para actualizar, guardar los cambios
            if 'update_fields' in locals():
                expediente.progreso = progreso
                expediente.fecha_actualizacion = timezone.now()
                expediente.save(update_fields=update_fields)
                logger.info(f"[ACTUALIZADO] Progreso del expediente {expediente_id} actualizado a {progreso}%")
            # No hacer nada si no hay cambios en el progreso
            else:
                logger.debug(f"[SIN CAMBIOS] Progreso del expediente {expediente_id} se mantiene en {progreso}%")
            
            # Obtener la fecha y hora actual del servidor
            fecha_actual = timezone.localtime(timezone.now())
            fecha_actual_str = fecha_actual.strftime('%d/%m/%Y %H:%M')
            
            # Obtener el total de documentos del expediente
            total_documentos = expediente.documentos.count()
            
            # Crear la respuesta con la hora actual del servidor
            response_data = {
                'porcentaje': progreso,
                'completadas': etapas_completadas,
                'total': total_etapas,
                'total_documentos': total_documentos,
                'estado': expediente.estado,
                'estado_actual': expediente.estado_actual,
                'completado': progreso == 100,
                'fecha_actualizacion': fecha_actual_str,
                'fecha_actualizacion_iso': fecha_actual.isoformat(),
                'hora_servidor': fecha_actual_str,
                'areas': {
                    'completadas': etapas_completadas,
                    'totales': total_etapas
                }
            }
            
            logger.info(f"[RESPUESTA] Progreso para expediente {expediente_id}: {response_data}")
            return JsonResponse(response_data)
            
    except DatabaseError as e:
        logger.error(f"[ERROR] Error de base de datos al obtener progreso para expediente {expediente_id}: {str(e)}")
        return JsonResponse({
            'error': 'Error al procesar la solicitud de progreso',
            'detalles': str(e)
        }, status=500)
        
    except Exception as e:
        logger.error(f"[ERROR] Error inesperado al obtener progreso para expediente {expediente_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Error inesperado al procesar la solicitud',
            'detalles': str(e)
        }, status=500)
@login_required
@require_http_methods(["POST"])
def editar_numero_sima(request, expediente_id):
    """
    Vista para editar el número SIMA de un expediente mediante AJAX
    """
    logger = logging.getLogger('digitalizacion')
    logger.info(f"=== INICIO editar_numero_sima ===")
    logger.info(f"Expediente ID: {expediente_id}")
    logger.info(f"Usuario: {request.user.get_full_name()} (ID: {request.user.id})")
    logger.info(f"Datos POST: {request.POST}")
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.change_expediente', expediente):
            logger.warning(f"Usuario {request.user} no tiene permiso para editar el expediente {expediente_id}")
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para editar este expediente.'
            }, status=403)
        
        # Obtener el número SIMA del formulario
        numero_sima = request.POST.get('numero_sima', '').strip()
        
        # Validar que el número no esté vacío si se está asignando
        if numero_sima == '':
            numero_sima = None  # Permitir eliminar el número SIMA
        
        # Obtener el valor anterior para el historial
        valor_anterior = expediente.numero_sima
        
        # Actualizar el número SIMA
        expediente.numero_sima = numero_sima
        expediente.save(update_fields=['numero_sima', 'fecha_actualizacion'])
        
        # Registrar en el historial
        if valor_anterior and not numero_sima:
            # Se eliminó el número SIMA
            accion = "Eliminación de número SIMA"
            descripcion = f"Se eliminó el número SIMA: {valor_anterior}"
        elif not valor_anterior and numero_sima:
            # Se agregó un número SIMA
            accion = "Asignación de número SIMA"
            descripcion = f"Se asignó el número SIMA: {numero_sima}"
        else:
            # Se modificó el número SIMA
            accion = "Actualización de número SIMA"
            descripcion = f"Se actualizó el número SIMA de '{valor_anterior}' a '{numero_sima}'"
        
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion=accion,
            descripcion=descripcion
        )
        
        logger.info(f"Número SIMA actualizado correctamente a: {numero_sima}")
        
        return JsonResponse({
            'success': True,
            'numero_sima': expediente.numero_sima,
            'mensaje': 'Número SIMA actualizado correctamente.'
        })
        
    except Exception as e:
        logger.error(f"Error al actualizar el número SIMA: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar el número SIMA: {str(e)}'
        }, status=500)


def formatear_tamano(tamano_bytes):
    """
    Formatea el tamaño del archivo en bytes a un formato legible (KB, MB, GB, etc.)
    
    Args:
        tamano_bytes (int): Tamaño del archivo en bytes
        
    Returns:
        str: Tamaño formateado (ej: '1.5 MB', '2.3 KB', '4.7 GB')
    """
    if not tamano_bytes or tamano_bytes == 0:
        return '0 Bytes'
    
    # Definir las unidades de medida
    unidades = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Calcular la unidad adecuada
    indice = 0
    tamano = float(tamano_bytes)
    
    while tamano >= 1024 and indice < len(unidades) - 1:
        tamano /= 1024.0
        indice += 1
    
    # Formatear el resultado con 2 decimales y la unidad correspondiente
    return f"{tamano:.2f} {unidades[indice]}"