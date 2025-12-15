from django.urls import path, include
from django.views.generic import RedirectView
from . import views, views_admin, views_auth, views_documentos, views_expedientes
from . import views_auth
from . import views_admin
from . import views_areas
from . import views_documentos
from . import views_escaneo

app_name = 'digitalizacion'




# URLs principales de la aplicación
urlpatterns = [
    # Página principal y dashboard
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Autenticación y perfil
    path('login/', views_auth.login_view, name='login'),
    path('registro/', views_auth.register_view, name='register'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('cambiar-password/', views_auth.cambiar_password, name='cambiar_password'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    # Términos y condiciones y política de privacidad
    path('terminos-condiciones/', views_auth.terminos_condiciones, name='terminos_condiciones'),
    path('politica-privacidad/', views_auth.politica_privacidad, name='politica_privacidad'),
    
    # Módulo de administración personalizado
    path('admin/departamentos/', RedirectView.as_view(url='/administracion/departamentos/', permanent=True)),
    path('administracion/panel/', views_admin.panel_administracion, name='panel_administracion'),
    path('administracion/usuarios/', views_admin.gestion_usuarios, name='gestion_usuarios'),
    path('administracion/solicitudes/', views_admin.gestion_solicitudes, name='gestion_solicitudes'),
    path('administracion/solicitudes/aprobar/<int:solicitud_id>/', views_admin.aprobar_solicitud, name='aprobar_solicitud'),
    path('administracion/solicitudes/rechazar/<int:solicitud_id>/', views_admin.rechazar_solicitud, name='rechazar_solicitud'),
    path('administracion/usuarios/crear/', views_admin.crear_usuario, name='crear_usuario'),
    path('administracion/usuarios/editar/<int:usuario_id>/', views_admin.editar_usuario, name='editar_usuario'),
    path('administracion/usuarios/eliminar/<int:usuario_id>/', views_admin.eliminar_usuario, name='eliminar_usuario'),
    path('administracion/departamentos/', views_admin.gestionar_departamentos, name='gestionar_departamentos'),
    path('administracion/areas/', views_admin.admin_areas, name='admin_areas'),
    path('configuracion/', views_admin.configuracion_sistema, name='configuracion_sistema'),
    
    # Módulo de documentos
    path('documentos/', include([
        path('subir/', views_documentos.subir_documento, name='subir_documento'),
        path('<int:documento_id>/', views_documentos.ver_documento, name='ver_documento'),
        path('<int:documento_id>/editar/', views_documentos.editar_documento, name='editar_documento'),
        path('<int:documento_id>/eliminar/', views_documentos.eliminar_documento, name='eliminar_documento'),
        path('<int:documento_id>/descargar/', views_documentos.descargar_documento, name='descargar_documento'),
    ])),
    
    # Módulo de reportes
    path('reportes/', include([
        path('', views.reportes, name='reportes'),
        path('obtener-expedientes/', views.obtener_expedientes_filtrados, name='obtener_expedientes_filtrados'),
        path('exportar/', views.exportar_reporte, name='exportar_reporte'),
    ])),
    
    # API Endpoints
    path('api/', include([
        path('areas/', include([
            path('', views_areas.listar_areas, name='api_areas'),
            path('<int:area_id>/', views_areas.detalle_area, name='api_detalle_area'),
            path('por-tipo/<str:tipo>/', views_areas.areas_por_tipo, name='api_areas_por_tipo'),
        ])),
        path('documentos/', include([
            path('upload/', views.upload_documento, name='api_upload_documento'),
            path('<int:documento_id>/', views.api_documento, name='api_documento'),
        ])),
        path('usuarios/conectados/', views.api_usuarios_conectados, name='api_usuarios_conectados'),
        path('estadisticas/', include([
            path('expedientes-semanales/', views.api_expedientes_semanales, name='api_expedientes_semanales'),
            path('expedientes-mensuales/', views.api_expedientes_mensuales, name='api_expedientes_mensuales'),
        ])),
        path('expedientes-por-tipo/', views.api_expedientes_por_tipo, name='api_expedientes_por_tipo'),
        # API de escaneo remoto (para usuarios autenticados)
        path('escaneo/', include([
            path('solicitar/', views_escaneo.crear_solicitud_escaneo, name='api_solicitar_escaneo'),
            path('<int:solicitud_id>/estado/', views_escaneo.estado_solicitud_escaneo, name='api_estado_escaneo'),
            path('<int:solicitud_id>/cancelar/', views_escaneo.cancelar_solicitud_escaneo, name='api_cancelar_escaneo'),
        ])),
    ])),
    
    # API para el servicio de escaneo local (requiere token)
    path('scanner/', include([
        path('solicitudes-pendientes/', views_escaneo.obtener_solicitudes_pendientes, name='scanner_solicitudes_pendientes'),
        path('solicitud/<int:solicitud_id>/procesando/', views_escaneo.marcar_solicitud_procesando, name='scanner_marcar_procesando'),
        path('solicitud/<int:solicitud_id>/completado/', views_escaneo.marcar_solicitud_completada, name='scanner_marcar_completado'),
        path('solicitud/<int:solicitud_id>/error/', views_escaneo.marcar_solicitud_error, name='scanner_marcar_error'),
    ])),
    
    # Módulos principales (incluidos desde archivos separados)
    path('expedientes/', include('digitalizacion.urls_expedientes', namespace='expedientes')),
    path('areas/', include('digitalizacion.urls_areas', namespace='areas')),
    path('mensajeria/', include('digitalizacion.urls_mensajeria', namespace='mensajeria')),
    
    # Páginas estáticas
    path('ayuda/', views.ayuda, name='ayuda'),
    path('acerca-de/', views.acerca_de, name='acerca_de'),
    path('contacto/', views.contacto, name='contacto'),
    
    # Búsqueda avanzada
    path('buscar/', views.buscar_documentos, name='buscar_documentos'),
    path('api/buscar/', views.api_buscar_documentos, name='api_buscar_documentos'),
    
    # Redirecciones para mantener compatibilidad
    path('expedientes/<int:expediente_id>/contar-documentos/', views.contar_documentos_expediente, name='contar_documentos'),
    path('expedientes/<int:expediente_id>/progreso/', views.obtener_progreso_documentos, name='progreso_expediente'),
    path('expedientes/<int:expediente_id>/progreso-documentos/', views.obtener_progreso_documentos, name='progreso_documentos'),
    path('expedientes/<int:expediente_id>/actualizar-progreso/', views.actualizar_progreso_expediente, name='actualizar_progreso_expediente'),
    
    # API para obtener documentos de un área específica
    path('expedientes/<int:expediente_id>/area/<int:area_id>/documentos/', 
         views_expedientes.obtener_documentos_area, 
         name='obtener_documentos_area'),
    
    
    # Indexar documentos existentes (solo para superusuarios)
    path('admin/indexar-documentos/', views.indexar_documentos, name='indexar_documentos'),
]
