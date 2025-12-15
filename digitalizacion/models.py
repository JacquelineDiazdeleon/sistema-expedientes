from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import os


class TipoDocumento(models.Model):
    """Modelo para los tipos de documentos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Departamento(models.Model):
    """Modelo para los departamentos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


def upload_to(instance, filename):
    """FunciÃ³n para definir la ruta de subida de archivos"""
    ext = filename.split('.')[-1]
    fecha = timezone.now()
    filename = f"{instance.expediente.numero_expediente}_{fecha.strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('expedientes', str(fecha.year), str(fecha.month), filename)


class Expediente(models.Model):
    """Modelo principal para los expedientes"""
    # Opciones de tipos de expediente
    TIPO_CHOICES = [
        ('licitacion', 'Licitación'),
        ('concurso_invitacion', 'Concurso por invitación'),
        ('compra_directa', 'Compra directa'),
        ('adjudicacion_directa', 'Adjudicación directa'),
    ]

    # Subtipos para licitaciÃ³n
    SUBTIPO_LICITACION_CHOICES = [
        ('recurso_propio', 'Recurso propio'),
        ('fondo_federal', 'Fondo federal'),
    ]

    # Opciones para compatibilidad (mantener por ahora)
    FUENTE_CHOICES = [
        ('propio_municipal', 'Propio Municipal'),
        ('estatal', 'Estatal'),
        ('federal', 'Federal'),
    ]

    TIPO_ADQUISICION_CHOICES = [
        ('bienes', 'Bienes'),
        ('servicios', 'Servicios'),
        ('arrendamientos', 'Arrendamientos'),
    ]

    MODALIDAD_MONTO_CHOICES = [
        ('compra_directa', 'Compra Directa'),
        ('concurso_invitacion', 'Concurso por Invitación'),
        ('licitacion', 'Licitación'),
        ('adjudicacion_directa', 'Adjudicación Directa'),
    ]

    ESTADOS_EXPEDIENTE = [
        ('en_proceso', 'En proceso'),
        ('completo', 'Expediente completo'),
        ('rechazado', 'Rechazado'),
    ]

    ESTADO_CHOICES = [
        ('inicio', 'Inicio'),
        ('solicitud_area', 'Solicitud del Área'),
        ('cotizacion', 'Cotización'),
        ('requisicion_sima', 'Requisición SIMA'),
        ('suficiencia_presupuestal', 'Suficiencia Presupuestal'),
        ('aprobacion_director', 'Aprobación Director Administrativo'),
        ('aprobacion_secretario', 'Aprobación Secretario'),
        ('notificacion_compras', 'Notificación a Compras Municipales'),
        ('valoracion_tipo', 'Valoración para Tipo de Adquisición'),
        ('adjudicacion', 'Adjudicación'),
        ('formalizacion', 'Formalización con Orden de Compra'),
        ('contrato', 'Contrato'),
        ('recepcion_bien', 'Recepción del Bien o Servicio'),
        ('recepcion_facturacion', 'Recepción de Facturación'),
        ('generacion_evidencia', 'Generación de Evidencia'),
        ('envio_compras', 'Envío de Expediente a Compras'),
        ('pago', 'Pago'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
        ('oficio_control_patrimonial', 'Oficio de Control Patrimonial'),
    ]

    # InformaciÃ³n bÃ¡sica
    numero_expediente = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True, 
        help_text="Se genera automáticamente si se deja en blanco"
    )
    titulo = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Título del expediente (opcional)"
    )
    descripcion = models.TextField(
        blank=True, 
        null=True,
        help_text="Descripción del expediente (opcional)"
    )
    
    # Estado del expediente
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_EXPEDIENTE, 
        default='en_proceso',
        help_text="Estado actual del expediente"
    )
    
    # Tipo de expediente
    tipo_expediente = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        help_text="Tipo de expediente"
    )
    
    # Campos especÃ­ficos segÃºn el tipo
    giro = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Giro del expediente (opcional)",
        verbose_name="Giro"
    )
    fuente_financiamiento = models.CharField(
        max_length=20, 
        choices=FUENTE_CHOICES,
        blank=True,
        null=True,
        help_text="Fuente de financiamiento del expediente (solo para ciertos tipos de expediente)",
        verbose_name="Fuente de Financiamiento"
    )
    tipo_adquisicion = models.CharField(
        max_length=20, 
        choices=TIPO_ADQUISICION_CHOICES,
        default='bienes',
        help_text="Tipo de adquisición del expediente",
        verbose_name="Tipo de Adquisición"
    )
    modalidad_monto = models.CharField(
        max_length=30, 
        choices=MODALIDAD_MONTO_CHOICES, 
        blank=True, 
        null=True,
        help_text="Modalidad de monto (opcional)",
        verbose_name="Modalidad de Monto"
    )
    
    # Subtipo especÃ­fico del expediente (determina quÃ© Ã¡reas/formulario usar)
    subtipo_expediente = models.CharField(
        max_length=30, 
        blank=True, 
        null=True,
        help_text="Subtipo específico que determina qué áreas usar (ej: bienes, servicios, etc.)"
    )
    
    # Estado actual del expediente
    estado_actual = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='inicio')
    
    # NÃºmero SIMA
    numero_sima = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Número o código SIMA asignado al expediente",
        verbose_name="Número SIMA"
    )
    
    # InformaciÃ³n adicional
    departamento = models.ForeignKey(
        Departamento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text="Departamento al que pertenece el expediente (opcional)",
        verbose_name="Departamento"
    )
    fecha_expediente = models.DateField(
        default=timezone.now, 
        blank=True, 
        null=True,
        help_text="Fecha del expediente (opcional)",
        verbose_name="Fecha del Expediente"
    )
    fecha_vencimiento = models.DateField(
        blank=True, 
        null=True,
        help_text="Fecha de vencimiento (opcional)",
        verbose_name="Fecha de Vencimiento"
    )
    
    # Usuarios
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='expedientes_creados',
        help_text="Usuario que creó el expediente"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del expediente"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha de última actualización"
    )
    
    # Progreso del expediente (0-100%)
    progreso = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de completado del expediente (0-100)"
    )
    
    # Metadata
    palabras_clave = models.TextField(
        blank=True, 
        null=True, 
        help_text="Palabras clave separadas por comas (opcional)",
        verbose_name="Palabras Clave"
    )
    observaciones = models.TextField(
        blank=True, 
        null=True,
        help_text="Observaciones adicionales (opcional)",
        verbose_name="Observaciones"
    )
    confidencial = models.BooleanField(
        default=False,
        help_text="Â¿El expediente es confidencial?",
        verbose_name="Confidencial"
    )
    
    # InformaciÃ³n de rechazo
    motivo_rechazo = models.TextField(
        blank=True, 
        null=True, 
        help_text="Motivo por el cual fue rechazado el expediente",
        verbose_name="Motivo de Rechazo"
    )
    fecha_rechazo = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="Fecha y hora del rechazo",
        verbose_name="Fecha de Rechazo"
    )
    rechazado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='expedientes_rechazados',
        help_text="Usuario que rechazó el expediente",
        verbose_name="Rechazado por"
    )
    
    class Meta:
        verbose_name = "Expediente"
        verbose_name_plural = "Expedientes"
        ordering = ['-fecha_creacion']

    def clean(self):
        """
        Método clean para manejar la validación personalizada y limpieza de datos
        """
        # Limpiar cadenas vacías para campos opcionales
        for field in ['titulo', 'descripcion', 'giro', 'palabras_clave', 'observaciones']:
            value = getattr(self, field, '')
            if value == '':
                setattr(self, field, None)
                
        # Asegurarse de que la fecha de expediente tenga un valor por defecto
        if not self.fecha_expediente:
            self.fecha_expediente = timezone.now().date()
            
        # Validar que el tipo_expediente tenga un valor vÃ¡lido
        if not self.tipo_expediente:
            raise ValidationError({
                'tipo_expediente': 'El tipo de expediente es obligatorio.'
            })
            
        # Validar que el creador_por estÃ© establecido
        if not hasattr(self, 'creado_por') or not self.creado_por:
            # Si no hay usuario autenticado, usar el usuario demo
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                self.creado_por = User.objects.get(username='demo')
            except User.DoesNotExist:
                # Si no existe el usuario demo, usar el primer superusuario
                admin = User.objects.filter(is_superuser=True).first()
                if admin:
                    self.creado_por = admin
                else:
                    # Si no hay superusuarios, crear uno temporal
                    self.creado_por = User.objects.create_user(
                        username='temp_admin',
                        email='temp@example.com',
                        password='temp_password',
                        is_superuser=True,
                        is_staff=True
                    )
        
        return super().clean()
        
    def save(self, *args, **kwargs):
        """
        Método save personalizado para manejar la lógica de guardado
        """
        # Limpiar y validar los datos antes de guardar
        self.full_clean()
        
        # Establecer fecha_expediente si no se proporciona
        if not self.fecha_expediente:
            self.fecha_expediente = timezone.now().date()
            
        # Mapeo de valores del formulario a los valores del modelo
        tipo_expediente_mapping = {
            'LicitaciÃ³n': 'licitacion',
            'Concurso por invitaciÃ³n': 'concurso_invitacion',
            'Compra directa': 'compra_directa',
            'AdjudicaciÃ³n directa': 'adjudicacion_directa'
        }
        
        # Mapear el tipo de expediente si es necesario
        if self.tipo_expediente in tipo_expediente_mapping:
            self.tipo_expediente = tipo_expediente_mapping[self.tipo_expediente]
        
        # Mapear fuente de financiamiento
        if self.fuente_financiamiento:
            self.fuente_financiamiento = self.fuente_financiamiento.lower().replace(' ', '_')
        
        # Mapear tipo de adquisiciÃ³n
        if self.tipo_adquisicion:
            self.tipo_adquisicion = self.tipo_adquisicion.lower()
        
        # Mapear modalidad de monto
        if self.modalidad_monto:
            modalidad_mapping = {
                'Compra directa': 'compra_directa',
                'Concurso por invitaciÃ³n': 'concurso_invitacion',
                'LicitaciÃ³n': 'licitacion',
                'AdjudicaciÃ³n directa': 'adjudicacion_directa'
            }
            self.modalidad_monto = modalidad_mapping.get(self.modalidad_monto, self.modalidad_monto.lower().replace(' ', '_'))
        
        # Generar nÃºmero de expediente automÃ¡ticamente si no se proporciona
        if not self.numero_expediente:
            from django.utils import timezone
            from django.template.defaultfilters import slugify
            
            # Formato: INI-AAAAMMDD-HHMMSS
            timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
            base_numero = f"EXP-{timestamp}"
            
            # Asegurarse de que el nÃºmero sea Ãºnico
            counter = 1
            self.numero_expediente = base_numero
            while Expediente.objects.filter(numero_expediente=self.numero_expediente).exists():
                self.numero_expediente = f"{base_numero}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.numero_expediente:
            return f"{self.numero_expediente} - {self.titulo}"
        return f"Nuevo Expediente - {self.titulo}"

    def get_palabras_clave_list(self):
        """Retorna las palabras clave como lista"""
        if self.palabras_clave:
            return [palabra.strip() for palabra in self.palabras_clave.split(',')]
        return []

    def actualizar_estado_a_completado(self):
        """Actualiza el estado del expediente a 'completado' y registra en el historial"""
        from django.utils import timezone
            
        # Guardar el estado anterior
        estado_anterior = self.estado_actual
            
        # Actualizar el estado
        self.estado_actual = 'completado'
        self.fecha_actualizacion = timezone.now()
        self.save(update_fields=['estado_actual', 'fecha_actualizacion'])
            
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=self,
            usuario=None,  # O el usuario del sistema
            accion='completado_automatico',
            descripcion='Expediente completado automáticamente al alcanzar el 100% de progreso',
            etapa_anterior=estado_anterior,
            etapa_nueva='completado'
        )
    
    def get_areas_configuradas(self):
        """
        Obtiene las áreas configuradas para este expediente, considerando el tipo y subtipo.
        Si no hay áreas específicas, intenta obtener áreas genéricas sin filtrar por subtipo.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        from .models import AreaTipoExpediente
        
        try:
            # Obtener áreas para el tipo de expediente
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=self.tipo_expediente,
                activa=True
            )
            
            logger.debug(f'[get_areas_configuradas] Expediente {self.id}: Tipo={self.tipo_expediente}, Áreas encontradas (sin filtrar subtipo): {areas.count()}')
            
            # Filtrar por subtipo si existe
            if hasattr(self, 'subtipo_expediente') and self.subtipo_expediente:
                # Para licitación, el subtipo puede estar con o sin prefijo "licitacion_"
                if self.tipo_expediente == 'licitacion':
                    # Buscar con el subtipo tal cual y con el prefijo "licitacion_"
                    subtipo_prefijo = f'licitacion_{self.subtipo_expediente}'
                    areas_filtradas = areas.filter(
                        Q(subtipo_expediente=self.subtipo_expediente) | 
                        Q(subtipo_expediente=subtipo_prefijo) |
                        Q(subtipo_expediente__isnull=True) | 
                        Q(subtipo_expediente='')
                    )
                    logger.debug(f'[get_areas_configuradas] Expediente {self.id}: Subtipo={self.subtipo_expediente} (también buscando {subtipo_prefijo}), Áreas después de filtrar: {areas_filtradas.count()}')
                else:
                    # Para otros tipos, buscar solo con el subtipo exacto
                    areas_filtradas = areas.filter(
                        Q(subtipo_expediente=self.subtipo_expediente) | 
                        Q(subtipo_expediente__isnull=True) | 
                        Q(subtipo_expediente='')
                    )
                    logger.debug(f'[get_areas_configuradas] Expediente {self.id}: Subtipo={self.subtipo_expediente}, Áreas después de filtrar: {areas_filtradas.count()}')
                
                # Si no hay áreas después de filtrar por subtipo, usar todas las áreas del tipo
                if areas_filtradas.count() == 0:
                    logger.warning(f'[get_areas_configuradas] Expediente {self.id}: No hay áreas para subtipo {self.subtipo_expediente}, usando todas las áreas del tipo')
                    areas_filtradas = areas
                
                areas = areas_filtradas
            else:
                # Si no hay subtipo, obtener áreas genéricas
                areas_genéricas = areas.filter(
                    Q(subtipo_expediente__isnull=True) | 
                    Q(subtipo_expediente='')
                )
                logger.debug(f'[get_areas_configuradas] Expediente {self.id}: Sin subtipo, Áreas genéricas: {areas_genéricas.count()}')
                
                # Si no hay áreas genéricas, usar todas las áreas del tipo
                if areas_genéricas.count() == 0:
                    logger.warning(f'[get_areas_configuradas] Expediente {self.id}: No hay áreas genéricas, usando todas las áreas del tipo')
                    areas = areas
                else:
                    areas = areas_genéricas
            
            areas_ordenadas = areas.order_by('orden')
            logger.info(f'[get_areas_configuradas] Expediente {self.id}: Total áreas configuradas: {areas_ordenadas.count()}')
            
            return areas_ordenadas
        except Exception as e:
            logger.error(f'[get_areas_configuradas] Error al obtener áreas para expediente {self.id}: {str(e)}', exc_info=True)
            return AreaTipoExpediente.objects.none()
    
    def actualizar_progreso(self, guardar=True):
        """
        Actualiza el progreso del expediente basado en las áreas completadas.
        Retorna el porcentaje de avance (0-100).
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            areas = self.get_areas_configuradas()
            total_areas = areas.count()
            
            if total_areas == 0:
                self.progreso = 0
                if guardar:
                    self.save(update_fields=['progreso', 'fecha_actualizacion'])
                return 0
            
            # Contar áreas completadas
            areas_completadas = 0
            for area in areas:
                if area.etapa_completada(self):
                    areas_completadas += 1
            
            # Calcular porcentaje
            progreso = int((areas_completadas / total_areas) * 100)
            self.progreso = min(100, max(0, progreso))  # Asegurar que esté entre 0 y 100
            
            # Actualizar estado según el progreso
            if self.progreso == 100 and self.estado != 'completo':
                # Si el progreso llega a 100%, marcar como completo
                self.estado = 'completo'
                # También actualizar estado_actual a 'completado' para que se muestre correctamente en la lista
                if self.estado_actual != 'completado':
                    self.estado_actual = 'completado'
                update_fields = ['progreso', 'estado', 'estado_actual', 'fecha_actualizacion']
                logger.info(f"Expediente {self.id} marcado como COMPLETO (progreso 100%)")
            elif self.progreso < 100 and self.estado == 'completo':
                # Si el progreso baja del 100% y estaba completo, volver a en_proceso
                self.estado = 'en_proceso'
                # También actualizar estado_actual a 'en_proceso'
                if self.estado_actual == 'completado':
                    self.estado_actual = 'en_proceso'
                update_fields = ['progreso', 'estado', 'estado_actual', 'fecha_actualizacion']
                logger.info(f"Expediente {self.id} cambiado a EN_PROCESO (progreso bajó a {self.progreso}%)")
            else:
                update_fields = ['progreso', 'fecha_actualizacion']
            
            if guardar:
                self.save(update_fields=update_fields)
            
            logger.info(f"Progreso actualizado para expediente {self.id}: {self.progreso}% ({areas_completadas}/{total_areas} áreas)")
            return self.progreso
            
        except Exception as e:
            logger.error(f"Error al actualizar progreso del expediente {self.id}: {str(e)}")
            return self.progreso if hasattr(self, 'progreso') else 0
    
    def get_progreso(self):
        """
        Método que retorna la información de progreso en formato de diccionario.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            areas = self.get_areas_configuradas()
            total_areas = areas.count()
            
            logger.info(f'[get_progreso] Expediente {self.id}: Total áreas configuradas: {total_areas}')
            
            # Si no hay áreas configuradas, retornar 0%
            if total_areas == 0:
                logger.warning(f'[get_progreso] Expediente {self.id}: No hay áreas configuradas')
                return {
                    'porcentaje': 0,
                    'completadas': 0,
                    'total': 0,
                    'texto': '0/0 áreas completadas',
                    'areas': []
                }
            
            # Contar áreas completadas y recopilar información detallada
            areas_completadas = 0
            areas_info = []
            
            for area in areas:
                try:
                    completada = area.etapa_completada(self)
                    if completada:
                        areas_completadas += 1
                        logger.debug(f'[get_progreso] Expediente {self.id}: Área {area.titulo} completada')
                    
                    # Obtener documentos del área
                    documentos = self.documentos.filter(area=area).values('id', 'nombre_documento', 'fecha_subida')
                    documentos_count = documentos.count()
                    
                    areas_info.append({
                        'id': area.id,
                        'nombre': area.nombre,
                        'titulo': area.titulo,
                        'completada': completada,
                        'documentos': list(documentos),
                        'documentos_count': documentos_count,
                        'tipo_area': area.tipo_area,
                        'obligatoria': area.obligatoria
                    })
                except Exception as area_error:
                    logger.error(f'[get_progreso] Error al procesar área {area.id} para expediente {self.id}: {str(area_error)}')
                    continue
            
            # Calcular porcentaje
            porcentaje = int((areas_completadas / total_areas) * 100) if total_areas > 0 else 0
            
            logger.info(f'[get_progreso] Expediente {self.id}: Progreso calculado: {porcentaje}% ({areas_completadas}/{total_areas} áreas)')
            
            return {
                'porcentaje': porcentaje,
                'completadas': areas_completadas,
                'total': total_areas,
                'texto': f'{areas_completadas}/{total_areas} áreas completadas ({porcentaje}%)' if porcentaje < 100 else 'Expediente completo',
                'areas': areas_info
            }
        except Exception as e:
            logger.error(f'[get_progreso] Error al calcular progreso para expediente {self.id}: {str(e)}', exc_info=True)
            return {
                'porcentaje': 0,
                'completadas': 0,
                'total': 0,
                'texto': 'Error al calcular progreso',
                'areas': []
            }
    
    def rechazar_expediente(self, usuario, motivo):
        """Rechaza el expediente con motivo y usuario"""
        self.estado_actual = 'rechazado'
        self.motivo_rechazo = motivo
        self.fecha_rechazo = timezone.now()
        self.rechazado_por = usuario
        self.save()
            
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=self,
            usuario=usuario,
            accion='rechazado',
            descripcion=f'Expediente rechazado. Motivo: {motivo}',
            etapa_anterior=self.estado_actual,
            etapa_nueva='rechazado'
        )
    
    def esta_rechazado(self):
        """Verifica si el expediente está rechazado"""
        return self.estado_actual == 'rechazado'


class EtapaExpediente(models.Model):
    """Modelo para las etapas de cada expediente"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='etapas')
    nombre_etapa = models.CharField(max_length=30, choices=Expediente.ESTADO_CHOICES)
    completada = models.BooleanField(default=False)
    fecha_completada = models.DateTimeField(blank=True, null=True)
    completada_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Etapa de Expediente"
        verbose_name_plural = "Etapas de Expedientes"
        unique_together = ['expediente', 'nombre_etapa']
        ordering = ['expediente', 'nombre_etapa']

    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.get_nombre_etapa_display()}"


