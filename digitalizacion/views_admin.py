from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count
from .models import SolicitudRegistro
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .models import (
    Departamento, ConfiguracionSistema, MensajeExpediente, Expediente,
    PerfilUsuario, RolUsuario
)
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q


@login_required
def panel_administracion(request):
    """Panel principal de administración"""
    # Verificar si el usuario es administrador
    tiene_perfil = hasattr(request.user, 'perfil')
    tiene_rol = tiene_perfil and request.user.perfil.rol is not None
    puede_administrar = tiene_rol and request.user.perfil.rol.puede_administrar_sistema
    
    if not tiene_perfil:
        messages.error(request, 'No tienes un perfil de usuario configurado.')
        return redirect('digitalizacion:dashboard')
    
    if not tiene_rol:
        messages.error(request, 'No tienes un rol asignado.')
        return redirect('digitalizacion:dashboard')
    
    if not puede_administrar:
        messages.error(request, f'Tu rol "{request.user.perfil.rol.nombre}" no tiene permisos de administración.')
        return redirect('digitalizacion:dashboard')
    
    # Estadísticas para el dashboard
    total_usuarios = User.objects.filter(is_active=True).count()
    total_departamentos = Departamento.objects.filter(activo=True).count()
    
    # Estadísticas de expedientes
    total_expedientes = Expediente.objects.count()
    expedientes_por_tipo = Expediente.objects.values('tipo_expediente').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Usuarios con más expedientes
    usuarios_top_expedientes = User.objects.filter(
        expedientes_creados__isnull=False
    ).annotate(
        total_expedientes=Count('expedientes_creados')
    ).order_by('-total_expedientes')[:5]
    
    # Expedientes por departamento
    expedientes_por_departamento = Departamento.objects.filter(
        expediente__isnull=False
    ).annotate(
        total_expedientes=Count('expediente')
    ).order_by('-total_expedientes')[:5]
    
    # Configuraciones del sistema
    configuraciones = ConfiguracionSistema.objects.filter(activo=True)[:10]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_departamentos': total_departamentos,
        'total_expedientes': total_expedientes,
        'expedientes_por_tipo': expedientes_por_tipo,
        'usuarios_top_expedientes': usuarios_top_expedientes,
        'expedientes_por_departamento': expedientes_por_departamento,
        'configuraciones': configuraciones,
    }
    
    # Asegurémonos de que la ruta de la plantilla sea correcta
    template_path = 'digitalizacion/admin/panel_administracion.html'
    print(f"Intentando cargar la plantilla desde: {template_path}")
    return render(request, template_path, context)





# ============================================
# GESTIÓN DE DEPARTAMENTOS
# ============================================

@login_required
def gestionar_departamentos(request):
    """Vista para gestionar departamentos"""
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para gestionar departamentos.')
        return redirect('digitalizacion:dashboard')
    
    departamentos = Departamento.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        departamento_id = request.POST.get('departamento_id')
        
        if accion == 'crear':
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion', '')
            if nombre:
                Departamento.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    activo=True
                )
                messages.success(request, f'Departamento "{nombre}" creado exitosamente.')
        
        elif accion == 'editar' and departamento_id:
            try:
                departamento = Departamento.objects.get(id=departamento_id)
                departamento.nombre = request.POST.get('nombre')
                departamento.descripcion = request.POST.get('descripcion', '')
                departamento.activo = request.POST.get('activo') == 'on'
                departamento.save()
                messages.success(request, f'Departamento "{departamento.nombre}" actualizado exitosamente.')
            except Departamento.DoesNotExist:
                messages.error(request, 'Departamento no encontrado.')
        
        elif accion == 'eliminar' and departamento_id:
            try:
                departamento = Departamento.objects.get(id=departamento_id)
                nombre = departamento.nombre
                departamento.delete()
                messages.success(request, f'Departamento "{nombre}" eliminado exitosamente.')
            except Departamento.DoesNotExist:
                messages.error(request, 'Departamento no encontrado.')
        
        return redirect('digitalizacion:gestionar_departamentos')
    
    context = {
        'departamentos': departamentos,
    }
    return render(request, 'digitalizacion/admin/departamentos/gestionar_departamentos.html', context)











# ============================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================

