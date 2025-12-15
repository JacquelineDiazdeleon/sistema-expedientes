from django.urls import path
from . import views
from . import views_auth

app_name = 'digitalizacion'

urlpatterns = [
    # Página principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de documentos
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('documentos/crear/', views.crear_documento, name='crear_documento'),
    path('documentos/<int:pk>/', views.detalle_documento, name='detalle_documento'),
    path('documentos/<int:pk>/editar/', views.editar_documento, name='editar_documento'),
    path('documentos/<int:pk>/eliminar/', views.eliminar_documento, name='eliminar_documento'),
    path('documentos/<int:pk>/digitalizar/', views.digitalizar_documento, name='digitalizar_documento'),
    path('documentos/<int:pk>/verificar/', views.verificar_documento, name='verificar_documento'),
    
    # Búsqueda y filtros
    path('buscar/', views.buscar_documentos, name='buscar_documentos'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar/', views.exportar_reporte, name='exportar_reporte'),
    
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
    path('tipos-documento/', views.gestionar_tipos_documento, name='tipos_documento'),
    path('departamentos/', views.gestionar_departamentos, name='departamentos'),
    
    # API endpoints (para futuras integraciones)
    path('api/documentos/', views.api_documentos, name='api_documentos'),
    path('api/estadisticas/', views.api_estadisticas, name='api_estadisticas'),
    
    # Autenticación (usando views_auth)
    path('login/', views_auth.login_view, name='login'),
    path('register/', views_auth.register_view, name='register'),
    path('registro/', views_auth.register_view, name='registro'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('cambiar-password/', views_auth.cambiar_password, name='cambiar_password'),
    path('profile/', views.user_profile, name='profile'),
]