class DocumentoExpediente(models.Model):
    """Modelo para los documentos subidos en cada etapa"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='documentos')
    etapa = models.CharField(max_length=30, choices=Expediente.ESTADO_CHOICES)
    nombre_documento = models.CharField(max_length=200)
    archivo = models.FileField(upload_to=upload_to)
    descripcion = models.TextField(blank=True, null=True)
    
    # Metadata del archivo
    tamano_archivo = models.PositiveIntegerField(blank=True, null=True)
    tipo_archivo = models.CharField(max_length=100, blank=True, null=True, help_text="Tipo de archivo (extensión o MIME type)")
    
    # Usuario y fechas
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    # ValidaciÃ³n
    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_validados')
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    
    # RelaciÃ³n con el Ã¡rea especÃ­fica
    area = models.ForeignKey(
        'AreaTipoExpediente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
        help_text="Ãrea especÃ­fica a la que pertenece este documento"
    )
    
    class Meta:
        verbose_name = "Documento de Expediente"
        verbose_name_plural = "Documentos de Expedientes"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.nombre_documento}"

    def save(self, *args, **kwargs):
        # Bandera para forzar la actualización del tamaño del archivo
        force_update_size = kwargs.pop('force_update_size', False)
        
        # Si hay un archivo, establecer el tipo de archivo y tamaño
        if self.archivo or force_update_size:
            # Establecer el tamaño del archivo primero
            try:
                self.tamano_archivo = self.archivo.size
            except (AttributeError, OSError):
                self.tamano_archivo = 0
            
            # Establecer el tipo de archivo basado en la extensión
            if hasattr(self.archivo, 'name'):
                # Obtener la extensión del archivo de forma segura
                try:
                    file_extension = os.path.splitext(self.archivo.name)[1].lower()
                    if file_extension:
                        extension = file_extension[1:]  # Quitar el punto
                        
                        # Diccionario de tipos MIME comunes a abreviaturas
                        mime_abreviados = {
                            'vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
                            'vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
                            'vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
                            'vnd.ms-excel.sheet.macroenabled.12': 'XLSM',
                            'vnd.ms-powerpoint.presentation.macroenabled.12': 'PPTM',
                            'vnd.ms-word.document.macroenabled.12': 'DOCM',
                            'vnd.adobe.pdf': 'PDF',
                            'jpeg': 'JPG',
                            'png': 'PNG',
                            'msword': 'DOC',
                            'vnd.ms-excel': 'XLS',
                            'vnd.ms-powerpoint': 'PPT',
                            'plain': 'TXT',
                            'csv': 'CSV',
                            'zip': 'ZIP',
                            'rar': 'RAR',
                            'gzip': 'GZ',
                            'x-7z-compressed': '7Z',
                            'x-rar-compressed': 'RAR',
                            'x-tar': 'TAR',
                            'x-zip-compressed': 'ZIP',
                            'vnd.oasis.opendocument.text': 'ODT',
                            'vnd.oasis.opendocument.spreadsheet': 'ODS',
                            'vnd.oasis.opendocument.presentation': 'ODP',
                            'rtf': 'RTF',
                            'json': 'JSON',
                            'xml': 'XML',
                            'html': 'HTML',
                            'css': 'CSS',
                            'javascript': 'JS',
                            'x-python': 'PY'
                        }
                        
                        # Intentar obtener el tipo MIME
                        try:
                            import mimetypes
                            mime_type, _ = mimetypes.guess_type(self.archivo.name)
                            
                            if mime_type:
                                # Extraer la parte final del MIME type
                                mime_part = mime_type.split('/')[-1].lower()
                                
                                # Usar abreviatura si está en el diccionario
                                if mime_part in mime_abreviados:
                                    self.tipo_archivo = mime_abreviados[mime_part]
                                # Si el tipo MIME es razonablemente corto, usarlo
                                elif len(mime_part) <= 45:
                                    self.tipo_archivo = mime_part.upper()
                                # Si es muy largo, usar la extensión del archivo
                                else:
                                    self.tipo_archivo = extension.upper() if extension else 'ARCHIVO'
                            else:
                                # Si no se puede determinar el MIME type, usar la extensión
                                self.tipo_archivo = extension.upper() if extension else 'ARCHIVO'
                        except (AttributeError, IndexError) as e:
                            # En caso de error, usar la extensión o un valor por defecto
                            self.tipo_archivo = extension.upper() if extension else 'ARCHIVO'
                            print(f"Error al obtener el tipo MIME: {str(e)}")
                    else:
                        self.tipo_archivo = 'ARCHIVO'
                except (AttributeError, IndexError) as e:
                    self.tipo_archivo = 'ARCHIVO'
                    print(f"Error al obtener la extensión del archivo: {str(e)}")
        
        # Asegurar que el tipo_archivo no sea demasiado largo (aunque ya debería estar controlado)
        if self.tipo_archivo and len(self.tipo_archivo) > 100:
            self.tipo_archivo = self.tipo_archivo[:100]
        
        super().save(*args, **kwargs)
        # Si después de todo no tenemos un tamaño, establecer 0
        if not hasattr(self, 'tamano_archivo') or self.tamano_archivo is None or self.tamano_archivo <= 0:
            self.tamano_archivo = 0
            DocumentoExpediente.objects.filter(pk=self.pk).update(tamano_archivo=0)
            print(f"No se pudo determinar el tamaño del archivo para documento {self.id}, establecido a 0")
        
        # Asegurarse de que el campo tamano_archivo se guarde en la base de datos
        if 'update_fields' not in kwargs and not kwargs.get('force_insert', False):
            # Actualizar solo el campo tamano_archivo para evitar bucles de guardado
            DocumentoExpediente.objects.filter(pk=self.pk).update(
                tamano_archivo=self.tamano_archivo if hasattr(self, 'tamano_archivo') and self.tamano_archivo is not None else 0,
                tipo_archivo=self.tipo_archivo if hasattr(self, 'tipo_archivo') else ''
            )

    @property
    def tamano_archivo_formateado(self):
        """Retorna el tamaño del archivo en formato legible"""
        if not self.tamano_archivo:
            return "0 Bytes"
        
        size = float(self.tamano_archivo)
        for unit in ['Bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0 or unit == 'GB':
                if unit == 'Bytes':
                    return f"{int(size)} {unit}"
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class ComentarioEtapa(models.Model):
    """Modelo para comentarios en cada etapa"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='comentarios')
    etapa = models.CharField(max_length=30, choices=Expediente.ESTADO_CHOICES)
    comentario = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_comentario = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Comentario de Etapa"
        verbose_name_plural = "Comentarios de Etapas"
        ordering = ['-fecha_comentario']

    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.get_etapa_display()}"





