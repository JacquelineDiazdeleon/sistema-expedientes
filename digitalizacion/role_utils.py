"""
Utilidades para verificar permisos y roles de usuario
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def tiene_rol(user, nombre_rol):
    """Verifica si el usuario tiene un rol específico"""
    if not user or not user.is_authenticated:
        return False
    if not hasattr(user, 'perfil') or not user.perfil:
        return False
    if not user.perfil.rol:
        return False
    return user.perfil.rol.nombre == nombre_rol


def puede_ver_expedientes(user):
    """Verifica si el usuario puede ver expedientes"""
    if not user or not user.is_authenticated:
        return False
    # Superusuarios siempre pueden ver
    if user.is_superuser:
        return True
    # Si no tiene perfil, asumimos que puede ver (por defecto)
    if not hasattr(user, 'perfil') or not user.perfil:
        return True
    # Si tiene perfil pero no tiene rol, puede ver (por defecto)
    if not user.perfil.rol:
        return True
    # Si tiene rol, verificar el permiso del rol
    return user.perfil.rol.puede_ver_expedientes


def puede_crear_expedientes(user):
    """Verifica si el usuario puede crear expedientes"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'perfil') or not user.perfil or not user.perfil.rol:
        return False
    return user.perfil.rol.puede_crear_expedientes


def puede_editar_expedientes(user):
    """Verifica si el usuario puede editar expedientes"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'perfil') or not user.perfil or not user.perfil.rol:
        return False
    return user.perfil.rol.puede_editar_expedientes


def puede_eliminar_expedientes(user):
    """Verifica si el usuario puede eliminar expedientes"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'perfil') or not user.perfil or not user.perfil.rol:
        return False
    return user.perfil.rol.puede_eliminar_expedientes


def puede_administrar_sistema(user):
    """Verifica si el usuario puede administrar el sistema"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'perfil') or not user.perfil or not user.perfil.rol:
        return False
    return user.perfil.rol.puede_administrar_sistema


def puede_aprobar_usuarios(user):
    """Verifica si el usuario puede aprobar solicitudes de registro"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, 'perfil') or not user.perfil or not user.perfil.rol:
        return False
    return user.perfil.rol.puede_aprobar_usuarios


def es_visualizador(user):
    """Verifica si el usuario es visualizador"""
    return tiene_rol(user, 'visualizador')


def es_editor(user):
    """Verifica si el usuario es editor"""
    return tiene_rol(user, 'editor')


def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return tiene_rol(user, 'administrador') or (user and user.is_superuser)


def decorador_requiere_permiso(permiso_func, redirect_to='digitalizacion:dashboard', mensaje_error='No tienes permisos para realizar esta acción'):
    """
    Decorador para verificar permisos antes de ejecutar una vista
    
    Args:
        permiso_func: Función que verifica el permiso (ej: puede_crear_expedientes)
        redirect_to: URL a donde redirigir si no tiene permiso
        mensaje_error: Mensaje a mostrar si no tiene permiso
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not permiso_func(request.user):
                messages.error(request, mensaje_error)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

