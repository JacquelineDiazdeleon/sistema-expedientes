from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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
    """Función para definir la ruta de subida de archivos"""
    ext = filename.split('.')[-1]
    fecha = timezone.now()
    # Get the expediente instance safely
    expediente = getattr(instance, 'expediente', None)
    if not expediente:
        raise ValueError("El documento debe estar asociado a un expediente")
        
    # Get the numero_expediente safely
    numero_expediente = getattr(expediente, 'numero_expediente', 'sin_numero')
    
    # Create a safe filename
    safe_numero = str(numero_expediente).replace(' ', '_').replace('/', '-')
    filename = f"{safe_numero}_{fecha.strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    return os.path.join('expedientes', str(fecha.year), str(fecha.month), filename)


class Expediente(models.Model):
    """Modelo principal para los expedientes"""
    TIPO_CHOICES = [
        ('giro', 'Por Giro'),
        ('fuente', 'Por Fuente de Financiamiento'),
        ('tipo_adquisicion', 'Por Tipo de Adquisición'),
        ('monto', 'Por Monto'),
    ]

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
    ]

    # Información básica
    numero_expediente = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
    # Tipo de expediente
    tipo_expediente = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Campos específicos según el tipo
    giro = models.CharField(max_length=100, blank=True, null=True, help_text="Para expedientes por giro")
    fuente_financiamiento = models.CharField(max_length=20, choices=FUENTE_CHOICES, blank=True, null=True)
    tipo_adquisicion = models.CharField(max_length=20, choices=TIPO_ADQUISICION_CHOICES, blank=True, null=True)
    modalidad_monto = models.CharField(max_length=30, choices=MODALIDAD_MONTO_CHOICES, blank=True, null=True)
    
    # Estado actual del expediente
    estado_actual = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='inicio')
    
    # Número SIMA
    numero_sima = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Número o código SIMA asignado al expediente",
        verbose_name="Número SIMA"
    )
    
    # Información adicional
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    fecha_expediente = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    
    # Usuarios
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expedientes_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Metadata
    palabras_clave = models.TextField(blank=True, null=True, help_text="Palabras clave separadas por comas")
    observaciones = models.TextField(blank=True, null=True)
    confidencial = models.BooleanField(default=False)
    
    # Información de rechazo
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

    def __str__(self):
        return f"{self.numero_expediente} - {self.titulo}" if self.numero_expediente else f"{self.id} - {self.titulo}"

    @property
    def numero(self):
        """Propiedad para mantener compatibilidad con código existente que usa 'numero'"""
        return self.numero_expediente

    def get_palabras_clave_list(self):
        """Retorna las palabras clave como lista"""
        if self.palabras_clave:
            return [palabra.strip() for palabra in self.palabras_clave.split(',')]
        return []

    def get_progreso(self):
        """Calcula el progreso del expediente basado en las etapas completadas"""
        # Orden correcto de las etapas según el esquema solicitado
        orden_etapas = [
            'inicio',
            'solicitud_area',
            'cotizacion',
            'requisicion_sima',
            'suficiencia_presupuestal',
            'aprobacion_director',
            'aprobacion_secretario',
            'notificacion_compras',
            'valoracion_tipo',
            'adjudicacion',
            'formalizacion',
            'contrato',
            'recepcion_bien',
            'recepcion_facturacion',
            'generacion_evidencia',
            'envio_compras',
            'pago',
        ]
        
        # Si está completado, retornar 100%
        if self.estado_actual == 'completado':
            return 100
        
        # Contar etapas completadas
        etapas_completadas = self.etapas.filter(completada=True).count()
        etapas_totales = len(orden_etapas)
        
        # Calcular progreso basado en etapas completadas
        if etapas_totales > 0:
            progreso = int((etapas_completadas / etapas_totales) * 100)
            return min(progreso, 100)  # Asegurar que no supere 100%
        
        return 0
    
    def rechazar_expediente(self, usuario, motivo):
        """Rechaza el expediente con motivo y usuario"""
        from django.utils import timezone
        
        now = timezone.now()
        self.estado_actual = 'rechazado'
        self.motivo_rechazo = motivo
        self.fecha_rechazo = now
        self.fecha_actualizacion = now
        self.rechazado_por = usuario
        self.save()
        
        # Crear entrada en el historial
        HistorialExpediente.objects.create(
            expediente=self,
            usuario=usuario,
            accion='rechazado',
            descripcion=f'Expediente rechazado. Motivo: {motivo}'
        )
    
    def es_rechazado(self):
        """Retorna True si el expediente está rechazado"""
        return self.estado_actual == 'rechazado'
        
    def save(self, *args, **kwargs):
        """Sobrescribir el método save para actualizar automáticamente la fecha de actualización"""
        from django.utils import timezone
        from django.core.cache import cache
        
        # Si el objeto ya existe (tiene un ID)
        if self.id:
            # Actualizar la fecha de actualización
            self.fecha_actualizacion = timezone.now()
            # Limpiar la caché de última actualización
            cache_key = f'expediente_{self.id}_ultima_actualizacion'
            cache.delete(cache_key)
            
        super().save(*args, **kwargs)

    def get_ultima_actualizacion(self, use_cache=True):
        """
        Obtiene la fecha de la última modificación del expediente.
        
        Returns:
            datetime: Fecha y hora de la última actualización (documento más reciente, comentario o fecha_actualizacion)
        """
        from django.utils import timezone
        from django.db.models import Max
        
        # Obtener la fecha del documento más reciente
        ultimo_documento = self.documentos.aggregate(
            ultima_fecha=Max('fecha_subida')
        )['ultima_fecha']
        
        # Obtener la fecha del comentario más reciente
        ultimo_comentario = self.comentarios.aggregate(
            ultima_fecha=Max('fecha_creacion')
        )['ultima_fecha']
        
        # Obtener la fecha de la última actualización del historial
        ultimo_historial = self.historial.aggregate(
            ultima_fecha=Max('fecha')
        )['ultima_fecha']
        
        # Encontrar la fecha más reciente entre todas las fuentes
        fechas = [
            self.fecha_creacion,
            self.fecha_actualizacion,
            ultimo_documento,
            ultimo_comentario,
            ultimo_historial
        ]
        
        # Filtrar fechas None y devolver la más reciente
        fechas_validas = [f for f in fechas if f is not None]
        return max(fechas_validas) if fechas_validas else timezone.now()
        
        # Obtener la fecha del comentario más reciente
        try:
            ultimo_comentario = self.comentarios.order_by('-fecha_comentario').first()
            if ultimo_comentario:
                fechas.append(('comentario', ultimo_comentario.fecha_comentario))
                logger.info(f'[DEBUG] Último comentario: {ultimo_comentario.fecha_comentario}')
        except Exception as e:
            logger.error(f'Error obteniendo último comentario: {str(e)}')
        
        # Obtener la fecha de la última etapa completada
        try:
            ultima_etapa = self.etapas.filter(completada=True).order_by('-fecha_completada').first()
            if ultima_etapa and ultima_etapa.fecha_completada:
                fechas.append(('etapa', ultima_etapa.fecha_completada))
                logger.info(f'[DEBUG] Última etapa completada: {ultima_etapa.fecha_completada} - {ultima_etapa.nombre_etapa}')
        except Exception as e:
            logger.error(f'Error obteniendo última etapa: {str(e)}')
        
        # Obtener la fecha de la última entrada en el historial
        try:
            ultimo_historial = self.historial.order_by('-fecha').first()
            if ultimo_historial:
                fechas.append(('historial', ultimo_historial.fecha))
                logger.info(f'[DEBUG] Último historial: {ultimo_historial.fecha} - {ultimo_historial.accion}')
        except Exception as e:
            logger.error(f'Error obteniendo último historial: {str(e)}')
        
        # Filtrar fechas None y obtener la más reciente con su fuente
        fechas_validas = [(fuente, fecha) for fuente, fecha in fechas if fecha is not None]
        logger.info(f'[DEBUG] Fechas válidas encontradas para expediente {self.id}:')
        for fuente, fecha in fechas_validas:
            logger.info(f'  - {fuente}: {fecha}')
        
        if not fechas_validas:
            logger.warning(f'No se encontraron fechas válidas para el expediente {self.id}')
            return timezone.now()
            
        # Ordenar por fecha descendente
        fechas_validas.sort(key=lambda x: x[1], reverse=True)
        fuente_mas_reciente, fecha_mas_reciente = fechas_validas[0]
        
        logger.info(f'[DEBUG] Fecha más reciente: {fecha_mas_reciente} (fuente: {fuente_mas_reciente})')
        
        # Guardar en caché por 5 minutos
        if use_cache and fecha_mas_reciente:
            cache.set(cache_key, fecha_mas_reciente, 300)  # 5 minutos de caché
            logger.info(f'[CACHE] Guardando en caché para expediente {self.id}: {fecha_mas_reciente}')
        
        return fecha_mas_reciente


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
    tamaño_archivo = models.PositiveIntegerField(blank=True, null=True)
    tipo_archivo = models.CharField(max_length=50, blank=True, null=True)
    
    # Usuario y fechas
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    # Validación
    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_validados')
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Documento de Expediente"
        verbose_name_plural = "Documentos de Expedientes"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.expediente.numero_expediente} - {self.nombre_documento}"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Guardar el documento
        if self.archivo and not self.tamaño_archivo:
            self.tamaño_archivo = self.archivo.size
            self.tipo_archivo = self.archivo.name.split('.')[-1].lower()
        
        # Guardar el documento primero
        super().save(*args, **kwargs)
        
        # Actualizar la fecha de actualización del expediente
        now = timezone.now()
        # Forzar la actualización de la fecha de actualización del expediente
        Expediente.objects.filter(id=self.expediente.id).update(fecha_actualizacion=now)
        
        # Actualizar el estado del expediente si es necesario
        if self.estado_etapa == 'completado' and self.expediente.estado_actual != self.estado_etapa:
            Expediente.objects.filter(id=self.expediente.id).update(
                estado_actual=self.estado_etapa,
                fecha_actualizacion=now
            )

    @property
    def tamaño_archivo_formateado(self):
        """Retorna el tamaño del archivo en formato legible"""
        if not self.tamaño_archivo:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamaño_archivo < 1024.0:
                return f"{self.tamaño_archivo:.1f} {unit}"
            self.tamaño_archivo /= 1024.0
        return f"{self.tamaño_archivo:.1f} TB"


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


