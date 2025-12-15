"""
Señales para el manejo de actualizaciones de expedientes
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import (
    Expediente, DocumentoExpediente, 
    ComentarioEtapa, EtapaExpediente,
    HistorialExpediente, NotaExpediente
)

def limpiar_cache_ultima_actualizacion(sender, instance, **kwargs):
    """Limpia la caché de última actualización para un expediente"""
    expediente = None
    
    # Determinar el expediente relacionado según el modelo
    if hasattr(instance, 'expediente'):
        expediente = instance.expediente
    elif isinstance(instance, Expediente):
        expediente = instance
    
    if expediente and expediente.id:
        cache_key = f'expediente_{expediente.id}_ultima_actualizacion'
        cache.delete(cache_key)
        
        # También actualizar el campo fecha_actualizacion del expediente
        # para que las consultas que no usan el caché también sean precisas
        if not isinstance(instance, Expediente):
            from django.utils import timezone
            Expediente.objects.filter(id=expediente.id).update(
                fecha_actualizacion=timezone.now()
            )

# Registrar las señales para todos los modelos relevantes
for model in [Expediente, DocumentoExpediente, ComentarioEtapa, 
              EtapaExpediente, HistorialExpediente, NotaExpediente]:
    post_save.connect(limpiar_cache_ultima_actualizacion, sender=model)
    post_delete.connect(limpiar_cache_ultima_actualizacion, sender=model)
