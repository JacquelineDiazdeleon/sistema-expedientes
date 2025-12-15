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
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def get_demo_user():
    """Obtener o crear un usuario demo para operaciones sin autenticación"""
    User = get_user_model()
    return User.objects.get_or_create(
        username='usuario_demo',
        defaults={'is_active': False, 'is_staff': False, 'is_superuser': False}
    )[0]

@login_required
def subir_documento(request, expediente_id, etapa):
    """Vista para subir documentos a una etapa específica"""
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    
    if request.method == 'POST':
        try:
            # Obtener el archivo del formulario
            archivo = request.FILES.get('documento')
            nombre_documento = request.POST.get('nombreDocumento')
            area_id = request.POST.get('area_id')
            
            if not archivo or not nombre_documento or not area_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan campos requeridos: documento, nombreDocumento y area_id son obligatorios'
                }, status=400)
            
            # Validar tamaño del archivo (10MB)
            if archivo.size > 10 * 1024 * 1024:  # 10MB
                return JsonResponse({
                    'success': False,
                    'error': 'El archivo es demasiado grande. El tamaño máximo permitido es 10MB.'
                }, status=400)
            
            # Obtener usuario (autenticado o demo)
            usuario = request.user if request.user.is_authenticated else get_demo_user()
            
            # Crear el documento
            documento = DocumentoExpediente.objects.create(
                expediente=expediente,
                etapa=etapa,
                area_id=area_id,
                nombre_documento=nombre_documento,
                archivo=archivo,
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
                    'id': documento.id,
                    'nombre': nombre_documento,
                    'fecha': ahora.strftime('%d/%m/%Y %H:%M'),
                    'usuario': usuario.get_full_name() or usuario.username,
                    'url': documento.archivo.url if documento.archivo else ''
                }
            })
            
        except Exception as e:
            logger.error(f'Error en subir_documento: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar el documento: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def subir_documento_temporal(request, expediente_id):
    """
    Vista temporal para manejar la subida de documentos sin la etapa en la URL.
    Obtiene la etapa directamente del formulario.
    """
    try:
        if request.method == 'POST':
            # Obtener la etapa directamente del formulario
            etapa = request.POST.get('etapa')
            if not etapa:
                return JsonResponse({
                    'success': False, 
                    'error': 'No se especificó la etapa del documento'
                }, status=400)
                
            # Llamar a la vista principal de subida de documentos con la etapa
            return subir_documento(request, expediente_id, etapa)
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    except Exception as e:
        logger.error(f'Error en subir_documento_temporal: {str(e)}')
        return JsonResponse({
            'success': False, 
            'error': 'Error al procesar la solicitud'
        }, status=500)
