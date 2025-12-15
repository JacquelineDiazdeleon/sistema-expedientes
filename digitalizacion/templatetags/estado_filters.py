from django import template

register = template.Library()

@register.filter(name='estado_badge')
def estado_badge(estado):
    """
    Devuelve la clase de color de Bootstrap para el estado del expediente.
    """
    estado_colors = {
        'borrador': 'secondary',
        'en_revision': 'info',
        'aprobado': 'success',
        'rechazado': 'danger',
        'en_progreso': 'primary',
        'completado': 'success',
        'archivado': 'dark',
        'pendiente': 'warning',
    }
    return estado_colors.get(estado, 'secondary')