@login_required
def configuracion_sistema(request):
    """Vista para configurar el sistema"""
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para configurar el sistema.')
        return redirect('digitalizacion:dashboard')
    
    configuraciones = ConfiguracionSistema.objects.all().order_by('clave')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        config_id = request.POST.get('config_id')
        
        if accion == 'crear':
            clave = request.POST.get('clave')
            valor = request.POST.get('valor')
            descripcion = request.POST.get('descripcion', '')
            
            if clave and valor:
                ConfiguracionSistema.objects.create(
                    clave=clave,
                    valor=valor,
                    descripcion=descripcion,
                    activo=True
                )
                messages.success(request, f'Configuración "{clave}" creada exitosamente.')
        
        elif accion == 'editar' and config_id:
            try:
                config = ConfiguracionSistema.objects.get(id=config_id)
                config.clave = request.POST.get('clave')
                config.valor = request.POST.get('valor')
                config.descripcion = request.POST.get('descripcion', '')
                config.activo = request.POST.get('activo') == 'on'
                config.save()
                messages.success(request, f'Configuración "{config.clave}" actualizada exitosamente.')
            except ConfiguracionSistema.DoesNotExist:
                messages.error(request, 'Configuración no encontrada.')
        
        elif accion == 'eliminar' and config_id:
            try:
                config = ConfiguracionSistema.objects.get(id=config_id)
                clave = config.clave
                config.delete()
                messages.success(request, f'Configuración "{clave}" eliminada exitosamente.')
            except ConfiguracionSistema.DoesNotExist:
                messages.error(request, 'Configuración no encontrada.')
        
        return redirect('digitalizacion:configuracion_sistema')
    
    context = {
        'configuraciones': configuraciones,
    }
    return render(request, 'digitalizacion/admin/configuracion/configuracion_sistema.html', context)