class RequisitoEtapa(models.Model):
    """Modelo para definir los requisitos de cada etapa según el tipo de expediente"""
    tipo_expediente = models.CharField(max_length=20, choices=Expediente.TIPO_CHOICES)
    subtipo = models.CharField(max_length=50, blank=True, null=True)  # Para modalidades específicas
    etapa = models.CharField(max_length=30, choices=Expediente.ESTADO_CHOICES)
    nombre_requisito = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    obligatorio = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Requisito de Etapa"
        verbose_name_plural = "Requisitos de Etapas"
        ordering = ['tipo_expediente', 'etapa', 'orden']
        unique_together = ['tipo_expediente', 'subtipo', 'etapa', 'nombre_requisito']

    def __str__(self):
        return f"{self.get_tipo_expediente_display()} - {self.get_etapa_display()} - {self.nombre_requisito}"


class HistorialExpediente(models.Model):
    """Modelo para el historial de cambios de expedientes"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
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
        return f"{self.expediente.numero_expediente} - {self.accion} - {self.fecha}"


class ConfiguracionSistema(models.Model):
    """Modelo para configuraciones del sistema"""
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        ordering = ['clave']

    def __str__(self):
        return f"{self.clave}: {self.valor[:50]}"


# Mantener compatibilidad con el modelo anterior
class Documento(models.Model):
    """Modelo de compatibilidad - se migrará a Expediente"""
    
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
    
    # Clasificación
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    
    # Información del expediente
    giro = models.CharField(max_length=100, blank=True, null=True)
    fuente_financiamiento = models.CharField(max_length=20, blank=True, null=True)
    tipo_adquisicion = models.CharField(max_length=20, blank=True, null=True)
    modalidad_monto = models.CharField(max_length=30, blank=True, null=True)
    
    # Estado y prioridad
    estado = models.CharField(max_length=20, default='pendiente')
    prioridad = models.CharField(max_length=10, default='media')
    
    # Archivo digitalizado
    archivo_digital = models.FileField(upload_to='documentos/', blank=True, null=True)
    tamaño_archivo = models.PositiveIntegerField(blank=True, null=True)
    
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
        help_text="Documento específico al que se adjunta la nota (opcional)"
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
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    enlace = models.CharField(max_length=500, blank=True, null=True, help_text="URL de destino")
    
    # Usuario que generó la notificación
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
    """Comentarios por área/etapa del expediente"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='comentarios_areas')
    etapa = models.CharField(max_length=50, help_text="Etapa donde se hace el comentario")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    
    # Menciones
    usuarios_mencionados = models.ManyToManyField(User, blank=True, related_name='comentarios_mencionado')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Comentario de Área"
        verbose_name_plural = "Comentarios de Áreas"
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