class HistorialExpediente(models.Model):
    """Modelo para el historial de cambios de expedientes"""
    expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE, 
        related_name='historial',
        null=True,  # Permite valores nulos para actividades del sistema
        blank=True,  # Permite valores en blanco en formularios
        help_text="Expediente relacionado (opcional para actividades del sistema)"
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,  # Cambiado de CASCADE a SET_NULL
        null=True,  # Permite valores nulos
        blank=True,  # Permite valores en blanco en formularios
        default=None,  # Valor por defecto
        help_text="Usuario que realizó la acción"
    )
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    etapa_anterior = models.CharField(max_length=30, blank=True, null=True)
    etapa_nueva = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Expediente"
        verbose_name_plural = "Historiales de Expedientes"
        ordering = ['-fecha']

    def __str__(self):
        if self.expediente:
            return f"{self.expediente.numero_expediente} - {self.accion} - {self.fecha}"
        else:
            return f"Sistema - {self.accion} - {self.fecha}"


class ConfiguracionSistema(models.Model):
    """Modelo para configuraciones del sistema"""
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ConfiguraciÃ³n del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        ordering = ['clave']

    def __str__(self):
        return f"{self.clave}: {self.valor[:50]}"


# Mantener compatibilidad con el modelo anterior
class Documento(models.Model):
    """Modelo de compatibilidad - se migrarÃ¡ a Expediente"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('digitalizado', 'Digitalizado'),
        ('verificado', 'Verificado'),
        ('archivado', 'Archivado'),
        ('rechazado', 'Rechazado'),
    ]

    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    numero_documento = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
    # ClasificaciÃ³n
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    
    # InformaciÃ³n del expediente
    giro = models.CharField(max_length=100, blank=True, null=True)
    fuente_financiamiento = models.CharField(max_length=20, blank=True, null=True)
    tipo_adquisicion = models.CharField(max_length=20, blank=True, null=True)
    modalidad_monto = models.CharField(max_length=30, blank=True, null=True)
    
    # Estado y prioridad
    estado = models.CharField(max_length=20, default='pendiente')
    prioridad = models.CharField(max_length=10, default='media')
    
    # Archivo digitalizado
    archivo_digital = models.FileField(upload_to='documentos/', blank=True, null=True)
    tamano_archivo = models.PositiveIntegerField(blank=True, null=True)
    
    # Fechas importantes
    fecha_documento = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_digitalizacion = models.DateTimeField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    
    # Usuarios
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos_creados')
    digitalizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_digitalizados')
    verificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_verificados')
    
    # Metadata
    palabras_clave = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    confidencial = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Documento (Legacy)"
        verbose_name_plural = "Documentos (Legacy)"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.numero_documento} - {self.titulo}"

    def get_palabras_clave_list(self):
        if self.palabras_clave:
            return [palabra.strip() for palabra in self.palabras_clave.split(',')]
        return []


class HistorialDocumento(models.Model):
    """Modelo para el historial de cambios de documentos (Legacy)"""
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado_anterior = models.CharField(max_length=20, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Documento (Legacy)"
        verbose_name_plural = "Historiales de Documentos (Legacy)"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.documento.numero_documento} - {self.accion} - {self.fecha}"


class NotaExpediente(models.Model):
    """Modelo para notas tipo post-it en expedientes"""
    COLORES_CHOICES = [
        ('amarillo', 'Amarillo'),
        ('azul', 'Azul'),
        ('verde', 'Verde'),
        ('rosa', 'Rosa'),
        ('naranja', 'Naranja'),
        ('morado', 'Morado'),
    ]
    
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='notas')
    documento = models.ForeignKey(
        DocumentoExpediente, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='notas',
        help_text="Documento especÃ­fico al que se adjunta la nota (opcional)"
    )
    
    # Contenido de la nota
    contenido = models.TextField(max_length=500, help_text="Contenido de la nota")
    color = models.CharField(max_length=10, choices=COLORES_CHOICES, default='amarillo')
    
    # Posición en la vista (para recordar dónde la puso el usuario)
    posicion_x = models.IntegerField(default=0, help_text="Posición horizontal en píxeles")
    posicion_y = models.IntegerField(default=0, help_text="Posición vertical en píxeles")
    
    # Metadatos
    creada_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True, help_text="Si está visible o archivada")
    
    class Meta:
        verbose_name = "Nota de Expediente"
        verbose_name_plural = "Notas de Expedientes"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Nota en {self.expediente.numero_expediente}: {self.contenido[:30]}..."


class Notificacion(models.Model):
    """Modelo para notificaciones del sistema"""
    TIPO_CHOICES = [
        ('mencion', 'Mención en Post-it'),
        ('comentario', 'Nuevo Comentario'),
        ('etapa', 'Cambio de Etapa'),
        ('documento', 'Nuevo Documento'),
        ('asignacion', 'Asignación de Expediente'),
        ('solicitud_registro', 'Solicitud de Registro'),
        ('solicitud_aprobada', 'Solicitud Aprobada'),
        ('usuario_eliminado', 'Usuario Eliminado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    enlace = models.CharField(max_length=500, blank=True, null=True, help_text="URL de destino")
    
    # Usuario que generÃ³ la notificaciÃ³n
    generada_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones_generadas')
    
    # Control de estado
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.username}: {self.titulo}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save()


class ComentarioArea(models.Model):
    """Comentarios por Ã¡rea/etapa del expediente"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='comentarios_areas')
    etapa = models.CharField(max_length=50, help_text="Etapa donde se hace el comentario")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    
    # Menciones
    usuarios_mencionados = models.ManyToManyField(User, blank=True, related_name='comentarios_mencionado')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Comentario de área"
        verbose_name_plural = "Comentarios de áreas"
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.username} en {self.etapa}: {self.contenido[:50]}..."
    
    def extraer_menciones(self):
        """Extrae las menciones @usuario del contenido"""
        import re
        menciones = re.findall(r'@(\w+)', self.contenido)
        return menciones
    
    def procesar_menciones(self):
        """Procesa las menciones y crea notificaciones"""
        menciones = self.extraer_menciones()
        for username in menciones:
            try:
                usuario_mencionado = User.objects.get(username=username)
                # Agregar a usuarios mencionados
                self.usuarios_mencionados.add(usuario_mencionado)
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=usuario_mencionado,
                    expediente=self.expediente,
                    tipo='mencion',
                    titulo=f'Te mencionaron en {self.expediente.numero_expediente}',
                    mensaje=f'{self.usuario.username} te mencionó en un comentario: "{self.contenido[:100]}..."',
                    enlace=f'/expedientes/{self.expediente.pk}/visualizador/',
                    generada_por=self.usuario
                )
            except User.DoesNotExist:
                continue


