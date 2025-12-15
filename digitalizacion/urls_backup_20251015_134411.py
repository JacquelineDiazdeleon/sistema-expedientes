from django.urls import path, include
from . import views
from . import views_auth
from . import views_admin
from . import views_expedientes
from . import views_areas
from . import views_documentos
from .views_expedientes import completar_etapa as marcar_como_completado, obtener_documentos_area
from .views_areas import areas_por_tipo

app_name = 'digitalizacion'

urlpatterns = [
    # Página principal
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/obtener-expedientes/', views.obtener_expedientes_filtrados, name='obtener_expedientes_filtrados'),
    path('reportes/exportar/', views.exportar_reporte, name='exportar_reporte'),
    
    # Autenticación
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('cambiar-password/', views_auth.cambiar_password, name='cambiar_password'),
    
    # Perfil de usuario
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    
    # Administración
    path('admin/usuarios/', views_admin.gestion_usuarios, name='gestion_usuarios'),
    path('admin/usuarios/crear/', views_admin.crear_usuario, name='crear_usuario'),
    path('admin/usuarios/editar/<int:usuario_id>/', views_admin.editar_usuario, name='editar_usuario'),
    path('admin/usuarios/eliminar/<int:usuario_id>/', views_admin.eliminar_usuario, name='eliminar_usuario'),
    
    # Configuración del sistema
    path('configuracion/', views_admin.configuracion_sistema, name='configuracion_sistema'),
    
    # API
    path('api/areas/', views_areas.listar_areas, name='api_areas'),
    path('api/areas/<int:area_id>/', views_areas.detalle_area, name='api_detalle_area'),
    path('api/areas/por-tipo/<str:tipo>/', areas_por_tipo, name='api_areas_por_tipo'),
    
    # Documentos
    path('documentos/subir/', views_documentos.subir_documento, name='subir_documento'),
    path('documentos/<int:documento_id>/', views_documentos.ver_documento, name='ver_documento'),
    path('documentos/<int:documento_id>/editar/', views_documentos.editar_documento, name='editar_documento'),
    path('documentos/<int:documento_id>/eliminar/', views_documentos.eliminar_documento, name='eliminar_documento'),
    path('documentos/<int:documento_id>/descargar/', views_documentos.descargar_documento, name='descargar_documento'),
    
    # Expedientes
    path('expedientes/', include('digitalizacion.urls_expedientes')),
    path('expedientes/buscar/', views_expedientes.buscar_expedientes, name='buscar_expedientes'),
    path('expedientes/crear/', views_expedientes.crear_expediente, name='crear_expediente'),
    path('expedientes/crear/<str:tipo>/', views_expedientes.crear_expediente, name='crear_expediente_tipo'),
    path('expedientes/<int:expediente_id>/', views_expedientes.detalle_expediente, name='detalle_expediente'),
    path('expedientes/<int:expediente_id>/editar/', views_expedientes.editar_expediente, name='editar_expediente'),
    path('expedientes/<int:expediente_id>/eliminar/', views_expedientes.eliminar_expediente, name='eliminar_expediente'),
    path('expedientes/<int:expediente_id>/documentos/', views_expedientes.ver_documentos_expediente, name='ver_documentos_expediente'),
    path('expedientes/<int:expediente_id>/etapa/<str:etapa>/subir-documento/', 
         views_expedientes.subir_documento, name='subir_documento'),
    path('documentos/<int:documento_id>/', views_expedientes.ver_documento_expediente, name='ver_documento_expediente'),
    path('expedientes/<int:expediente_id>/documentos/<int:documento_id>/editar/', views_expedientes.editar_documento_expediente, name='editar_documento_expediente'),
    path('expedientes/<int:expediente_id>/documentos/<int:documento_id>/eliminar/', views_expedientes.eliminar_documento_expediente, name='eliminar_documento_expediente'),
    path('expedientes/<int:expediente_id>/documentos/<int:documento_id>/descargar/', views_expedientes.descargar_documento_expediente, name='descargar_documento_expediente'),
    path('expedientes/<int:expediente_id>/comentarios/', views_expedientes.agregar_comentario, name='agregar_comentario'),
    path('expedientes/<int:expediente_id>/comentarios/<int:comentario_id>/eliminar/', views_expedientes.eliminar_comentario, name='eliminar_comentario'),
    path('expedientes/<int:expediente_id>/estado/', views_expedientes.cambiar_estado_expediente, name='cambiar_estado_expediente'),
    path('expedientes/<int:expediente_id>/asignar/', views_expedientes.asignar_expediente, name='asignar_expediente'),
    path('expedientes/<int:expediente_id>/transferir/', views_expedientes.transferir_expediente, name='transferir_expediente'),
    path('expedientes/<int:expediente_id>/historial/', views_expedientes.ver_historial, name='ver_historial'),
    path('expedientes/<int:expediente_id>/contar-documentos/', views.contar_documentos_expediente, name='contar_documentos'),
    path('expedientes/<int:expediente_id>/marcar-completado/', marcar_como_completado, name='marcar_como_completado'),
    path('expedientes/<int:expediente_id>/progreso-documentos/', views.obtener_progreso_documentos, name='progreso_documentos'),
    
    # Rutas para áreas
    path('areas/', include('digitalizacion.urls_areas')),
    
    # API de documentos
    path('api/documentos/upload/', views.upload_documento, name='api_upload_documento'),
    path('api/documentos/<int:documento_id>/', views.api_documento, name='api_documento'),
    path('api/usuarios/conectados/', views.api_usuarios_conectados, name='api_usuarios_conectados'),
    
    # Otras rutas
    path('ayuda/', views.ayuda, name='ayuda'),
    path('acerca-de/', views.acerca_de, name='acerca_de'),
    path('contacto/', views.contacto, name='contacto'),
    path('admin/panel/', views.panel_administracion, name='panel_administracion'),
]