@login_required
def gestion_usuarios(request):
    """Vista para gestionar usuarios (solo para administradores)"""
    # Verificar si el usuario es administrador
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('digitalizacion:dashboard')
    
    # Obtener parámetros de búsqueda y filtrado
    query = request.GET.get('q', '')
    rol_id = request.GET.get('rol', '')
    estado = request.GET.get('estado', 'activos')
    
    # Construir la consulta base
    usuarios = User.objects.select_related('perfil', 'perfil__rol').all()
    
    # Aplicar filtros
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    if rol_id and rol_id.isdigit():
        usuarios = usuarios.filter(perfil__rol_id=rol_id)
    
    if estado == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivos':
        usuarios = usuarios.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(usuarios.order_by('username'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener roles para el filtro
    roles = RolUsuario.objects.all()
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'roles': roles,
        'rol_seleccionado': int(rol_id) if rol_id and rol_id.isdigit() else '',
        'estado_seleccionado': estado,
    }
    
    return render(request, 'digitalizacion/admin/gestion_usuarios.html', context)


@login_required
def crear_usuario(request):
    """Vista para crear un nuevo usuario desde el panel de administración"""
    # Verificar permisos de administrador
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('digitalizacion:dashboard')
    
    # Obtener roles disponibles para el formulario
    roles = RolUsuario.objects.all()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            rol_id = request.POST.get('rol')
            is_active = request.POST.get('is_active') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'
            
            # Validaciones básicas
            if not all([username, email, password, confirm_password, rol_id]):
                messages.error(request, 'Todos los campos son obligatorios.')
                return redirect('digitalizacion:crear_usuario')
                
            if password != confirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('digitalizacion:crear_usuario')
                
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya está en uso.')
                return redirect('digitalizacion:crear_usuario')
                
            if User.objects.filter(email=email).exists():
                messages.error(request, 'El correo electrónico ya está registrado.')
                return redirect('digitalizacion:crear_usuario')
            
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
                is_staff=is_staff
            )
            
            # Obtener el rol seleccionado
            try:
                rol = RolUsuario.objects.get(id=rol_id)
            except RolUsuario.DoesNotExist:
                rol = None
            
            # Crear perfil de usuario
            PerfilUsuario.objects.create(
                usuario=user,
                rol=rol
            )
            
            messages.success(request, f'Usuario {username} creado exitosamente.')
            return redirect('digitalizacion:gestion_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
            return redirect('digitalizacion:crear_usuario')
    
    context = {
        'roles': roles,
    }
    return render(request, 'digitalizacion/admin/usuarios/crear_usuario.html', context)


@login_required
def editar_usuario(request, usuario_id):
    """Vista para editar un usuario existente desde el panel de administración"""
    # Verificar permisos de administrador
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar usuarios.')
        return redirect('digitalizacion:dashboard')
    
    # Obtener el usuario a editar
    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        messages.error(request, 'El usuario solicitado no existe.')
        return redirect('digitalizacion:gestion_usuarios')
    
    # Obtener roles disponibles
    roles = RolUsuario.objects.all()
    
    # Obtener el perfil del usuario (crear si no existe)
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            usuario.username = request.POST.get('username', usuario.username)
            usuario.email = request.POST.get('email', usuario.email)
            usuario.first_name = request.POST.get('first_name', usuario.first_name)
            usuario.last_name = request.POST.get('last_name', usuario.last_name)
            
            # Actualizar contraseña si se proporcionó una nueva
            nueva_password = request.POST.get('password')
            if nueva_password and nueva_password == request.POST.get('confirm_password'):
                usuario.set_password(nueva_password)
            
            # Actualizar estado y permisos
            usuario.is_active = request.POST.get('is_active') == 'on'
            usuario.is_staff = request.POST.get('is_staff') == 'on'
            usuario.is_superuser = request.POST.get('is_superuser') == 'on'
            
            # Guardar cambios en el usuario
            usuario.save()
            
            # Actualizar perfil
            rol_id = request.POST.get('rol')
            if rol_id:
                try:
                    perfil.rol = RolUsuario.objects.get(id=rol_id)
                except RolUsuario.DoesNotExist:
                    perfil.rol = None
            else:
                perfil.rol = None
            
            # Actualizar campos adicionales del perfil si existen
            if hasattr(perfil, 'telefono'):
                perfil.telefono = request.POST.get('telefono', '')
            if hasattr(perfil, 'departamento'):
                try:
                    perfil.departamento_id = request.POST.get('departamento')
                except (ValueError, TypeError):
                    perfil.departamento = None
            
            perfil.save()
            
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('digitalizacion:gestion_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el usuario: {str(e)}')
    
    # Obtener departamentos si el modelo tiene el campo
    departamentos = []
    if hasattr(PerfilUsuario, 'departamento'):
        departamentos = Departamento.objects.filter(activo=True)
    
    context = {
        'usuario_editar': usuario,
        'perfil': perfil,
        'roles': roles,
        'departamentos': departamentos,
    }
    
    return render(request, 'digitalizacion/admin/usuarios/editar_usuario.html', context)


@login_required
def eliminar_usuario(request, usuario_id):
    """Vista para eliminar un usuario permanentemente desde el panel de administración"""
    # Verificar permisos de administrador
    if not request.user.is_staff and not request.user.is_superuser:
        try:
            if not request.user.perfil.rol.puede_aprobar_usuarios:
                messages.error(request, 'No tienes permisos para eliminar usuarios.')
                return redirect('digitalizacion:dashboard')
        except:
            messages.error(request, 'No tienes permisos para eliminar usuarios.')
            return redirect('digitalizacion:dashboard')
    
    # Evitar que un usuario se elimine a sí mismo
    if request.user.id == usuario_id:
        messages.error(request, 'No puedes eliminar tu propio usuario mientras estás autenticado.')
        return redirect('digitalizacion:gestion_usuarios')
    
    try:
        # Obtener el usuario a eliminar
        usuario = User.objects.get(id=usuario_id)
        
        # Proteger al usuario principal
        if usuario.email == 'diazdeleondiazdeleonj3@gmail.com':
            messages.error(request, 'No se puede eliminar la cuenta del administrador principal.')
            return redirect('digitalizacion:gestion_usuarios')
        
        nombre_usuario = usuario.get_full_name() or usuario.username
        
        # Eliminar el perfil asociado si existe
        try:
            if hasattr(usuario, 'perfil'):
                usuario.perfil.delete()
        except:
            pass
        
        # Eliminar el usuario permanentemente
        usuario.delete()
        messages.success(request, f'Usuario "{nombre_usuario}" ha sido eliminado permanentemente.')
            
    except User.DoesNotExist:
        messages.error(request, 'El usuario que intentas eliminar no existe.')
    except Exception as e:
        messages.error(request, f'Error al intentar eliminar el usuario: {str(e)}')
    
    return redirect('digitalizacion:gestion_usuarios')


def redirigir_areas(request):
    """Redirecciona a la gestión de áreas"""
    return redirect('digitalizacion:gestionar_areas')


def admin_areas(request, tipo_expediente=None):
    """Vista para gestionar las áreas/etapas de los expedientes con lógica avanzada"""
    from .models import AreaTipoExpediente, Expediente
    from django.db.models import Q
    
    # Obtener las opciones de tipo de expediente del modelo Expediente
    TIPO_CHOICES = Expediente.TIPO_CHOICES
    tipos_validos = dict(TIPO_CHOICES)
    tipos_validos_keys = [key for key, _ in TIPO_CHOICES]
    
    # Crear una lista de tuplas (código, nombre) para usar en el template
    tipos_choices = [(tipo[0], tipo[1]) for tipo in TIPO_CHOICES]
    
    # ============================================
    # LÓGICA AVANZADA: OBTENER Y VALIDAR TIPO
    # ============================================
    
    # Obtener tipo desde parámetro de función o GET
    tipo_raw = None
    if tipo_expediente:
        tipo_raw = str(tipo_expediente).strip()
    elif request.GET.get('tipo'):
        tipo_raw = request.GET.get('tipo').strip()
    
    # Normalizar y validar el tipo
    tipo_selected = None
    if tipo_raw:
        tipo_normalizado = str(tipo_raw).strip().lower()
        # Validar que el tipo existe EXACTAMENTE en las opciones válidas
        if tipo_normalizado in tipos_validos_keys:
            tipo_selected = tipo_normalizado
    
    # NO usar valor por defecto - dejar como None si no se especifica
    
    # ============================================
    # MANEJO DE SUBTIPOS (SOLO PARA LICITACIÓN)
    # ============================================
    
    subtipos_disponibles = []
    subtipo_selected = None
    subtipos_con_contadores = []
    
    if tipo_selected == 'licitacion':
        # IMPORTANTE: Usar formato sin prefijo para coincidir con Expediente.SUBTIPO_LICITACION_CHOICES
        subtipos_disponibles = [
            ('recurso_propio', 'Recurso Propio'),
            ('fondo_federal', 'Fondo Federal')
        ]
        
        # Obtener subtipo desde GET
        subtipo_raw = request.GET.get('subtipo', '').strip()
        if subtipo_raw:
            # Normalizar: si viene con prefijo 'licitacion_', quitarlo
            if subtipo_raw.startswith('licitacion_'):
                subtipo_normalizado = subtipo_raw.replace('licitacion_', '')
            else:
                subtipo_normalizado = subtipo_raw
            
            subtipos_keys = [key for key, _ in subtipos_disponibles]
            if subtipo_normalizado in subtipos_keys:
                subtipo_selected = subtipo_normalizado
            else:
                subtipo_selected = subtipos_disponibles[0][0]
        else:
            subtipo_selected = subtipos_disponibles[0][0]
        
        # Calcular contadores (buscar áreas con ambos formatos posibles)
        for subtipo_key, subtipo_display in subtipos_disponibles:
            count = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_key) | Q(subtipo_expediente=f'licitacion_{subtipo_key}')
            ).count()
            subtipos_con_contadores.append((subtipo_key, subtipo_display, count))
    
    # ============================================
    # OBTENER ÁREAS SEGÚN TIPO Y SUBTIPO
    # ============================================
    
    areas = []
    if tipo_selected:
        if tipo_selected == 'licitacion' and subtipo_selected:
            # Para licitación con subtipo específico:
            # SOLO mostrar áreas específicas del subtipo (NO incluir genéricas)
            # Buscar ambos formatos: con y sin prefijo
            areas = list(AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_selected) | Q(subtipo_expediente=f'licitacion_{subtipo_selected}')
            ).order_by('orden', 'titulo'))
        else:
            # Para otros tipos (no licitación) o licitación sin subtipo:
            # Buscar solo áreas genéricas (sin subtipo específico)
            areas = list(AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_selected,
                activa=True
            ).filter(
                Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
            ).order_by('orden', 'titulo'))
        
        # Ordenar por orden (con manejo de None)
        areas.sort(key=lambda x: (x.orden or 0, x.titulo or ''))
        
        # Normalizar el orden para que sea consecutivo (1, 2, 3, 4, 5...)
        # IMPORTANTE: Normalizar solo dentro del contexto del tipo/subtipo específico
        # Esto corrige saltos en el orden causados por eliminaciones
        from django.db import transaction
        with transaction.atomic():
            for index, area in enumerate(areas, start=1):
                if area.orden != index:
                    area.orden = index
                    area.save(update_fields=['orden'])
    
    # Calcular estadísticas para el contexto
    # IMPORTANTE: Mostrar solo las áreas que realmente se están mostrando en la lista
    total_areas_mostradas = len(areas)  # Solo las áreas que se están mostrando (filtradas por tipo/subtipo)
    
    # Información de tipos para el template
    tipos_info = {
        'licitacion': 'Licitación',
        'concurso_invitacion': 'Concurso por Invitación',
        'compra_directa': 'Compra Directa',
        'adjudicacion_directa': 'Adjudicación Directa',
    }
    
    context = {
        'title': 'Gestión de Áreas de Expedientes',
        'breadcrumb': [
            {'name': 'Inicio', 'url': reverse_lazy('digitalizacion:dashboard')},
            {'name': 'Panel de Administración', 'url': reverse_lazy('digitalizacion:panel_administracion')},
            {'name': 'Gestión de Áreas', 'active': True}
        ],
        'tipo_selected': tipo_selected,  # Usar tipo_selected validado, no tipo_expediente
        'tipos_choices': tipos_choices,
        'tipos_info': tipos_info,
        'areas': areas,
        'subtipos_disponibles': subtipos_disponibles,
        'subtipos_con_contadores': subtipos_con_contadores,
        'subtipo_selected': subtipo_selected,
        'total_areas_activas': total_areas_mostradas,  # Áreas que se están mostrando (exactas)
    }
    return render(request, 'digitalizacion/admin/areas/gestionar_areas.html', context)


