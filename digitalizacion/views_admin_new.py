from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import (
    Departamento, ConfiguracionSistema, MensajeExpediente, Expediente,
    PerfilUsuario, RolUsuario, SolicitudRegistro
)
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

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
    
    # Solicitudes pendientes
    solicitudes_pendientes = SolicitudRegistro.objects.filter(estado='pendiente').count()
    
    context = {
        'title': 'Panel de Administración',
        'total_usuarios': total_usuarios,
        'total_departamentos': total_departamentos,
        'total_expedientes': total_expedientes,
        'expedientes_por_tipo': expedientes_por_tipo,
        'usuarios_top_expedientes': usuarios_top_expedientes,
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    
    return render(request, 'digitalizacion/admin/panel_administracion.html', context)

def gestionar_departamentos(request):
    """Vista para gestionar departamentos"""
    # Código existente...
    pass

def configuracion_sistema(request):
    """Vista para configurar el sistema"""
    # Código existente...
    pass

def gestion_usuarios(request):
    """Vista para gestionar usuarios (solo para administradores)"""
    # Código existente...
    pass

def crear_usuario(request):
    """Vista para crear un nuevo usuario desde el panel de administración"""
    # Código existente...
    pass

def editar_usuario(request, usuario_id):
    """Vista para editar un usuario existente desde el panel de administración"""
    # Código existente...
    pass

def eliminar_usuario(request, usuario_id):
    """Vista para eliminar un usuario (desactivar) desde el panel de administración"""
    # Código existente...
    pass

def redirigir_areas(request):
    """Redirecciona a la gestión de áreas"""
    return redirect('digitalizacion:gestionar_areas')

def admin_areas(request):
    """Vista para gestionar las áreas/etapas de los expedientes"""
    context = {
        'title': 'Gestión de Áreas de Expedientes',
        'breadcrumb': [
            {'name': 'Inicio', 'url': reverse_lazy('digitalizacion:dashboard')},
            {'name': 'Panel de Administración', 'url': reverse_lazy('digitalizacion:panel_administracion')},
            {'name': 'Gestión de Áreas', 'active': True}
        ],
    }
    return render(request, 'digitalizacion/admin/areas/gestionar_areas.html', context)

@login_required
def gestion_solicitudes(request):
    """Vista para gestionar las solicitudes de registro de usuarios"""
    # Verificar permisos
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('digitalizacion:dashboard')
    
    # Obtener todas las solicitudes pendientes
    User = get_user_model()
    solicitudes = SolicitudRegistro.objects.filter(estado='pendiente').order_by('fecha_solicitud')
    
    # Procesar acciones sobre las solicitudes
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        accion = request.POST.get('accion')
        
        try:
            solicitud = SolicitudRegistro.objects.get(id=solicitud_id, estado='pendiente')
            
            if accion == 'aprobar':
                # Crear el usuario
                usuario = User(
                    username=solicitud.email_institucional.split('@')[0],
                    email=solicitud.email_institucional,
                    first_name=solicitud.nombres,
                    last_name=f"{solicitud.apellido_paterno} {solicitud.apellido_materno or ''}".strip(),
                    is_active=True,
                    is_staff=False,
                    is_superuser=False
                )
                usuario.set_password(solicitud.password)
                usuario.save()
                
                # Actualizar el estado de la solicitud
                solicitud.estado = 'aprobada'
                solicitud.resuelto_por = request.user
                solicitud.fecha_resolucion = timezone.now()
                solicitud.save()
                
                messages.success(request, f'Solicitud de {solicitud.nombre_completo} aprobada correctamente.')
                
            elif accion == 'rechazar':
                # Actualizar el estado de la solicitud
                solicitud.estado = 'rechazada'
                solicitud.resuelto_por = request.user
                solicitud.fecha_resolucion = timezone.now()
                solicitud.save()
                
                messages.success(request, f'Solicitud de {solicitud.nombre_completo} rechazada.')
            
            return redirect('digitalizacion:gestion_solicitudes')
            
        except SolicitudRegistro.DoesNotExist:
            messages.error(request, 'La solicitud no existe o ya ha sido procesada.')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
    
    # Contexto para la plantilla
    context = {
        'title': 'Gestión de Solicitudes de Registro',
        'solicitudes': solicitudes,
        'breadcrumb': [
            {'name': 'Inicio', 'url': reverse_lazy('digitalizacion:dashboard')},
            {'name': 'Panel de Administración', 'url': reverse_lazy('digitalizacion:panel_administracion')},
            {'name': 'Gestión de Solicitudes', 'active': True}
        ],
    }
    
    return render(request, 'digitalizacion/admin/solicitudes/gestion_solicitudes.html', context)
