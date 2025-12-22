from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.db.models import Max, Q
import json

# Deshabilitar mensajes
def _no_op(*args, **kwargs):
    pass

# Reemplazar las funciones de mensajes con no-ops
messages = type('NoOpMessages', (), {
    'debug': _no_op,
    'info': _no_op,
    'success': _no_op,
    'warning': _no_op,
    'error': _no_op,
    'add_message': _no_op,
    'get_messages': lambda *a, **kw: [],
    'get_level': lambda *a, **kw: 0,
    'set_level': _no_op,
    'constants': type('Constants', (), {
        'DEBUG': 10,
        'INFO': 20,
        'SUCCESS': 25,
        'WARNING': 30,
        'ERROR': 40,
    })(),
})()

from .models import (
    AreaTipoExpediente, CampoAreaPersonalizado, Expediente,
    ValorAreaExpediente, ValorCampoPersonalizadoArea
)


# ============================================
# VISTAS PARA GESTIÓN DE ÁREAS
# ============================================

@login_required
def gestionar_areas_tipos(request, tipo=None):
    """Vista principal para gestionar áreas por tipo y subtipo de expediente"""
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para administrar áreas del sistema.')
        return redirect('expedientes:dashboard')
    
    # ============================================
    # LÓGICA AVANZADA: VALIDACIÓN Y OBTENCIÓN DEL TIPO
    # ============================================
    from django.db.models import Q
    
    # Obtener tipos válidos del modelo
    tipos_validos = dict(Expediente.TIPO_CHOICES)
    tipos_validos_keys = [key for key, _ in Expediente.TIPO_CHOICES]
    
    # Obtener tipo desde parámetro de URL o GET
    # Priorizar el parámetro de la función sobre GET
    tipo_raw = None
    if tipo:
        tipo_raw = str(tipo).strip()
    elif request.GET.get('tipo'):
        tipo_raw = request.GET.get('tipo').strip()
    
    # DEBUG: Imprimir valores para depuración (remover en producción)
    # print(f"DEBUG: tipo (parámetro función) = {tipo}")
    # print(f"DEBUG: request.GET.get('tipo') = {request.GET.get('tipo')}")
    # print(f"DEBUG: tipo_raw = {tipo_raw}")
    # print(f"DEBUG: tipos_validos_keys = {tipos_validos_keys}")
    
    # Normalizar y validar el tipo
    tipo_selected = None
    if tipo_raw:
        tipo_normalizado = str(tipo_raw).strip().lower()
        
        # Validar que el tipo existe EXACTAMENTE en las opciones válidas
        # Comparación exacta sin búsqueda parcial para evitar errores
        if tipo_normalizado in tipos_validos_keys:
            tipo_selected = tipo_normalizado
        # Si no coincide exactamente, dejar como None (no hacer búsqueda parcial)
    
    # Asegurar que tipo_selected sea string o None (no vacío)
    if tipo_selected:
        tipo_selected = str(tipo_selected).strip()
        # Si después de strip queda vacío, establecer a None
        if not tipo_selected:
            tipo_selected = None
    
    # DEBUG: Verificar resultado final
    # print(f"DEBUG: tipo_selected final = {tipo_selected}")
    
    # ============================================
    # LÓGICA AVANZADA: MANEJO DE SUBTIPOS (SOLO LICITACIÓN)
    # ============================================
    
    subtipos_disponibles = []
    subtipo_selected = None
    subtipos_con_contadores = []
    
    if tipo_selected == 'licitacion':
        # Definir subtipos disponibles para licitación
        # IMPORTANTE: Usar formato sin prefijo para coincidir con Expediente.SUBTIPO_LICITACION_CHOICES
        subtipos_disponibles = [
            ('recurso_propio', 'Recurso Propio'),
            ('fondo_federal', 'Fondo Federal'),
            ('otros', 'Otros')
        ]
        
        # Obtener subtipo seleccionado desde GET
        subtipo_raw = request.GET.get('subtipo', '').strip()
        if subtipo_raw:
            # Normalizar: si viene con prefijo 'licitacion_', quitarlo
            if subtipo_raw.startswith('licitacion_'):
                subtipo_normalizado = subtipo_raw.replace('licitacion_', '')
            else:
                subtipo_normalizado = subtipo_raw
            
            # Validar que el subtipo es válido
            subtipos_keys = [key for key, _ in subtipos_disponibles]
            if subtipo_normalizado in subtipos_keys:
                subtipo_selected = subtipo_normalizado
            else:
                # Si no es válido, usar el primero por defecto
                subtipo_selected = subtipos_disponibles[0][0]
        else:
            # Si no hay subtipo, usar el primero por defecto
            subtipo_selected = subtipos_disponibles[0][0]
        
        # Calcular contadores para cada subtipo
        # Buscar áreas con ambos formatos (sin prefijo y con prefijo) para compatibilidad
        for subtipo_key, subtipo_display in subtipos_disponibles:
            count = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_key) | Q(subtipo_expediente=f'licitacion_{subtipo_key}')
            ).count()
            subtipos_con_contadores.append((subtipo_key, subtipo_display, count))
    
    # ============================================
    # LÓGICA AVANZADA: OBTENER ÁREAS SEGÚN TIPO Y SUBTIPO
    # ============================================
    
    areas = []
    
    if tipo_selected:
        if tipo_selected == 'licitacion' and subtipo_selected:
            # Para licitación con subtipo específico:
            # SOLO mostrar áreas específicas del subtipo (NO incluir genéricas)
            # Buscar ambos formatos: con y sin prefijo
            # IMPORTANTE: Obtener todas las áreas del subtipo (sin importar el formato del subtipo)
            areas_query = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_selected) | Q(subtipo_expediente=f'licitacion_{subtipo_selected}')
            )
            
            # Convertir a lista y ordenar por orden actual
            areas = list(areas_query)
            areas.sort(key=lambda x: (x.orden or 0, x.titulo or ''))
        else:
            # Para otros tipos (no licitación) o licitación sin subtipo:
            # Buscar solo áreas genéricas (sin subtipo específico)
            areas_query = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
            )
            
            # Convertir a lista y ordenar
            areas = list(areas_query)
            areas.sort(key=lambda x: (x.orden or 0, x.titulo or ''))
        
        # CRÍTICO: Normalizar el orden SOLO para las áreas ACTIVAS que se están mostrando
        # Esto asegura que el orden sea consecutivo (1, 2, 3, 4, 5...) sin saltos
        # Las áreas inactivas mantienen su orden pero no se muestran
        from django.db import transaction
        
        # Usar bulk_update para mejor rendimiento y consistencia
        areas_to_update = []
        with transaction.atomic():
            for index, area in enumerate(areas, start=1):
                if area.orden != index:
                    area.orden = index
                    areas_to_update.append(area)
            
            # Actualizar todas las áreas de una vez
            if areas_to_update:
                AreaTipoExpediente.objects.bulk_update(areas_to_update, ['orden'])
                # Recargar las áreas desde la base de datos para reflejar los cambios
                for area in areas_to_update:
                    area.refresh_from_db()
                # Reordenar la lista después de actualizar
                areas.sort(key=lambda x: (x.orden or 0, x.titulo or ''))
    
    # Información de tipos para el template
    tipos_info = {
        'licitacion': 'Licitación',
        'concurso_invitacion': 'Concurso por Invitación',
        'compra_directa': 'Compra Directa',
        'adjudicacion_directa': 'Adjudicación Directa',
    }
    
    # Calcular estadísticas para el contexto
    # IMPORTANTE: Mostrar solo las áreas que realmente se están mostrando en la lista
    total_areas_mostradas = len(areas)  # Solo las áreas que se están mostrando (filtradas por tipo/subtipo)
    
    context = {
        'areas': areas,
        'tipo_selected': tipo_selected,  # Ya normalizado arriba
        'subtipo_selected': subtipo_selected,
        'tipos_choices': Expediente.TIPO_CHOICES,
        'tipos_info': tipos_info,
        'subtipos_disponibles': subtipos_disponibles,
        'subtipos_con_contadores': subtipos_con_contadores,
        'tipos_validos': tipos_validos_keys,  # Para validación en template si es necesario
        'total_areas_activas': total_areas_mostradas,  # Áreas que se están mostrando (exactas)
    }
    
    return render(request, 'digitalizacion/admin/areas/gestionar_areas.html', context)