@login_required
def gestion_solicitudes(request):
    """Vista para gestionar las solicitudes en el panel de administración"""
    # Verificar permisos de administrador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('digitalizacion:dashboard')
    
    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', 'pendientes')
    
    from .models import SolicitudRegistro
    
    # Construir la consulta base para las solicitudes de registro
    solicitudes = SolicitudRegistro.objects.select_related('departamento', 'rol_solicitado').all()
    
    # Obtener contadores para cada estado
    total_count = solicitudes.count()
    pendientes_count = solicitudes.filter(estado='pendiente').count()
    aprobadas_count = solicitudes.filter(estado='aprobada').count()
    rechazadas_count = solicitudes.filter(estado='rechazada').count()
    
    # Aplicar filtros
    if query:
        solicitudes = solicitudes.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(email_institucional__icontains=query) |
            Q(departamento__nombre__icontains=query) |
            Q(puesto__icontains=query)
        )
    
    # Filtrar por estado
    if estado == 'pendientes':
        solicitudes = solicitudes.filter(estado='pendiente')
    elif estado == 'aprobadas':
        solicitudes = solicitudes.filter(estado='aprobada')
    elif estado == 'rechazadas':
        solicitudes = solicitudes.filter(estado='rechazada')
    
    # Ordenar por fecha de solicitud (más recientes primero)
    solicitudes = solicitudes.order_by('-fecha_solicitud')
    
    # Paginación
    paginator = Paginator(solicitudes, 10)  # 10 solicitudes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'estado_actual': estado,
        'titulo': 'Gestión de Solicitudes de Registro',
        'total_count': total_count,
        'pendientes_count': pendientes_count,
        'aprobadas_count': aprobadas_count,
        'rechazadas_count': rechazadas_count,
        'breadcrumb': [
            {'name': 'Inicio', 'url': reverse_lazy('digitalizacion:dashboard')},
            {'name': 'Panel de Administración', 'url': reverse_lazy('digitalizacion:panel_administracion')},
            {'name': 'Gestión de Solicitudes', 'active': True}
        ],
    }
    
    return render(request, 'digitalizacion/admin/solicitudes/gestion_solicitudes.html', context)


