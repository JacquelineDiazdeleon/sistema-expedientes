from django.db.models import Q
from django.core.cache import cache
from ..models import AreaTipoExpediente

def get_areas_por_expediente(expediente):
    """
    Obtiene las áreas configuradas para un expediente específico basado en su tipo y subtipo.
    
    Args:
        expediente: Instancia del modelo Expediente
        
    Returns:
        QuerySet de áreas configuradas para el tipo y subtipo del expediente
    """
    if not expediente or not expediente.tipo_expediente:
        return AreaTipoExpediente.objects.none()
    
    # Crear una clave única para el cache
    cache_key = f'areas_tipo_{expediente.tipo_expediente}_subtipo_{expediente.subtipo_expediente or ""}'
    
    # Intentar obtener del cache primero
    cached_areas = cache.get(cache_key)
    if cached_areas is not None:
        return cached_areas
    
    # Obtener áreas específicas para el subtipo (si existe)
    if expediente.subtipo_expediente:
        areas = AreaTipoExpediente.objects.filter(
            Q(tipo_expediente=expediente.tipo_expediente) &
            (Q(subtipo_expediente=expediente.subtipo_expediente) | Q(subtipo_expediente__isnull=True)) &
            Q(activa=True)
        ).order_by('orden', 'titulo').distinct()
    else:
        # Si no hay subtipo, obtener solo las áreas generales para el tipo de expediente
        areas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            subtipo_expediente__isnull=True,
            activa=True
        ).order_by('orden', 'titulo')
    
    # Guardar en cache por 1 hora
    cache.set(cache_key, areas, 3600)
    return areas

def get_area_por_id(area_id, expediente):
    """
    Obtiene un área específica validando que pertenezca al tipo de expediente
    
    Args:
        area_id: ID del área a buscar
        expediente: Instancia del modelo Expediente
        
    Returns:
        AreaTipoExpediente si se encuentra y es válida, None en caso contrario
    """
    try:
        area = AreaTipoExpediente.objects.get(id=area_id, activa=True)
        
        # Verificar que el área corresponda al tipo de expediente
        if area.tipo_expediente != expediente.tipo_expediente:
            return None
            
        # Si el área tiene subtipo, debe coincidir con el del expediente
        if area.subtipo_expediente and area.subtipo_expediente != expediente.subtipo_expediente:
            return None
            
        return area
    except AreaTipoExpediente.DoesNotExist:
        return None