@login_required
def crear_area_tipo(request, tipo):
    """Vista para crear una nueva área para un tipo y subtipo de expediente con validación avanzada"""
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para crear áreas.')
        from django.urls import reverse
        return redirect(reverse('areas:gestionar') + f'?tipo={tipo}')
    
    # ============================================
    # VALIDACIÓN AVANZADA DEL TIPO
    # ============================================
    
    # Obtener tipos válidos
    tipos_validos = dict(Expediente.TIPO_CHOICES)
    tipos_validos_keys = [key for key, _ in Expediente.TIPO_CHOICES]
    
    # Normalizar y validar el tipo
    tipo_normalizado = str(tipo).strip().lower()
    if tipo_normalizado not in tipos_validos_keys:
        # Intentar encontrar coincidencia
        tipo_encontrado = None
        for key in tipos_validos_keys:
            if key.startswith(tipo_normalizado) or tipo_normalizado in key:
                tipo_encontrado = key
                break
        
        if not tipo_encontrado:
            messages.error(request, f'Tipo de expediente no válido: {tipo}')
            return redirect('areas:gestionar')
        
        tipo = tipo_encontrado
    else:
        tipo = tipo_normalizado
    
    # ============================================
    # MANEJO DE SUBTIPOS (SOLO PARA LICITACIÓN)
    # ============================================
    
    subtipo = None
    subtipos_disponibles = []
    
    if tipo == 'licitacion':
        # Definir subtipos válidos para licitación
        # IMPORTANTE: Usar el formato sin prefijo 'licitacion_' para coincidir con Expediente.SUBTIPO_LICITACION_CHOICES
        subtipos_validos = {
            'recurso_propio': 'Recurso Propio',
            'fondo_federal': 'Fondo Federal',
            'otros': 'Otros'
        }
        # También aceptar el formato con prefijo para compatibilidad
        subtipos_validos_con_prefijo = {
            'licitacion_recurso_propio': 'Recurso Propio',
            'licitacion_fondo_federal': 'Fondo Federal',
            'licitacion_otros': 'Otros'
        }
        subtipos_disponibles = [
            ('recurso_propio', 'Recurso Propio'),
            ('fondo_federal', 'Fondo Federal'),
            ('otros', 'Otros')
        ]
        
        # Obtener subtipo desde GET o POST
        subtipo_raw = request.GET.get('subtipo') or request.POST.get('subtipo', '').strip()
        
        if subtipo_raw:
            # Normalizar: si viene con prefijo 'licitacion_', quitarlo
            if subtipo_raw.startswith('licitacion_'):
                subtipo = subtipo_raw.replace('licitacion_', '')
            elif subtipo_raw in subtipos_validos:
                subtipo = subtipo_raw
            elif subtipo_raw in subtipos_validos_con_prefijo:
                subtipo = subtipo_raw.replace('licitacion_', '')
            else:
                # Si no es válido, usar el primero por defecto
                subtipo = subtipos_disponibles[0][0]
        else:
            # Si no se proporciona, usar el primero por defecto
            subtipo = subtipos_disponibles[0][0]
    else:
        # Para otros tipos, no hay subtipos
        subtipo = None
        subtipos_disponibles = []
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener el subtipo del formulario si no está en la URL
                if not subtipo and tipo == 'licitacion':
                    subtipo = request.POST.get('subtipo')
                
                # Validar que el nombre no esté vacío
                nombre = request.POST.get('nombre', '').strip()
                if not nombre:
                    messages.error(request, 'El nombre del área es obligatorio.')
                    return redirect('crear_area_tipo', tipo=tipo)
                
                # Verificar si ya existe un área con el mismo nombre para este tipo y subtipo
                # Buscar con ambos formatos posibles (sin prefijo y con prefijo) para evitar duplicados
                nombre_normalizado = nombre.lower().replace(' ', '_')
                if tipo == 'licitacion' and subtipo:
                    # Para licitación, buscar con ambos formatos de subtipo
                    existe = AreaTipoExpediente.objects.filter(
                        tipo_expediente=tipo,
                        nombre=nombre_normalizado,
                        activa=True
                    ).filter(
                        Q(subtipo_expediente=subtipo) | Q(subtipo_expediente=f'licitacion_{subtipo}')
                    ).exists()
                else:
                    # Para otros tipos, búsqueda normal
                    existe = AreaTipoExpediente.objects.filter(
                    tipo_expediente=tipo,
                    subtipo_expediente=subtipo,
                        nombre=nombre_normalizado
                    ).exists()
                
                if existe:
                    messages.error(request, 'Ya existe un área con este nombre para el tipo seleccionado.')
                    from django.urls import reverse
                    redirect_url = reverse('areas:crear', kwargs={'tipo': tipo})
                    if subtipo:
                        redirect_url += f'?subtipo={subtipo}'
                    return redirect(redirect_url)
                
                # Obtener siguiente orden - contar todas las áreas del mismo tipo y subtipo
                # para asegurar que el orden sea consecutivo
                filtro = {'tipo_expediente': tipo, 'activa': True}
                if subtipo:
                    # Buscar áreas con el subtipo específico (ambos formatos)
                    areas_existentes = AreaTipoExpediente.objects.filter(
                        tipo_expediente=tipo,
                        activa=True
                    ).filter(
                        Q(subtipo_expediente=subtipo) | Q(subtipo_expediente=f'licitacion_{subtipo}')
                    )
                else:
                    # Para áreas sin subtipo
                    areas_existentes = AreaTipoExpediente.objects.filter(
                        tipo_expediente=tipo,
                        activa=True
                    ).filter(
                        Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
                    )
                
                # Contar áreas existentes para obtener el siguiente orden consecutivo
                cantidad_areas = areas_existentes.count()
                siguiente_orden = cantidad_areas + 1
                
                # Crear el área - IMPORTANTE: activa=True para que aparezca en expedientes
                # Debug: Ver qué valores se están guardando
                print(f"[DEBUG CREAR ÁREA] Tipo: {tipo}, Subtipo: {subtipo} (tipo: {type(subtipo)})")
                print(f"[DEBUG CREAR ÁREA] Nombre: {nombre}, Título: {request.POST.get('titulo', nombre)}")
                
                area = AreaTipoExpediente.objects.create(
                    nombre=nombre.lower().replace(' ', '_'),
                    titulo=request.POST.get('titulo', nombre),
                    descripcion=request.POST.get('descripcion', ''),
                    tipo_expediente=tipo,
                    subtipo_expediente=subtipo,  # Se guarda con el formato normalizado (sin prefijo)
                    tipo_area=request.POST.get('tipo_area', 'mixto'),
                    orden=siguiente_orden,
                    obligatoria=request.POST.get('obligatoria') == 'on',
                    tipos_archivo_permitidos=request.POST.get('tipos_archivo_permitidos', 'pdf,docx,xlsx'),
                    tamano_max_archivo=int(request.POST.get('tamaño_max_archivo', 10)),
                    activa=True,  # CRÍTICO: Debe estar activa para aparecer en expedientes
                    es_default=False,  # Las creadas manualmente no son por defecto
                    creada_por=request.user
                )
                
                # Debug: Verificar que se guardó correctamente
                area_refreshed = AreaTipoExpediente.objects.get(id=area.id)
                print(f"[DEBUG CREAR ÁREA] Área creada - ID: {area_refreshed.id}, Subtipo guardado: '{area_refreshed.subtipo_expediente}' (tipo: {type(area_refreshed.subtipo_expediente)})")
                
                messages.success(request, f'Área "{area.titulo}" creada exitosamente.')
                
                # Redirigir a la lista de áreas del mismo tipo/subtipo
                from django.urls import reverse
                redirect_url = reverse('areas:gestionar')
                if subtipo:
                    redirect_url += f'?tipo={tipo}&subtipo={subtipo}'
                else:
                    redirect_url += f'?tipo={tipo}'
                return redirect(redirect_url)
                
        except Exception as e:
            messages.error(request, f'Error al crear el área: {str(e)}')
    
    # GET request - mostrar formulario
    try:
        tipo_display = dict(Expediente.TIPO_CHOICES)[tipo]
    except KeyError:
        tipo_display = tipo.replace('_', ' ').title()
        
    subtipos_disponibles = []
    if tipo == 'licitacion':
        subtipos_disponibles = [
            ('licitacion_recurso_propio', 'Recurso Propio'),
            ('licitacion_fondo_federal', 'Fondo Federal')
        ]
    
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
    }
    
    return render(request, 'digitalizacion/admin/areas/crear_area.html', context)


