from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TipoDocumento, Departamento, Documento, HistorialDocumento, ConfiguracionSistema


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['fecha_creacion']


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['fecha_creacion']


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento', 'titulo', 'tipo_documento', 'departamento',
        'estado', 'prioridad', 'fecha_documento', 'creado_por', 'archivo_link'
    ]
    list_filter = [
        'estado', 'prioridad', 'tipo_documento', 'departamento',
        'confidencial', 'fecha_creacion', 'fecha_documento'
    ]
    search_fields = [
        'numero_documento', 'titulo', 'descripcion',
        'palabras_clave', 'creado_por__username'
    ]
    ordering = ['-fecha_creacion']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_documento', 'titulo', 'descripcion')
        }),
        ('Clasificación', {
            'fields': ('tipo_documento', 'departamento', 'prioridad', 'confidencial')
        }),
        ('Estado', {
            'fields': ('estado', 'observaciones')
        }),
        ('Archivo Digital', {
            'fields': ('archivo_digital', 'archivo_original', 'tamaño_archivo')
        }),
        ('Fechas', {
            'fields': ('fecha_documento', 'fecha_vencimiento', 'fecha_digitalizacion')
        }),
        ('Usuarios', {
            'fields': ('creado_por', 'digitalizado_por', 'verificado_por')
        }),
        ('Metadata', {
            'fields': ('palabras_clave',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'fecha_creacion', 'fecha_actualizacion', 'tamaño_archivo'
    ]
    
    filter_horizontal = []
    
    def archivo_link(self, obj):
        if obj.archivo_digital:
            return format_html(
                '<a href="{}" target="_blank">Ver archivo</a>',
                obj.archivo_digital.url
            )
        return "Sin archivo"
    archivo_link.short_description = "Archivo"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una creación nueva
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'tipo_documento', 'departamento', 'creado_por',
            'digitalizado_por', 'verificado_por'
        )


class HistorialDocumentoInline(admin.TabularInline):
    model = HistorialDocumento
    extra = 0
    readonly_fields = ['fecha', 'usuario', 'accion', 'descripcion', 'estado_anterior', 'estado_nuevo']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(HistorialDocumento)
class HistorialDocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'documento', 'usuario', 'accion', 'fecha',
        'estado_anterior', 'estado_nuevo'
    ]
    list_filter = ['accion', 'fecha', 'estado_anterior', 'estado_nuevo']
    search_fields = [
        'documento__numero_documento', 'documento__titulo',
        'usuario__username', 'accion', 'descripcion'
    ]
    ordering = ['-fecha']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        (None, {
            'fields': ('documento', 'usuario', 'accion', 'descripcion')
        }),
        ('Estados', {
            'fields': ('estado_anterior', 'estado_nuevo')
        }),
        ('Información del Sistema', {
            'fields': ('fecha',),
        }),
    )
    
    readonly_fields = ['fecha']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('documento', 'usuario')


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['clave', 'valor_truncado', 'activo', 'fecha_actualizacion']
    list_filter = ['activo', 'fecha_creacion', 'fecha_actualizacion']
    search_fields = ['clave', 'valor', 'descripcion']
    ordering = ['clave']
    
    fieldsets = (
        (None, {
            'fields': ('clave', 'valor', 'descripcion', 'activo')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def valor_truncado(self, obj):
        if len(obj.valor) > 50:
            return obj.valor[:50] + "..."
        return obj.valor
    valor_truncado.short_description = "Valor"


# Personalización del admin site
admin.site.site_header = "Sistema de Digitalización - Administración"
admin.site.site_title = "Sistema de Digitalización"
admin.site.index_title = "Panel de Administración"