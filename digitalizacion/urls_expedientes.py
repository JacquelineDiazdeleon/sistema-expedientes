from django.urls import path
from .views_expedientes import (
    dashboard_expedientes, lista_expedientes, seleccionar_tipo_expediente,
    crear_expediente, editar_expediente, ver_documentos_expediente, guardar_expediente,
    rechazar_expediente, eliminar_expediente, detalle_expediente,
    subir_documento, completar_etapa, agregar_comentario, obtener_documentos_area,
    eliminar_documento_area, ver_historial, obtener_detalles_expediente,
    obtener_usuarios_mencion, obtener_notificaciones, listar_areas,
    marcar_notificacion_leida, crear_comentario_area, enviar_mensaje_expediente,
    obtener_mensajes_expediente, enviar_mensaje_usuario, agregar_sima,
    buscar_expedientes, obtener_mensajes_usuario, eliminar_documento_expediente,
    ver_documento_expediente, ver_documento_drive, editar_documento_expediente, descargar_documento_expediente,
    descargar_expediente, generar_pdf_completo, obtener_progreso_expediente, 
    obtener_documentos_expediente_api, editar_numero_sima
)
from .api_views import subir_documento_api, subir_documento_escaneado_api

app_name = 'expedientes'

urlpatterns = [
    # Dashboard
    path('', dashboard_expedientes, name='dashboard'),
    
    # Listado de expedientes
    path('lista/', lista_expedientes, name='lista_expedientes'),
    
    # Creación de expedientes
    path('crear/', seleccionar_tipo_expediente, name='seleccionar_tipo'),
    path('crear/<str:tipo_id>/', crear_expediente, name='crear'),
    
    # Vista simple de documentos (DEBE IR ANTES que detalle)
    path('<int:expediente_id>/documentos/', 
         ver_documentos_expediente, name='ver_documentos'),
    
    # Guardar expediente
    path('<int:expediente_id>/guardar/', 
         guardar_expediente, name='guardar_expediente'),
    
    # Gestión de expedientes
    path('<int:expediente_id>/rechazar/', 
         rechazar_expediente, name='rechazar_expediente'),
    path('<int:expediente_id>/eliminar/', 
         eliminar_expediente, name='eliminar'),
    
    # Detalle y gestión de expedientes (DEBE IR AL FINAL)
    path('<int:expediente_id>/', detalle_expediente, name='detalle'),
    path('<int:expediente_id>/editar/', editar_expediente, name='editar'),
    
    # Gestión de etapas
    path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/', 
         subir_documento, name='subir_documento'),
    # Ruta alternativa sin etapa (el área se obtiene del POST)
    path('<int:expediente_id>/subir-documento/', 
         subir_documento, name='subir_documento_sin_etapa'),
    path('<int:expediente_id>/etapa/<str:etapa>/completar/', 
         completar_etapa, name='completar_etapa'),
    path('<int:expediente_id>/etapa/<str:etapa>/comentario/', 
         agregar_comentario, name='agregar_comentario'),
    
    # Descargas y generación de PDF
    path('<int:expediente_id>/descargar-completo/',
         descargar_expediente, name='descargar_completo'),
    path('<int:expediente_id>/pdf-completo/',
         generar_pdf_completo, name='pdf_completo'),
    
    # Documentos por área (dos formatos de URL para compatibilidad)
    path('<int:expediente_id>/documentos-por-area/<int:area_id>/', 
         obtener_documentos_area, name='documentos_por_area'),
    path('<int:expediente_id>/area/<int:area_id>/documentos/', 
         obtener_documentos_area, name='obtener_documentos_area'),
    
    # Historial
    path('<int:expediente_id>/historial/', 
         ver_historial, name='ver_historial'),
    
    # API Endpoints
    path('api/<int:expediente_id>/detalles/', 
         obtener_detalles_expediente, name='api_detalles_expediente'),
    path('api/<int:expediente_id>/documentos/', 
         obtener_documentos_expediente_api, name='api_documentos_expediente'),
    path('<int:expediente_id>/detalles-json/', 
         obtener_detalles_expediente, name='detalles_json'),
    path('usuarios/mencion/', 
         obtener_usuarios_mencion, name='obtener_usuarios_mencion'),
    path('notificaciones/', 
         obtener_notificaciones, name='obtener_notificaciones'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', 
         marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('areas/', 
         listar_areas, name='listar_areas'),
    
    # Mensajería
    path('<int:expediente_id>/mensajes/enviar/', 
         enviar_mensaje_expediente, name='enviar_mensaje'),
    path('<int:expediente_id>/mensajes/', 
         obtener_mensajes_expediente, name='obtener_mensajes'),
    path('mensajes/enviar-usuario/', 
         enviar_mensaje_usuario, name='enviar_mensaje_usuario'),
    path('mensajes/usuario/<int:usuario_id>/', 
         obtener_mensajes_usuario, name='obtener_mensajes_usuario'),
    
    # SIMA
    path('<int:expediente_id>/agregar-sima/', 
         agregar_sima, name='agregar_sima'),
    path('<int:expediente_id>/editar-sima/', 
         editar_numero_sima, name='editar_numero_sima'),
    
    # Búsqueda
    path('buscar/', 
         buscar_expedientes, name='buscar'),
    
    # Generar PDF completo del expediente
    path('<int:expediente_id>/generar-pdf/', 
         generar_pdf_completo, name='generar_pdf_completo'),
    
    # Obtener progreso del expediente (para actualizaciones en tiempo real)
    path('<int:expediente_id>/obtener-progreso/', 
         obtener_progreso_expediente, name='obtener_progreso'),
    
    # Documentos
    path('documentos/expediente/<int:expediente_id>/', ver_documentos_expediente, name='ver_documentos'),
    path('documentos/subir/', subir_documento, name='subir_documento'),
    path('expedientes/documentos/subir/', subir_documento, name='subir_documento_ajax'),
    path('<int:expediente_id>/documentos/eliminar/<int:documento_id>/', 
         eliminar_documento_expediente, name='eliminar_documento'),
    path('documentos/<int:documento_id>/', 
         ver_documento_expediente, name='ver_documento'),
    path('documentos/<int:documento_id>/drive/', 
         ver_documento_drive, name='ver_documento_drive'),
    path('documentos/<int:documento_id>/servir/', 
         servir_documento, name='servir_documento'),
    path('<int:expediente_id>/documentos/editar/<int:documento_id>/', 
         editar_documento_expediente, name='editar_documento'),
    path('<int:expediente_id>/documentos/descargar/<int:documento_id>/', 
         descargar_documento_expediente, name='descargar_documento'),
    
    # API Endpoints
    path('api/documentos/subir/', subir_documento_api, name='api_subir_documento'),
    
    # Endpoint para escáner local (servicio NAPS2)
    path('api/documentos/escaneado/', subir_documento_escaneado_api, name='api_subir_documento_escaneado'),
]