@login_required
def editar_area(request, area_id):
    """Vista para editar un área existente"""
    area = get_object_or_404(AreaTipoExpediente, pk=area_id)
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        if area.creada_por != request.user:
            messages.error(request, 'No tienes permisos para editar esta área.')
            return redirect('areas:gestionar_tipo', tipo=area.tipo_expediente)
    
    if request.method == 'POST':
        try:
            # Actualizar campos
            area.titulo = request.POST.get('titulo')
            area.descripcion = request.POST.get('descripcion', '')
            area.tipo_area = request.POST.get('tipo_area', 'mixto')
            area.obligatoria = request.POST.get('obligatoria') == 'on'
            area.tipos_archivo_permitidos = request.POST.get('tipos_archivo_permitidos', 'pdf,docx,xlsx')
            area.tamaño_max_archivo = int(request.POST.get('tamaño_max_archivo', 10))
            
            # Solo permitir cambiar nombre si no es área por defecto
            if not area.es_default:
                nuevo_nombre = request.POST.get('nombre')
                if nuevo_nombre:  # Verificar que el campo no sea None
                    nuevo_nombre = nuevo_nombre.lower().replace(' ', '_')
                    if nuevo_nombre != area.nombre:
                        # Verificar que no exista otro con ese nombre
                        if AreaTipoExpediente.objects.filter(
                            tipo_expediente=area.tipo_expediente,
                            nombre=nuevo_nombre
                        ).exclude(pk=area.pk).exists():
                            messages.error(request, 'Ya existe un área con ese nombre.')
                            return render(request, 'digitalizacion/admin/areas/editar_area.html', {'area': area})
                        area.nombre = nuevo_nombre
            
            area.save()
            
            messages.success(request, f'Área "{area.titulo}" actualizada exitosamente.')
            return redirect('areas:gestionar_tipo', tipo=area.tipo_expediente)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el área: {str(e)}')
    
    context = {
        'area': area,
        'tipo_area_choices': AreaTipoExpediente.TIPO_AREA_CHOICES,
    }
    
    return render(request, 'digitalizacion/admin/areas/editar_area.html', context)


