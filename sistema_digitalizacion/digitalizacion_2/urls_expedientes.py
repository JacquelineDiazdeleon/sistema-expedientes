from django.urls import path
from . import views_expedientes, views_expedientes_updated, fixed_views_expedientes
from .document_views import subir_documento, subir_documento_temporal, eliminar_documento

app_name = 'expedientes'

urlpatterns = [
    # Dashboard
    path('', views_expedientes.dashboard_expedientes, name='dashboard'),
    
    # Listado de expedientes
    path('lista/', views_expedientes.lista_expedientes, name='lista'),
    
    # Creación de expedientes
    path('crear/', views_expedientes.seleccionar_tipo_expediente, name='seleccionar_tipo'),
    path('crear/<str:tipo>/', views_expedientes.crear_expediente, name='crear'),
    
    # Detalle y gestión de expedientes
    path('<int:pk>/', views_expedientes.detalle_expediente, name='detalle'),
    
    # Gestión de etapas - Rutas para subida de documentos
    # Ruta temporal para compatibilidad con el frontend existente
    path('<int:expediente_id>/subir-documento/', 
         document_views.subir_documento_temporal, 
         name='subir_documento_temporal'),

    # Ruta mejorada con etapa en la URL
    path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/', 
         subir_documento, 
         name='subir_documento'),
    
    # Eliminación de documentos
    path('documento/<int:documento_id>/eliminar/', 
         eliminar_documento, 
         name='eliminar_documento'),
    
    path('<int:expediente_id>/etapa/<str:etapa>/completar/', 
         views_expedientes.completar_etapa, name='completar_etapa'),
    path('<int:expediente_id>/etapa/<str:etapa>/comentario/', 
         views_expedientes.agregar_comentario, name='agregar_comentario'),
    
    # Gestión de expedientes
    path('<int:expediente_id>/rechazar/', 
         views_expedientes.rechazar_expediente, name='rechazar_expediente'),
    
    # Visualizador de expediente completo
    path('<int:expediente_id>/visualizador/', 
         views_expedientes.visualizador_expediente, name='visualizador'),
    path('<int:expediente_id>/descargar-completo/',
         views_expedientes.descargar_expediente_completo, name='descargar_completo'),
    path('<int:expediente_id>/pdf-completo/',
         views_expedientes.generar_pdf_completo, name='pdf_completo'),
    
    # Gestión de notas
    path('<int:expediente_id>/notas/crear/', 
         views_expedientes.crear_nota, name='crear_nota'),
    path('<int:expediente_id>/notas/<int:nota_id>/editar/', 
         views_expedientes.editar_nota, name='editar_nota'),
    path('<int:expediente_id>/notas/<int:nota_id>/eliminar/', 
         views_expedientes.eliminar_nota, name='eliminar_nota'),
    
    # Sistema colaborativo y menciones
    path('<int:expediente_id>/comentarios/crear/', 
         views_expedientes.crear_comentario_area, name='crear_comentario_area'),
    
    # Documentos por área - Usando la vista actualizada
    path('<int:expediente_id>/documentos-por-area/<path:area_id>/', 
         views_expedientes_updated.obtener_documentos_por_area, name='documentos_por_area'),
         
    # Progreso de documentos
    path('<int:expediente_id>/progreso-documentos/', 
         views_expedientes.obtener_progreso_documentos, name='progreso_documentos'),
    path('notificaciones/<int:notificacion_id>/leer/', 
         views_expedientes.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    
    # AJAX endpoints
    path('api/notificaciones/', 
         views_expedientes.obtener_notificaciones, name='obtener_notificaciones'),
    path('api/usuarios-mencion/', 
         views_expedientes.obtener_usuarios_mencion, name='obtener_usuarios_mencion'),
]
