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

# ... (resto de las importaciones y funciones existentes)

@login_required
def obtener_documentos_por_area(request, expediente_id, area_id):
    """
    Vista para obtener los documentos de un área específica de un expediente.
    Puede recibir un ID numérico o un slug como identificador del área.
    """
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, pk=expediente_id)
        
        # Obtener el área - primero intentamos por ID numérico
        try:
            # Si area_id es un número, lo usamos directamente
            area_id_num = int(area_id)
            area = get_object_or_404(AreaTipoExpediente, id=area_id_num)
        except (ValueError, TypeError):
            # Si no es un número, asumimos que es un slug
            area = get_object_or_404(AreaTipoExpediente, slug=area_id)
        
        # Obtener los documentos del área
        documentos = DocumentoExpediente.objects.filter(
            expediente=expediente,
            area=area
        ).select_related('subido_por', 'area').order_by('-fecha_subida')
        
        # Formatear los documentos
        documentos_data = []
        for doc in documentos:
            documentos_data.append({
                'id': doc.id,
                'nombre_documento': doc.nombre_documento,
                'archivo': os.path.basename(doc.archivo.name) if doc.archivo else None,
                'archivo_url': doc.archivo.url if doc.archivo else None,
                'fecha_subida': doc.fecha_subida.isoformat(),
                'subido_por': doc.subido_por.get_full_name() if doc.subido_por else 'Usuario desconocido',
                'tamanio': doc.archivo.size if doc.archivo else 0,
                'tipo': os.path.splitext(doc.archivo.name)[1].lstrip('.').lower() if doc.archivo else '',
                'area_nombre': area.titulo if area else ''
            })
        
        return JsonResponse(documentos_data, safe=False)
        
    except Exception as e:
        print(f"Error en obtener_documentos_por_area: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': 'Error al obtener los documentos del área',
            'detalle': str(e),
            'trace': traceback.format_exc()
        }, status=500)

# ... (resto del código existente)