class RolUsuario(models.Model):
    """Modelo para roles de usuario en el sistema"""
    ROLES_CHOICES = [
        ('administrador', 'Administrador'),
        ('editor', 'Editor'),
        ('visualizador', 'Visualizador'),
    ]
    
    nombre = models.CharField(max_length=20, choices=ROLES_CHOICES, unique=True)
    descripcion = models.TextField()
    puede_aprobar_usuarios = models.BooleanField(default=False)
    puede_editar_expedientes = models.BooleanField(default=False)
    puede_ver_expedientes = models.BooleanField(default=True)
    puede_crear_expedientes = models.BooleanField(default=False)
    puede_eliminar_expedientes = models.BooleanField(default=False)
    puede_administrar_sistema = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Rol de Usuario"
        verbose_name_plural = "Roles de Usuario"
        ordering = ['nombre']
    
    def __str__(self):
        return self.get_nombre_display()


class PerfilUsuario(models.Model):
    """Modelo extendido para perfiles de usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.ForeignKey(RolUsuario, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_acceso = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.rol.get_nombre_display() if self.rol else 'Sin rol'}"


class UserSession(models.Model):
    """Modelo para rastrear sesiones de usuario"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuarios'
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.last_activity}"
        
    def update_activity(self):
        """Actualiza la última actividad del usuario"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
        
    def set_online(self, is_online):
        """Actualiza el estado de conexión del usuario"""
        self.is_online = is_online
        self.save(update_fields=['is_online', 'last_activity'])
        
    @classmethod
    def update_user_activity(cls, user, session_key):
        """Actualiza la actividad del usuario en la sesión actual"""
        try:
            session = cls.objects.get(user=user, session_key=session_key)
            session.last_activity = timezone.now()
            session.save(update_fields=['last_activity'])
            return True
        except cls.DoesNotExist:
            # Si la sesión no existe, intentamos crearla
            try:
                cls.objects.create(
                    user=user,
                    session_key=session_key,
                    last_activity=timezone.now(),
                    is_online=True
                )
                return True
            except Exception as e:
                logger.error(f'Error al crear sesión de usuario: {str(e)}')
                return False


class SolicitudRegistro(models.Model):
    """Modelo para solicitudes de registro de usuarios"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    # Información del solicitante
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email_institucional = models.EmailField(unique=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    
    # Información de la solicitud
    rol_solicitado = models.ForeignKey(RolUsuario, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    
    # Contraseña del usuario (encriptada)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    
    # Usuario que aprobó/rechazó
    resuelto_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='solicitudes_resueltas'
    )
    motivo_rechazo = models.TextField(blank=True, null=True)
    
    # Usuario creado (si fue aprobado)
    usuario_creado = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='solicitud_registro'
    )
    
    class Meta:
        verbose_name = "Solicitud de Registro"
        verbose_name_plural = "Solicitudes de Registro"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.get_estado_display()}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def aprobar(self, aprobado_por):
        """Aprueba la solicitud y crea el usuario"""
        # Usar el email como username
        username = self.email_institucional.split('@')[0]
        
        # Crear usuario con la contraseÃ±a original
        user = User.objects.create_user(
            username=username,
            email=self.email_institucional,
            password=self.password_hash,  # Usar la contraseÃ±a original
            first_name=self.nombres,
            last_name=self.apellidos,
            is_active=True
        )
        
        # Crear perfil
        perfil = PerfilUsuario.objects.create(
            usuario=user,
            rol=self.rol_solicitado,
            departamento=self.departamento,
            puesto=self.puesto,
            telefono=self.telefono,
            extension=self.extension
        )
        
        # Actualizar solicitud
        self.estado = 'aprobada'
        self.resuelto_por = aprobado_por
        self.fecha_resolucion = timezone.now()
        self.usuario_creado = user
        self.save()
        
        return user, None  # No devolver contraseÃ±a ya que el usuario ya la conoce
    
    def rechazar(self, rechazado_por, motivo):
        """Rechaza la solicitud"""
        self.estado = 'rechazada'
        self.resuelto_por = rechazado_por
        self.fecha_resolucion = timezone.now()
        self.motivo_rechazo = motivo
        self.save()




