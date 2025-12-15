from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TipoDocumento, Departamento, Expediente, EtapaExpediente, 
    DocumentoExpediente, ComentarioEtapa, HistorialExpediente,
    ConfiguracionSistema, Documento, HistorialDocumento, NotaExpediente,
    Notificacion, ComentarioArea, RolUsuario, PerfilUsuario, SolicitudRegistro,
    # Nuevos modelos para áreas personalizables
    AreaTipoExpediente, CampoAreaPersonalizado, ValorAreaExpediente, 
    ValorCampoPersonalizadoArea, CampoFormularioPersonalizado, ValorCampoPersonalizado,
    # Modelos de colaboración en expedientes
    MensajeExpediente,
    # Modelos de mensajería
    Chat, Mensaje, ArchivoAdjunto
)


# ============================================
# ADMIN PARA AREAS PERSONALIZABLES
# ============================================

class CampoAreaPersonalizadoInline(admin.TabularInline):
    model = CampoAreaPersonalizado
    extra = 0
    fields = ['nombre', 'etiqueta', 'tipo_campo', 'requerido', 'orden', 'activo']
    ordering = ['orden', 'etiqueta']


@admin.register(AreaTipoExpediente)
class AreaTipoExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'tipo_expediente', 'tipo_area', 'orden', 
        'obligatoria', 'activa', 'es_default', 'fecha_creacion'
    ]
    list_filter = ['tipo_expediente', 'tipo_area', 'obligatoria', 'activa', 'es_default']
    search_fields = ['titulo', 'nombre', 'descripcion']
    ordering = ['tipo_expediente', 'orden']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'titulo', 'descripcion', 'tipo_expediente')
        }),
        ('Configuración del Área', {
            'fields': ('tipo_area', 'orden', 'obligatoria', 'activa')
        }),
        ('Configuración de Archivos', {
            'fields': ('tipos_archivo_permitidos', 'tamaño_max_archivo'),
            'classes': ('collapse',)
        }),
        ('Control del Sistema', {
            'fields': ('es_default', 'creada_por'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [CampoAreaPersonalizadoInline]
    
    def get_readonly_fields(self, request, obj=None):
        readonly = ['creada_por', 'fecha_creacion', 'fecha_modificacion']
        if obj and obj.es_default:
            # Los campos por defecto no se pueden editar tanto
            readonly.extend(['nombre', 'tipo_expediente'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.creada_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Los no-superusers solo ven las áreas no-default y las suyas
            qs = qs.filter(
                models.Q(es_default=False) | 
                models.Q(creada_por=request.user)
            )
        return qs


@admin.register(CampoAreaPersonalizado)
class CampoAreaPersonalizadoAdmin(admin.ModelAdmin):
    list_display = [
        'etiqueta', 'area', 'tipo_campo', 'requerido', 
        'orden', 'activo', 'fecha_creacion'
    ]
    list_filter = ['tipo_campo', 'requerido', 'activo', 'area__tipo_expediente']
    search_fields = ['etiqueta', 'nombre', 'area__titulo']
    ordering = ['area__tipo_expediente', 'area__orden', 'orden']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('area', 'nombre', 'etiqueta', 'tipo_campo', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('requerido', 'orden', 'activo', 'placeholder')
        }),
        ('Opciones (para select/radio/checkbox)', {
            'fields': ('opciones',),
            'classes': ('collapse',)
        }),
        ('Validaciones', {
            'fields': (
                'valor_minimo', 'valor_maximo', 
                'longitud_minima', 'longitud_maxima', 
                'patron_validacion'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(ValorAreaExpediente)
class ValorAreaExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'expediente', 'area', 'completada', 'fecha_completada', 
        'completada_por', 'fecha_modificacion'
    ]
    list_filter = ['completada', 'area__tipo_expediente', 'area__titulo']
    search_fields = ['expediente__numero_expediente', 'expediente__titulo', 'area__titulo']
    ordering = ['-fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('expediente', 'area')
        }),
        ('Valores', {
            'fields': ('valor_texto', 'valor_fecha', 'valor_datetime', 'valor_numero', 'valor_json')
        }),
        ('Control de Completitud', {
            'fields': ('completada', 'fecha_completada', 'completada_por'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'fecha_completada']


# ============================================
# ADMIN EXISTENTES ACTUALIZADOS
# ============================================

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'fecha_creacion']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'fecha_creacion']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    

class EtapaExpedienteInline(admin.TabularInline):
    model = EtapaExpediente
    extra = 0
    readonly_fields = ['fecha_completada']


class DocumentoExpedienteInline(admin.TabularInline):
    model = DocumentoExpediente
    extra = 0
    readonly_fields = ['fecha_subida', 'tamano_archivo', 'tipo_archivo']


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'numero_expediente', 'titulo', 'tipo_expediente', 
        'estado_actual', 'departamento', 'fecha_expediente', 
        'creado_por', 'fecha_creacion'
    ]
    list_filter = [
        'tipo_expediente', 'estado_actual', 'departamento',
        'fecha_expediente', 'confidencial'
    ]
    search_fields = [
        'numero_expediente', 'titulo', 'descripcion', 
        'palabras_clave', 'numero_sima'
    ]
    ordering = ['-fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_expediente', 'titulo', 'descripcion', 
                'tipo_expediente', 'departamento'
            )
        }),
        ('Campos Específicos', {
            'fields': (
                'giro', 'fuente_financiamiento', 
                'tipo_adquisicion', 'modalidad_monto'
            ),
            'classes': ('collapse',)
        }),
        ('Estado y Fechas', {
            'fields': (
                'estado_actual', 'fecha_expediente', 'fecha_vencimiento'
            )
        }),
        ('SIMA', {
            'fields': ('numero_sima',),
            'classes': ('collapse',)
        }),
        ('Información de Rechazo', {
            'fields': ('motivo_rechazo', 'fecha_rechazo', 'rechazado_por'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'palabras_clave', 'observaciones', 'confidencial',
                'creado_por', 'fecha_creacion', 'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'fecha_rechazo']
    inlines = [EtapaExpedienteInline, DocumentoExpedienteInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    

@admin.register(EtapaExpediente)
class EtapaExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'expediente', 'nombre_etapa', 'completada', 
        'fecha_completada', 'completada_por'
    ]
    list_filter = ['completada', 'nombre_etapa']
    search_fields = ['expediente__numero_expediente', 'expediente__titulo']
    ordering = ['expediente', 'nombre_etapa']


@admin.register(DocumentoExpediente)
class DocumentoExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'expediente', 'nombre_documento', 'etapa', 
        'validado', 'subido_por', 'fecha_subida'
    ]
    list_filter = ['etapa', 'validado', 'fecha_subida']
    search_fields = [
        'expediente__numero_expediente', 'nombre_documento', 'descripcion'
    ]
    ordering = ['-fecha_subida']
    
    readonly_fields = ['fecha_subida', 'tamano_archivo', 'tipo_archivo']


@admin.register(RolUsuario)
class RolUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'get_nombre_display', 'puede_crear_expedientes', 
        'puede_editar_expedientes', 'puede_administrar_sistema'
    ]
    list_filter = [
        'puede_aprobar_usuarios', 'puede_crear_expedientes',
        'puede_editar_expedientes', 'puede_administrar_sistema'
    ]


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'rol', 'departamento', 'puesto', 
        'activo', 'fecha_registro'
    ]
    list_filter = ['rol', 'departamento', 'activo']
    search_fields = [
        'usuario__username', 'usuario__first_name', 
        'usuario__last_name', 'puesto'
    ]


@admin.register(SolicitudRegistro)
class SolicitudRegistroAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_completo', 'email_institucional', 'rol_solicitado',
        'estado', 'fecha_solicitud', 'resuelto_por'
    ]
    list_filter = ['estado', 'rol_solicitado', 'fecha_solicitud']
    search_fields = [
        'nombres', 'apellidos', 'email_institucional'
    ]
    ordering = ['-fecha_solicitud']


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['clave', 'valor', 'activo', 'fecha_actualizacion']
    list_filter = ['activo']
    search_fields = ['clave', 'valor', 'descripcion']
    ordering = ['clave']


# ============================================
# ADMIN PARA CAMPOS PERSONALIZADOS LEGACY
# ============================================

@admin.register(CampoFormularioPersonalizado)
class CampoFormularioPersonalizadoAdmin(admin.ModelAdmin):
    list_display = [
        'etiqueta', 'tipo_expediente', 'etapa', 'tipo', 
        'requerido', 'orden', 'activo'
    ]
    list_filter = ['tipo_expediente', 'etapa', 'tipo', 'requerido', 'activo']
    search_fields = ['nombre', 'etiqueta', 'descripcion']
    ordering = ['tipo_expediente', 'etapa', 'orden']


@admin.register(ValorCampoPersonalizado)
class ValorCampoPersonalizadoAdmin(admin.ModelAdmin):
    list_display = [
        'expediente', 'campo', 'valor', 'fecha_creacion'
    ]
    list_filter = ['campo__tipo_expediente', 'campo__etapa']
    search_fields = [
        'expediente__numero_expediente', 'campo__etiqueta', 'valor'
    ]


# ============================================
# ADMIN PARA NOTIFICACIONES
# ============================================

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'tipo', 'titulo', 'leida', 
        'fecha_creacion', 'generada_por'
    ]
    list_filter = ['tipo', 'leida', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje', 'usuario__username']
    ordering = ['-fecha_creacion']


# ============================================
# REGISTROS SIMPLES
# ============================================

admin.site.register(ComentarioEtapa)
admin.site.register(HistorialExpediente)
admin.site.register(Documento)
admin.site.register(HistorialDocumento)
admin.site.register(NotaExpediente)
admin.site.register(ComentarioArea)
admin.site.register(ValorCampoPersonalizadoArea)

# ============================================
# ADMIN PARA COLABORACIÓN EN EXPEDIENTES
# ============================================

@admin.register(MensajeExpediente)
class MensajeExpedienteAdmin(admin.ModelAdmin):
    list_display = [
        'expediente', 'usuario', 'contenido', 
        'fecha_envio', 'editado'
    ]
    list_filter = ['fecha_envio', 'editado']
    search_fields = [
        'expediente__numero_expediente', 'usuario__username', 'contenido'
    ]
    ordering = ['-fecha_envio']
    

# ============================================
# ADMIN PARA MENSAJERÍA
# ============================================

class MensajeInline(admin.TabularInline):
    model = Mensaje
    extra = 0
    fields = ['remitente', 'contenido', 'tipo', 'fecha_envio', 'leido']
    readonly_fields = ['fecha_envio']
    ordering = ['-fecha_envio']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tipo', 'nombre', 'creado_por', 
        'fecha_creacion', 'ultima_actividad', 'activo'
    ]
    list_filter = ['tipo', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'creado_por__username', 'participantes__username']
    ordering = ['-ultima_actividad']
    readonly_fields = ['fecha_creacion', 'ultima_actividad']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo', 'nombre', 'creado_por', 'activo')
        }),
        ('Participantes', {
            'fields': ('participantes',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'ultima_actividad'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [MensajeInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('participantes', 'creado_por')


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'chat', 'remitente', 'tipo', 'contenido', 
        'fecha_envio', 'leido', 'editado'
    ]
    list_filter = ['tipo', 'leido', 'editado', 'fecha_envio']
    search_fields = [
        'contenido', 'remitente__username', 'chat__id'
    ]
    ordering = ['-fecha_envio']
    readonly_fields = ['fecha_envio', 'fecha_lectura', 'fecha_edicion']
    
    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('chat', 'remitente', 'contenido', 'tipo')
        }),
        ('Archivo Adjunto', {
            'fields': ('archivo_adjunto',),
            'classes': ('collapse',)
        }),
        ('Icono', {
            'fields': ('icono',),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('leido', 'editado')
        }),
        ('Fechas', {
            'fields': ('fecha_envio', 'fecha_lectura', 'fecha_edicion'),
            'classes': ('collapse',)
        })
    )


@admin.register(ArchivoAdjunto)
class ArchivoAdjuntoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_original', 'usuario', 'tipo_mime', 
        'tamano', 'fecha_subida'
    ]
    list_filter = ['tipo_mime', 'fecha_subida']
    search_fields = ['nombre_original', 'usuario__username']
    ordering = ['-fecha_subida']
    readonly_fields = ['fecha_subida']
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('nombre_original', 'nombre_archivo', 'tipo_mime', 'tamano')
        }),
        ('Ubicación', {
            'fields': ('ruta',)
        }),
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_subida',),
            'classes': ('collapse',)
        })
    )
    
    def get_tamano_formateado(self, obj):
        return obj.get_tamano_formateado()
    get_tamano_formateado.short_description = 'Tamaño'


# ============================================
# CONFIGURACIÓN DEL ADMIN SITE
# ============================================

admin.site.site_header = "Sistema de Digitalización - Administración"
admin.site.site_title = "Admin Sistema Digitalización"
admin.site.index_title = "Panel de Administración"