@login_required
@require_http_methods(["POST"])
def eliminar_area(request, area_id):
    """Vista para eliminar un área"""
    area = get_object_or_404(AreaTipoExpediente, pk=area_id)
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        if area.creada_por != request.user:
            messages.error(request, 'No tienes permisos para eliminar esta área.')
            return redirect('areas:gestionar_tipo', tipo=area.tipo_expediente)
    
    # Obtener información sobre expedientes asociados
    valores_asociados = ValorAreaExpediente.objects.filter(area=area)
    expedientes_con_valores = valores_asociados.count()
    
    try:
        titulo = area.titulo
        tipo = area.tipo_expediente
        es_default = area.es_default
        
        # Eliminar primero todos los valores asociados de expedientes
        if expedientes_con_valores > 0:
            valores_asociados.delete()
        
        # Eliminar el área
        area.delete()
        
        # Mensaje de éxito diferente según el tipo
        if es_default:
            messages.success(request, f'Área DEFAULT "{titulo}" eliminada exitosamente. Se eliminó de {expedientes_con_valores} expedientes.')
        else:
            if expedientes_con_valores > 0:
                messages.success(request, f'Área "{titulo}" eliminada exitosamente. Se eliminó de {expedientes_con_valores} expedientes.')
            else:
                messages.success(request, f'Área "{titulo}" eliminada exitosamente.')
                
    except Exception as e:
        messages.error(request, f'Error al eliminar el área: {str(e)}')
    
    return redirect('areas:gestionar_tipo', tipo=tipo)


