"""
Módulo que contiene la lógica de actualización de progreso para los expedientes.
"""
import logging

logger = logging.getLogger(__name__)

def actualizar_progreso_expediente(expediente, porcentaje, areas_completadas, total_areas):
    """
    Actualiza el progreso de un expediente en la base de datos.
    
    Args:
        expediente: Instancia del modelo Expediente
        porcentaje: Porcentaje de progreso (0-100)
        areas_completadas: Número de áreas completadas
        total_areas: Número total de áreas
    """
    from django.db import transaction
    from django.utils import timezone
    
    try:
        with transaction.atomic():
            # Guardar el estado anterior para el historial
            estado_anterior = expediente.estado
            progreso_anterior = getattr(expediente, 'progreso', 0)
            
            # Actualizar el progreso
            expediente.progreso = porcentaje
            expediente.fecha_actualizacion = timezone.now()
            
            # Determinar el nuevo estado basado en el progreso
            if porcentaje == 100:
                nuevo_estado = 'completo'  # Usar 'completo' que es el valor en el modelo
            elif porcentaje < 100 and estado_anterior == 'completo':
                # Si el progreso baja del 100%, volver a 'en_proceso'
                nuevo_estado = 'en_proceso'
            else:
                nuevo_estado = estado_anterior
            
            # Actualizar el estado si es necesario
            if nuevo_estado != estado_anterior:
                expediente.estado = nuevo_estado
                update_fields = ['progreso', 'estado', 'fecha_actualizacion']
                
                # Registrar el cambio de estado en el historial
                from .models import HistorialExpediente
                HistorialExpediente.crear_registro(
                    usuario=expediente.modificado_por,
                    accion='cambio_estado',
                    modelo='Expediente',
                    objeto_id=expediente.id,
                    detalles=f'Cambio de estado: {estado_anterior} → {nuevo_estado}. Progreso: {progreso_anterior}% → {porcentaje}%',
                    etapa_anterior=estado_anterior,
                    etapa_nueva=nuevo_estado
                )
            else:
                update_fields = ['progreso', 'fecha_actualizacion']
            
            # Guardar los cambios
            expediente.save(update_fields=update_fields)
            
            # Registrar el cambio de progreso en el historial
            if progreso_anterior != porcentaje:
                from .models import HistorialExpediente
                HistorialExpediente.crear_registro(
                    usuario=expediente.modificado_por,
                    accion='actualizacion_progreso',
                    modelo='Expediente',
                    objeto_id=expediente.id,
                    detalles=f'Progreso actualizado: {progreso_anterior}% → {porcentaje}% ({areas_completadas}/{total_areas} áreas completadas)'
                )
            
            return True
    except Exception as e:
        logger.error(f"Error al actualizar progreso del expediente {getattr(expediente, 'id', 'N/A')}: {str(e)}")
        return False
