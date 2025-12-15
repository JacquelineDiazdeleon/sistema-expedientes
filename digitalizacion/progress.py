from django.db import models, transaction
from django.utils import timezone
from .models import Expediente

class ProgresoExpediente(models.Model):
    """
    Modelo para rastrear el progreso de un expediente
    """
    expediente = models.OneToOneField(
        Expediente,
        on_delete=models.CASCADE,
        related_name='progreso',
        primary_key=True
    )
    
    # Contadores de áreas
    areas_totales = models.PositiveIntegerField(default=0)
    areas_completadas = models.PositiveIntegerField(default=0)
    
    # Porcentaje de progreso (0-100)
    porcentaje = models.PositiveIntegerField(default=0)
    
    # Fechas de seguimiento
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Detalles adicionales (puede usarse para almacenar información específica de áreas)
    detalles = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Progreso de Expediente"
        verbose_name_plural = "Progreso de Expedientes"
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"Progreso de {self.expediente.numero_expediente}: {self.porcentaje}%"
    
    def actualizar_progreso(self, areas_totales=None, areas_completadas=None, detalles=None):
        """
        Actualiza el progreso del expediente
        """
        if areas_totales is not None:
            self.areas_totales = areas_totales
        if areas_completadas is not None:
            self.areas_completadas = areas_completadas
        if detalles is not None:
            self.detalles = detalles
        
        # Calcular porcentaje
        if self.areas_totales > 0:
            self.porcentaje = min(100, int((self.areas_completadas / self.areas_totales) * 100))
        else:
            self.porcentaje = 0
        
        self.save()
        return self.porcentaje
    
    @classmethod
    def obtener_para_expediente(cls, expediente_id):
        """
        Obtiene o crea un registro de progreso para el expediente
        """        
        with transaction.atomic():
            # Usar select_for_update para evitar condiciones de carrera
            progreso, creado = cls.objects.select_for_update().get_or_create(
                expediente_id=expediente_id,
                defaults={
                    'areas_totales': 0,
                    'areas_completadas': 0,
                    'porcentaje': 0,
                    'detalles': {}
                }
            )
            
            # Si es un nuevo registro, inicializar con los valores actuales
            if creado and hasattr(progreso.expediente, 'get_progreso'):
                progreso_data = progreso.expediente.get_progreso()
                if progreso_data:
                    progreso.areas_totales = progreso_data.get('total', 0)
                    progreso.areas_completadas = progreso_data.get('completadas', 0)
                    progreso.porcentaje = progreso_data.get('porcentaje', 0)
                    progreso.save()
            
            return progreso