@login_required
@require_http_methods(["POST"])
def reordenar_areas(request, tipo):
    """Vista AJAX para reordenar áreas"""
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        data = json.loads(request.body)
        area_ids = data.get('area_ids', [])
        
        with transaction.atomic():
            for index, area_id in enumerate(area_ids):
                AreaTipoExpediente.objects.filter(
                    pk=area_id,
                    tipo_expediente=tipo
                ).update(orden=index + 1)
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def duplicar_area(request, area_id):
    """Vista para duplicar un área a otro tipo de expediente"""
    area_origen = get_object_or_404(AreaTipoExpediente, pk=area_id)
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para duplicar áreas.')
        return redirect('areas:gestionar_tipo', tipo=area_origen.tipo_expediente)
    
    tipo_destino = request.POST.get('tipo_destino')
    if not tipo_destino or tipo_destino == area_origen.tipo_expediente:
        messages.error(request, 'Debes seleccionar un tipo de expediente diferente.')
        return redirect('areas:gestionar_tipo', tipo=area_origen.tipo_expediente)
    
    try:
        with transaction.atomic():
            # Verificar si ya existe
            if AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_destino,
                nombre=area_origen.nombre
            ).exists():
                messages.error(request, f'Ya existe un área con el nombre "{area_origen.nombre}" en el tipo destino.')
                return redirect('areas:gestionar_tipo', tipo=area_origen.tipo_expediente)
            
            # Obtener siguiente orden en tipo destino
            ultimo_orden = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_destino
            ).aggregate(max_orden=Max('orden'))['max_orden'] or 0
            
            # Duplicar el área
            area_nueva = AreaTipoExpediente.objects.create(
                nombre=area_origen.nombre,
                titulo=area_origen.titulo,
                descripcion=area_origen.descripcion,
                tipo_expediente=tipo_destino,
                tipo_area=area_origen.tipo_area,
                orden=ultimo_orden + 1,
                obligatoria=area_origen.obligatoria,
                tipos_archivo_permitidos=area_origen.tipos_archivo_permitidos,
                tamaño_max_archivo=area_origen.tamaño_max_archivo,
                activa=True,
                es_default=False,  # Las duplicadas nunca son por defecto
                creada_por=request.user
            )
            
            # Duplicar campos personalizados
            for campo in area_origen.campos.filter(activo=True):
                CampoAreaPersonalizado.objects.create(
                    area=area_nueva,
                    nombre=campo.nombre,
                    etiqueta=campo.etiqueta,
                    tipo_campo=campo.tipo_campo,
                    requerido=campo.requerido,
                    orden=campo.orden,
                    placeholder=campo.placeholder,
                    descripcion=campo.descripcion,
                    opciones=campo.opciones,
                    valor_minimo=campo.valor_minimo,
                    valor_maximo=campo.valor_maximo,
                    longitud_minima=campo.longitud_minima,
                    longitud_maxima=campo.longitud_maxima,
                    patron_validacion=campo.patron_validacion,
                    activo=True
                )
            
            tipo_destino_nombre = dict(Expediente.TIPO_CHOICES)[tipo_destino]
            messages.success(request, f'Área duplicada exitosamente a "{tipo_destino_nombre}".')
            
    except Exception as e:
        messages.error(request, f'Error al duplicar el área: {str(e)}')
    
    return redirect('areas:gestionar_tipo', tipo=area_origen.tipo_expediente)


