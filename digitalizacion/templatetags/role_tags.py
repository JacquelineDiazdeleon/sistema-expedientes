"""
Template tags para verificar permisos y roles de usuario
"""
from django import template
from ..role_utils import (
    puede_ver_expedientes, puede_crear_expedientes, puede_editar_expedientes,
    puede_eliminar_expedientes, puede_administrar_sistema, puede_aprobar_usuarios,
    es_visualizador, es_editor, es_administrador
)

register = template.Library()


@register.filter
def puede_ver_exp(user):
    """Verifica si el usuario puede ver expedientes"""
    return puede_ver_expedientes(user)


@register.filter
def puede_crear_exp(user):
    """Verifica si el usuario puede crear expedientes"""
    return puede_crear_expedientes(user)


@register.filter
def puede_editar_exp(user):
    """Verifica si el usuario puede editar expedientes"""
    return puede_editar_expedientes(user)


@register.filter
def puede_eliminar_exp(user):
    """Verifica si el usuario puede eliminar expedientes"""
    return puede_eliminar_expedientes(user)


@register.filter
def puede_administrar(user):
    """Verifica si el usuario puede administrar el sistema"""
    return puede_administrar_sistema(user)


@register.filter
def puede_aprobar(user):
    """Verifica si el usuario puede aprobar usuarios"""
    return puede_aprobar_usuarios(user)


@register.filter
def es_visual(user):
    """Verifica si el usuario es visualizador"""
    return es_visualizador(user)


@register.filter
def es_edit(user):
    """Verifica si el usuario es editor"""
    return es_editor(user)


@register.filter
def es_admin(user):
    """Verifica si el usuario es administrador"""
    return es_administrador(user)