# ============================================
# MODELOS PARA AREAS PERSONALIZABLES
# ============================================

class AreaTipoExpediente(models.Model):
    """Modelo para Ã¡reas/etapas configurables por tipo y subtipo de expediente"""
    TIPO_AREA_CHOICES = [
        ('texto', 'Solo Texto'),
        ('archivo', 'Subida de Archivo'),
        ('mixto', 'Texto y Archivo'),
    ]
    
    # Configuración del área
    nombre = models.CharField(max_length=100, help_text="Nombre interno del área (sin espacios)")
    titulo = models.CharField(max_length=200, help_text="Título visible del área")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción opcional del área")
    
    # Tipo de expediente al que pertenece
    tipo_expediente = models.CharField(max_length=20, choices=Expediente.TIPO_CHOICES)
    
    # Subtipo específico (nuevo campo)
    subtipo_expediente = models.CharField(
        max_length=30, 
        blank=True, 
        null=True,
        help_text="Subtipo específico del expediente (ej: bienes, servicios, arrendamientos)"
    )
    
    # Configuración del área
    tipo_area = models.CharField(max_length=10, choices=TIPO_AREA_CHOICES, default='mixto')
    orden = models.PositiveIntegerField(default=0, help_text="Orden en que aparece en el formulario")
    obligatoria = models.BooleanField(default=True, help_text="Si el área es obligatoria para completar el expediente")
    
    # Configuración de archivos (si aplica)
    tipos_archivo_permitidos = models.TextField(
        blank=True, 
        null=True, 
        help_text="Extensiones permitidas separadas por comas (ej: pdf,docx,xlsx)"
    )
    tamano_max_archivo = models.PositiveIntegerField(
        default=10, 
        help_text="Tamaño máximo de archivo en MB"
    )
    
    # Control de estado
    activa = models.BooleanField(default=True)
    es_default = models.BooleanField(default=False, help_text="Si es un área por defecto del sistema")
    
    # Metadatos
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Área de Tipo de Expediente"
        verbose_name_plural = "Áreas de Tipos de Expediente"
        ordering = ['tipo_expediente', 'subtipo_expediente', 'orden', 'titulo']
        unique_together = [['tipo_expediente', 'subtipo_expediente', 'nombre']]
    
    def __str__(self):
        subtipo_text = f" ({self.subtipo_expediente})" if self.subtipo_expediente else ""
        return f"{self.get_tipo_expediente_display()}{subtipo_text} - {self.titulo}"
    
    def get_tipos_archivo_list(self):
        """Retorna la lista de tipos de archivo permitidos"""
        if self.tipos_archivo_permitidos:
            return [ext.strip().lower() for ext in self.tipos_archivo_permitidos.split(',')]
        return []
    
    @staticmethod
    def get_subtipos_por_tipo(tipo_expediente):
        """Retorna los subtipos disponibles para un tipo de expediente"""
        subtipos_map = {
            'licitacion': [
                ('recurso_propio', 'Recurso propio'),
                ('fondo_federal', 'Fondo federal'),
            ],
            'concurso_invitacion': [
                ('bienes', 'Bienes'),
                ('servicios', 'Servicios'),
                ('arrendamientos', 'Arrendamientos'),
            ],
            'compra_directa': [
                ('bienes', 'Bienes'),
                ('servicios', 'Servicios'),
                ('arrendamientos', 'Arrendamientos'),
            ],
            'adjudicacion_directa': [
                ('bienes', 'Bienes'),
                ('servicios', 'Servicios'),
                ('arrendamientos', 'Arrendamientos'),
            ],
            # Mantener compatibilidad con los tipos antiguos
            'giro': [
                ('ferreteria', 'Ferretería'),
                ('construccion', 'Construcción'),
                ('comercial', 'Comercial'),
                ('servicios', 'Servicios'),
                ('industrial', 'Industrial'),
                ('otros', 'Otros Giros'),
            ],
            'fuente': [
                ('propio_municipal', 'Propio Municipal'),
                ('estatal', 'Estatal'), 
                ('federal', 'Federal'),
            ],
            'tipo_adquisicion': [
                ('bienes', 'Bienes'),
                ('servicios', 'Servicios'),
                ('arrendamientos', 'Arrendamientos'),
            ],
            'monto': [
                ('compra_directa', 'Compra Directa'),
                ('concurso_invitacion', 'Concurso por Invitación'),
                ('licitacion', 'Licitación'),
                ('adjudicacion_directa', 'Adjudicación Directa'),
            ]
        }
        return subtipos_map.get(tipo_expediente, [])
        
    def etapa_completada(self, expediente):
        """
        Verifica si esta área/etapa está completada para un expediente dado.
        
        Args:
            expediente: Instancia del modelo Expediente
            
        Returns:
            bool: True si la etapa está completada, False en caso contrario
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Importar aquí para evitar importaciones circulares
        from .models import DocumentoExpediente, ValorAreaExpediente
        
        try:
            # Verificar si hay documentos para esta área
            tiene_documentos = DocumentoExpediente.objects.filter(
                expediente=expediente,
                area=self
            ).exists()
            
            # Verificar si hay un valor guardado para esta área
            valor_area = ValorAreaExpediente.objects.filter(
                expediente=expediente,
                area=self
            ).first()
            
            # Verificar contenido de texto
            tiene_texto = False
            if valor_area:
                if valor_area.valor_texto and valor_area.valor_texto.strip():
                    tiene_texto = True
                elif valor_area.valor_json:
                    # Si hay JSON, verificar que no esté vacío
                    if valor_area.valor_json:
                        tiene_texto = True
            
            # Lógica de validación basada en el tipo de área
            # IMPORTANTE: Siempre verificar el contenido real, no confiar solo en el flag 'completada'
            if self.tipo_area == 'archivo':
                # Para áreas de archivo, debe haber al menos un documento
                completada = tiene_documentos
            elif self.tipo_area == 'texto':
                # Para áreas de texto, debe haber contenido de texto
                completada = tiene_texto
            else:  # mixto
                # Para áreas mixtas, debe haber documentos Y texto
                completada = tiene_documentos and tiene_texto
            
            # Actualizar el flag 'completada' en ValorAreaExpediente si no coincide con la realidad
            if valor_area and valor_area.completada != completada:
                valor_area.completada = completada
                if completada:
                    from django.utils import timezone
                    valor_area.fecha_completada = timezone.now()
                else:
                    valor_area.fecha_completada = None
                valor_area.save(update_fields=['completada', 'fecha_completada'])
                logger.info(f"Área {self.id} del expediente {expediente.id}: flag 'completada' actualizado a {completada}")
            
            return completada
                
        except Exception as e:
            logger.error(f"Error al verificar si el área {self.id} está completada: {str(e)}", exc_info=True)
            return False


class CampoAreaPersonalizado(models.Model):
    """Modelo para campos personalizados dentro de un área"""
    TIPO_CAMPO_CHOICES = [
        ('text', 'Texto'),
        ('textarea', 'Área de Texto'),
        ('number', 'Número'),
        ('email', 'Email'),
        ('tel', 'Teléfono'),
        ('url', 'URL'),
        ('date', 'Fecha'),
        ('time', 'Hora'),
        ('datetime', 'Fecha y Hora'),
        ('select', 'Lista Desplegable'),
        ('radio', 'Botones de Radio'),
        ('checkbox', 'Casillas de Verificación'),
        ('file', 'Archivo'),
    ]
    
    area = models.ForeignKey(AreaTipoExpediente, on_delete=models.CASCADE, related_name='campos')
    nombre = models.CharField(max_length=100, help_text="Nombre interno del campo")
    etiqueta = models.CharField(max_length=200, help_text="Etiqueta visible del campo")
    tipo_campo = models.CharField(max_length=20, choices=TIPO_CAMPO_CHOICES)
    
    # Configuración del campo
    requerido = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # Para campos select, radio, checkbox
    opciones = models.JSONField(
        blank=True, 
        null=True,
        help_text='Para campos select/radio/checkbox. Formato: ["opcion1", "opcion2"]'
    )
    
    # Validaciones
    valor_minimo = models.FloatField(blank=True, null=True, help_text="Para campos numéricos")
    valor_maximo = models.FloatField(blank=True, null=True, help_text="Para campos numéricos")
    longitud_minima = models.PositiveIntegerField(blank=True, null=True, help_text="Para campos de texto")
    longitud_maxima = models.PositiveIntegerField(blank=True, null=True, help_text="Para campos de texto")
    patron_validacion = models.CharField(max_length=500, blank=True, null=True, help_text="Expresión regular para validación")
    
    # Control de estado
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Campo de Área Personalizado"
        verbose_name_plural = "Campos de Áreas Personalizados"
        ordering = ['area', 'orden', 'etiqueta']
        unique_together = [['area', 'nombre']]
    
    def __str__(self):
        return f"{self.area.titulo} - {self.etiqueta}"


class ValorAreaExpediente(models.Model):
    """Modelo para almacenar valores de texto en áreas de expedientes"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='valores_areas')
    area = models.ForeignKey(AreaTipoExpediente, on_delete=models.CASCADE)
    
    # Para campos de texto/textarea
    valor_texto = models.TextField(blank=True, null=True)
    
    # Para fechas
    valor_fecha = models.DateField(blank=True, null=True)
    valor_datetime = models.DateTimeField(blank=True, null=True)
    
    # Para números
    valor_numero = models.FloatField(blank=True, null=True)
    
    # Para valores JSON (select múltiple, checkbox, etc)
    valor_json = models.JSONField(blank=True, null=True)
    
    # Metadatos
    completada = models.BooleanField(default=False, help_text="Si el área está marcada como completada")
    fecha_completada = models.DateTimeField(blank=True, null=True)
    completada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='areas_modificadas')
    
    class Meta:
        verbose_name = "Valor de Área de Expediente"
        verbose_name_plural = "Valores de Áreas de Expedientes"
        unique_together = [['expediente', 'area']]
        ordering = ['expediente', 'area__orden']
    
    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.area.titulo}"
    
    def marcar_completada(self, usuario):
        """Marca el área como completada"""
        self.completada = True
        self.fecha_completada = timezone.now()
        self.completada_por = usuario
        self.save()