# ============================================
# VISTAS PARA GESTIÓN DE CAMPOS PERSONALIZADOS
# ============================================

@login_required
def gestionar_campos_area(request, area_id):
    """Vista para gestionar campos personalizados de un área"""
    area = get_object_or_404(AreaTipoExpediente, pk=area_id)
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        if area.creada_por != request.user:
            messages.error(request, 'No tienes permisos para gestionar esta área.')
            return redirect('areas:gestionar_tipo', tipo=area.tipo_expediente)
    
    # Obtener campos
    campos = area.campos.filter(activo=True).order_by('orden', 'etiqueta')
    
    context = {
        'area': area,
        'campos': campos,
    }
    
    return render(request, 'digitalizacion/admin/areas/gestionar_campos.html', context)


@login_required
def crear_campo_area(request, area_id):
    """Vista para crear un campo personalizado en un área"""
    area = get_object_or_404(AreaTipoExpediente, pk=area_id)
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        if area.creada_por != request.user:
            messages.error(request, 'No tienes permisos para crear campos en esta área.')
            return redirect('areas:campos', area_id=area.pk)
    
    if request.method == 'POST':
        try:
            # Obtener siguiente orden
            ultimo_orden = area.campos.aggregate(max_orden=Max('orden'))['max_orden'] or 0
            
            # Procesar opciones para select/radio/checkbox
            opciones = None
            if request.POST.get('tipo_campo') in ['select', 'radio', 'checkbox']:
                opciones_texto = request.POST.get('opciones_texto', '')
                if opciones_texto:
                    opciones = [opcion.strip() for opcion in opciones_texto.split('\n') if opcion.strip()]
            
            # Crear el campo
            campo = CampoAreaPersonalizado.objects.create(
                area=area,
                nombre=request.POST.get('nombre').lower().replace(' ', '_'),
                etiqueta=request.POST.get('etiqueta'),
                tipo_campo=request.POST.get('tipo_campo'),
                requerido=request.POST.get('requerido') == 'on',
                orden=ultimo_orden + 1,
                placeholder=request.POST.get('placeholder', ''),
                descripcion=request.POST.get('descripcion', ''),
                opciones=opciones,
                valor_minimo=float(request.POST.get('valor_minimo')) if request.POST.get('valor_minimo') else None,
                valor_maximo=float(request.POST.get('valor_maximo')) if request.POST.get('valor_maximo') else None,
                longitud_minima=int(request.POST.get('longitud_minima')) if request.POST.get('longitud_minima') else None,
                longitud_maxima=int(request.POST.get('longitud_maxima')) if request.POST.get('longitud_maxima') else None,
                patron_validacion=request.POST.get('patron_validacion', '') or None,
            )
            
            messages.success(request, f'Campo "{campo.etiqueta}" creado exitosamente.')
            return redirect('areas:campos', area_id=area.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear el campo: {str(e)}')
    
    context = {
        'area': area,
        'tipo_campo_choices': CampoAreaPersonalizado.TIPO_CAMPO_CHOICES,
    }
    
    return render(request, 'digitalizacion/admin/areas/crear_campo.html', context)


@login_required
@require_http_methods(["POST"])
def eliminar_campo_area(request, campo_id):
    """Vista para eliminar un campo personalizado"""
    campo = get_object_or_404(CampoAreaPersonalizado, pk=campo_id)
    area = campo.area
    
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para eliminar campos personalizados.')
        return redirect('areas:gestionar_campos', area_id=area.id)
    
    try:
        nombre_campo = campo.etiqueta
        campo.delete()
        messages.success(request, f'Campo "{nombre_campo}" eliminado correctamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el campo: {str(e)}')
    
    return redirect('areas:gestionar_campos', area_id=area.id)


from django.http import JsonResponse

def listar_areas(request):
    """
    API endpoint para listar todas las áreas disponibles.
    Retorna un JSON con la lista de áreas y sus detalles.
    """
    try:
        # Obtener todas las áreas activas
        areas = AreaTipoExpediente.objects.filter(
            activa=True
        ).select_related('tipo_expediente', 'subtipo_expediente')
        
        # Preparar la respuesta
        areas_data = []
        for area in areas:
            area_data = {
                'id': area.id,
                'nombre': area.nombre,
                'descripcion': area.descripcion,
                'tipo_expediente': area.tipo_expediente.nombre if area.tipo_expediente else None,
                'subtipo_expediente': area.subtipo_expediente.nombre if area.subtipo_expediente else None,
                'orden': area.orden,
                'es_requerida': area.es_requerida,
                'es_multiple': area.es_multiple,
                'tipo': area.tipo,
                'opciones': area.opciones if area.opciones else []
            }
            areas_data.append(area_data)
        
        return JsonResponse({
            'status': 'success',
            'count': len(areas_data),
            'areas': areas_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def detalle_area(request, area_id):
    """
    API endpoint para obtener los detalles de un área específica.
    Retorna un JSON con los detalles del área y sus campos personalizados.
    """
    try:
        # Obtener el área solicitada
        area = get_object_or_404(
            AreaTipoExpediente.objects.select_related('tipo_expediente', 'subtipo_expediente'),
            id=area_id,
            activa=True
        )
        
        # Obtener campos personalizados del área
        campos = CampoAreaPersonalizado.objects.filter(
            area=area,
            activo=True
        ).order_by('orden')
        
        # Preparar datos del área
        area_data = {
            'id': area.id,
            'nombre': area.nombre,
            'descripcion': area.descripcion,
            'tipo_expediente': area.tipo_expediente.nombre if area.tipo_expediente else None,
            'subtipo_expediente': area.subtipo_expediente.nombre if area.subtipo_expediente else None,
            'orden': area.orden,
            'es_requerida': area.es_requerida,
            'es_multiple': area.es_multiple,
            'tipo': area.tipo,
            'opciones': area.opciones if area.opciones else [],
            'campos_personalizados': [
                {
                    'id': campo.id,
                    'etiqueta': campo.etiqueta,
                    'tipo': campo.tipo,
                    'requerido': campo.requerido,
                    'orden': campo.orden,
                    'opciones': campo.opciones if campo.opciones else []
                }
                for campo in campos
            ]
        }
        
        return JsonResponse({
            'status': 'success',
            'area': area_data
        })
        
    except AreaTipoExpediente.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'El área solicitada no existe o no está disponible.'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def areas_por_tipo(request, tipo):
    """Vista para obtener áreas por tipo de expediente"""
    try:
        # Mapeo de tipos de URL a tipos de expediente
        tipo_mapeo = {
            'compra_directa': 'adjudicacion_directa',
            'concurso_invitacion': 'concurso_invitacion',
            'licitacion': 'licitacion',
            'adjudicacion_directa': 'adjudicacion_directa'
        }
        
        # Obtener el tipo real del mapeo o usar el proporcionado
        tipo_expediente = tipo_mapeo.get(tipo, tipo)
        
        # Obtener el subtipo de los parámetros de consulta
        subtipo = request.GET.get('subtipo')
        
        # Filtrar áreas por tipo de expediente
        areas_query = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo_expediente,
            activa=True
        )
        
        # Si hay un subtipo, filtrar por él
        if subtipo:
            areas_query = areas_query.filter(
                Q(subtipo_expediente=subtipo) | 
                Q(subtipo_expediente__isnull=True) | 
                Q(subtipo_expediente='')
            )
        
        # Ordenar las áreas
        areas = areas_query.order_by('orden', 'titulo')
        
        # Preparar la respuesta
        areas_data = []
        for area in areas:
            areas_data.append({
                'id': area.id,
                'titulo': area.titulo,
                'descripcion': area.descripcion,
                'tipo_area': area.tipo_area,
                'es_requerida': area.obligatoria,
                'icono': area.icono or 'bi-folder',
                'subtipo': area.subtipo_expediente or ''
            })
        
        return JsonResponse({
            'success': True,
            'areas': areas_data,
            'tipo': tipo_expediente,
            'subtipo': subtipo or ''
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