@login_required
@require_POST
def aprobar_solicitud(request, solicitud_id):
    """Vista para aprobar una solicitud de registro"""
    # Verificar permisos de administrador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('digitalizacion:dashboard')
    
    solicitud = get_object_or_404(SolicitudRegistro, id=solicitud_id)
    
    # Verificar que la solicitud esté pendiente
    if solicitud.estado != 'pendiente':
        messages.warning(request, 'Esta solicitud ya ha sido procesada anteriormente')
        return redirect('digitalizacion:gestion_solicitudes')
    
    try:
        # Aprobar la solicitud
        user, _ = solicitud.aprobar(request.user)
        messages.success(request, f'La solicitud ha sido aprobada y se ha creado el usuario {user.username}')
    except Exception as e:
        messages.error(request, f'Error al aprobar la solicitud: {str(e)}')
    
    return redirect('digitalizacion:gestion_solicitudes')


@login_required
@require_POST
def rechazar_solicitud(request, solicitud_id):
    """Vista para rechazar una solicitud de registro"""
    # Verificar permisos de administrador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or not request.user.perfil.rol.puede_administrar_sistema:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('digitalizacion:dashboard')
    
    solicitud = get_object_or_404(SolicitudRegistro, id=solicitud_id)
    
    # Verificar que la solicitud esté pendiente
    if solicitud.estado != 'pendiente':
        messages.warning(request, 'Esta solicitud ya ha sido procesada anteriormente')
        return redirect('digitalizacion:gestion_solicitudes')
    
    try:
        # Rechazar la solicitud
        motivo = request.POST.get('motivo', 'Solicitud rechazada por el administrador')
        solicitud.rechazar(request.user, motivo)
        messages.success(request, 'La solicitud ha sido rechazada correctamente')
    except Exception as e:
        messages.error(request, f'Error al rechazar la solicitud: {str(e)}')
    
    return redirect('digitalizacion:gestion_solicitudes')