class ValorCampoPersonalizadoArea(models.Model):
    """Modelo para valores de campos personalizados en áreas"""
    valor_area = models.ForeignKey(ValorAreaExpediente, on_delete=models.CASCADE, related_name='valores_campos')
    campo = models.ForeignKey(CampoAreaPersonalizado, on_delete=models.CASCADE)
    
    # Valor del campo (se usa según el tipo)
    valor = models.TextField(blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Valor de Campo Personalizado de Área"
        verbose_name_plural = "Valores de Campos Personalizados de Áreas"
        unique_together = [['valor_area', 'campo']]
    
    def __str__(self):
        return f"{self.valor_area} - {self.campo.etiqueta}"


# ============================================
# MODELOS PARA CAMPOS PERSONALIZADOS (ACTUALIZADOS)
# ============================================

class CampoFormularioPersonalizado(models.Model):
    """Modelo para campos personalizados en formularios por tipo - LEGACY"""
    TIPO_CAMPO_CHOICES = [
        ('text', 'Texto'),
        ('textarea', 'Área de texto'),
        ('select', 'Selector'),
        ('number', 'Número'),
        ('date', 'Fecha'),
        ('email', 'Email'),
        ('file', 'Archivo'),
        ('checkbox', 'Casilla de verificación'),
    ]
    
    nombre = models.CharField(max_length=100)
    etiqueta = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CAMPO_CHOICES)
    tipo_expediente = models.CharField(max_length=20, choices=Expediente.TIPO_CHOICES)
    
    # Configuración del campo
    requerido = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)
    opciones = models.JSONField(blank=True, null=True)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # Etapa asociada (agregado en migración 0015)
    etapa = models.CharField(
        max_length=30,
        choices=Expediente.ESTADO_CHOICES,
        default='inicio'
    )
    
    # Control de estado
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Campo de Formulario Personalizado"
        verbose_name_plural = "Campos de Formulario Personalizados"
        ordering = ['tipo_expediente', 'etapa', 'orden', 'nombre']
        unique_together = [['nombre', 'tipo_expediente', 'etapa']]
    
    def __str__(self):
        return f"{self.get_tipo_expediente_display()} - {self.get_etapa_display()} - {self.etiqueta}"


