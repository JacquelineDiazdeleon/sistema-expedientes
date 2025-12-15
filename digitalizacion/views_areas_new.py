from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.db.models import Max, Q
import json
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# ... (resto de las importaciones existentes)

@login_required
def crear_area_tipo(request, tipo):
    """Vista para crear una nueva área para un tipo y subtipo de expediente"""
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para crear áreas.')
        return redirect('gestionar_areas_tipos', tipo=tipo)
    
    # Obtener subtipo desde parámetros
    subtipo = request.GET.get('subtipo')
    
    # Si es un tipo que no requiere subtipo, establecerlo como None
    if tipo != 'licitacion':
        subtipo = None
    
    # Obtener el nombre del tipo para mostrar
    try:
        tipo_display = dict(Expediente.TIPO_CHOICES).get(tipo, tipo.replace('_', ' ').title())
    except (AttributeError, KeyError):
        tipo_display = tipo.replace('_', ' ').title()
    
    # Inicializar variables para el formulario
    form_data = request.POST if request.method == 'POST' else {}
    form_errors = {}
    
    # Obtener subtipos disponibles
    subtipos_disponibles = []
    if tipo == 'licitacion':
        subtipos_disponibles = [
            ('licitacion_recurso_propio', 'Recurso Propio'),
            ('licitacion_fondo_federal', 'Fondo Federal')
        ]
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener el subtipo del formulario si no está en la URL
                if not subtipo and tipo == 'licitacion':
                    subtipo = request.POST.get('subtipo')
                
                # Validar campos requeridos
                nombre = request.POST.get('nombre', '').strip()
                titulo = request.POST.get('titulo', '').strip()
                
                if not nombre:
                    form_errors['nombre'] = 'Este campo es obligatorio'
                
                if not titulo:
                    form_errors['titulo'] = 'Este campo es obligatorio'
                
                # Validar tamaño máximo de archivo
                try:
                    tamano_max = int(request.POST.get('tamaño_max_archivo', 10))
                    if tamano_max <= 0:
                        form_errors['tamaño_max_archivo'] = 'Debe ser mayor a 0'
                except (ValueError, TypeError):
                    form_errors['tamaño_max_archivo'] = 'Debe ser un número válido'
                
                # Si no hay errores, continuar con la creación
                if not form_errors:
                    # Verificar si ya existe un área con el mismo nombre para este tipo y subtipo
                    filtro_existencia = {
                        'tipo_expediente': tipo,
                        'nombre': nombre.lower().replace(' ', '_')
                    }
                    
                    if subtipo:
                        filtro_existencia['subtipo_expediente'] = subtipo
                    else:
                        filtro_existencia['subtipo_expediente__isnull'] = True
                    
                    if AreaTipoExpediente.objects.filter(**filtro_existencia).exists():
                        messages.error(request, f'Ya existe un área con el nombre "{nombre}" para este tipo de expediente.')
                    else:
                        # Obtener siguiente orden
                        filtro_orden = {'tipo_expediente': tipo}
                        if subtipo:
                            filtro_orden['subtipo_expediente'] = subtipo
                        else:
                            filtro_orden['subtipo_expediente__isnull'] = True
                        
                        ultimo_orden = AreaTipoExpediente.objects.filter(**filtro_orden).aggregate(
                            max_orden=Max('orden')
                        )['max_orden'] or 0
                        
                        # Procesar tipos de archivo permitidos
                        tipos_archivo = [ext.strip().lower() for ext in request.POST.get('tipos_archivo_permitidos', 'pdf,docx,xlsx').split(',')]
                        
                        # Crear el área
                        area = AreaTipoExpediente.objects.create(
                            nombre=nombre.lower().replace(' ', '_'),
                            titulo=titulo,
                            descripcion=request.POST.get('descripcion', '').strip(),
                            tipo_expediente=tipo,
                            subtipo_expediente=subtipo,
                            tipo_area=request.POST.get('tipo_area', 'mixto'),
                            orden=ultimo_orden + 1,
                            obligatoria=request.POST.get('obligatoria') == 'on',
                            tipos_archivo_permitidos=','.join(tipos_archivo),
                            tamaño_max_archivo=tamano_max,
                            creada_por=request.user
                        )
                        
                        messages.success(request, f'Área "{area.titulo}" creada exitosamente.')
                        
                        # Redirigir a la lista de áreas del mismo tipo/subtipo
                        if subtipo:
                            return redirect(f'/areas/?tipo={tipo}&subtipo={subtipo}')
                        return redirect(f'/areas/?tipo={tipo}')
        
        except Exception as e:
            logger.error(f"Error al crear área: {str(e)}", exc_info=True)
            messages.error(request, f'Error inesperado al crear el área: {str(e)}')
    
    # Si hay mensajes de error o es GET, mostrar el formulario
    # Si no se proporcionó subtipo y hay subtipos disponibles, usar el primero
    if not subtipo and subtipos_disponibles:
        subtipo = subtipos_disponibles[0][0]
    
    subtipo_display = dict(subtipos_disponibles).get(subtipo, subtipo.replace('_', ' ').title() if subtipo else "")
    
    context = {
        'tipo': tipo,
        'subtipo': subtipo,
        'tipo_info': tipo_display,
        'subtipo_info': subtipo_display,
        'tipo_area_choices': AreaTipoExpediente.TIPO_AREA_CHOICES,
        'subtipos_disponibles': subtipos_disponibles,
        'form_data': form_data,
        'form_errors': form_errors,
    }
    
    return render(request, 'digitalizacion/admin/areas/crear_area.html', context)