class ValorCampoPersonalizado(models.Model):
    """Modelo para valores de campos personalizados - LEGACY"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='valores_campos_personalizados')
    campo = models.ForeignKey(CampoFormularioPersonalizado, on_delete=models.CASCADE)
    valor = models.TextField()
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Valor de Campo Personalizado"
        verbose_name_plural = "Valores de Campos Personalizados"
        unique_together = [['expediente', 'campo']]
    
    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.campo.etiqueta}"


# ============================================
# MODELOS PARA COLABORACIÃ“N EN EXPEDIENTES
# ============================================

class MensajeExpediente(models.Model):
    """Modelo para mensajes en expedientes"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='mensajes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    etiquetas = models.JSONField(blank=True, null=True, help_text="Lista de usuarios etiquetados con @")
    fecha_envio = models.DateTimeField(auto_now_add=True)
    editado = models.BooleanField(default=False)
    fecha_edicion = models.DateTimeField(blank=True, null=True)
    leido = models.BooleanField(default=False, help_text="Indica si el mensaje ha sido leÃ­do")
    
    class Meta:
        verbose_name = "Mensaje de Expediente"
        verbose_name_plural = "Mensajes de Expedientes"
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.usuario.username} - {self.fecha_envio.strftime('%d/%m/%Y %H:%M')}"
    
    def get_etiquetas_usuarios(self):
        """Obtiene los usuarios etiquetados"""
        if not self.etiquetas:
            return []
        return User.objects.filter(username__in=self.etiquetas)



class Chat(models.Model):
    """Modelo para chats entre usuarios"""
    TIPO_CHOICES = [
        ('individual', 'Individual'),
        ('grupo', 'Grupo'),
        ('departamento', 'Departamento'),
    ]
    
    nombre = models.CharField(max_length=200, blank=True, null=True, help_text="Nombre del chat (para grupos)")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='individual')
    participantes = models.ManyToManyField(User, related_name='chats')
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ['-ultima_actividad']
    
    def __str__(self):
        if self.tipo == 'individual':
            participantes = list(self.participantes.exclude(id=self.creado_por.id))
            if participantes:
                return f"Chat con {participantes[0].get_full_name() or participantes[0].username}"
            return f"Chat de {self.creado_por.username}"
        return self.nombre or f"Chat {self.id}"
    
    def get_ultimo_mensaje(self):
        """Obtiene el último mensaje del chat"""
        return self.mensajes.order_by('-fecha_envio').first()
    
    def get_mensajes_no_leidos(self, usuario):
        """Obtiene el número de mensajes no leídos para un usuario"""
        return self.mensajes.filter(
            fecha_envio__gt=usuario.last_login or usuario.date_joined,
            remitente__in=self.participantes.exclude(id=usuario.id)
        ).count()


class Mensaje(models.Model):
    """Modelo para mensajes en chats"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensajes')
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    contenido = models.TextField()
    tipo = models.CharField(max_length=20, choices=[
        ('texto', 'Texto'),
        ('archivo', 'Archivo'),
        ('icono', 'Icono'),
        ('sistema', 'Sistema'),
    ], default='texto')
    archivo_adjunto = models.ForeignKey('ArchivoAdjunto', on_delete=models.SET_NULL, blank=True, null=True)
    icono = models.CharField(max_length=50, blank=True, null=True, help_text="CÃ³digo del icono Bootstrap")
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    editado = models.BooleanField(default=False)
    fecha_edicion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['fecha_envio']
    
    def __str__(self):
        return f"{self.remitente.username}: {self.contenido[:50]}"
    
    def marcar_como_leido(self, usuario):
        """Marca el mensaje como leído por un usuario"""
        if not self.leido and self.remitente != usuario:
            self.leido = True
            self.fecha_lectura = timezone.now()
            self.save()
    
    def es_archivo(self):
        """Verifica si el mensaje contiene un archivo"""
        return self.tipo == 'archivo' and self.archivo_adjunto
    
    def es_icono(self):
        """Verifica si el mensaje contiene un icono"""
        return self.tipo == 'icono' and self.icono


class ArchivoAdjunto(models.Model):
    """Modelo para archivos adjuntos en mensajes"""
    nombre_original = models.CharField(max_length=255)
    nombre_archivo = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=100)
    tamano = models.PositiveIntegerField(help_text="Tamaño en bytes")
    ruta = models.CharField(max_length=500)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return self.nombre_original
    
    def get_tamano_formateado(self):
        """Retorna el tamaño del archivo formateado"""
        tamano = self.tamano
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if tamano < 1024.0 or unidad == 'GB':
                return f"{tamano:.1f} {unidad}"
            tamano /= 1024.0
        return f"{tamano:.1f} TB"
    
    def es_imagen(self):
        """Verifica si el archivo es una imagen"""
        return self.tipo_mime.startswith('image/')
    
    def es_documento(self):
        """Verifica si el archivo es un documento"""
        doc_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain'
        ]
        return self.tipo_mime in doc_types

# Fin de la clase ArchivoAdjunto


class SolicitudEscaneo(models.Model):
    """
    Modelo para solicitudes de escaneo remoto.
    Permite que cualquier dispositivo solicite un escaneo que será
    procesado por el servicio de escaneo local.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Información de la solicitud
    expediente = models.ForeignKey(
        'Expediente', 
        on_delete=models.CASCADE, 
        related_name='solicitudes_escaneo'
    )
    area_id = models.IntegerField(help_text="ID del área donde se guardará el documento")
    nombre_documento = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    duplex = models.BooleanField(default=False, help_text="Escanear por ambos lados")
    
    # Estado de la solicitud
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    mensaje_error = models.TextField(blank=True, null=True)
    
    # Usuario que solicitó el escaneo
    solicitado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='solicitudes_escaneo'
    )
    
    # Timestamps
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)
    fecha_completado = models.DateTimeField(blank=True, null=True)
    
    # Documento resultante (si se completó exitosamente)
    documento_creado = models.ForeignKey(
        'DocumentoExpediente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitud_escaneo'
    )
    
    class Meta:
        verbose_name = "Solicitud de Escaneo"
        verbose_name_plural = "Solicitudes de Escaneo"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Escaneo: {self.nombre_documento} - {self.estado}"
    
    def marcar_procesando(self):
        """Marca la solicitud como en proceso"""
        self.estado = 'procesando'
        self.fecha_procesamiento = timezone.now()
        self.save()
    
    def marcar_completado(self, documento=None):
        """Marca la solicitud como completada"""
        self.estado = 'completado'
        self.fecha_completado = timezone.now()
        if documento:
            self.documento_creado = documento
        self.save()
    
    def marcar_error(self, mensaje):
        """Marca la solicitud con error"""
        self.estado = 'error'
        self.mensaje_error = mensaje
        self.fecha_completado = timezone.now()
        self.save()
    
    def cancelar(self):
        """Cancela la solicitud"""
        if self.estado == 'pendiente':
            self.estado = 'cancelado'
            self.save()
            return True
        return False

