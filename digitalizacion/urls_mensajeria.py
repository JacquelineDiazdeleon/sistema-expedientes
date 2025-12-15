from django.urls import path
from . import views_mensajeria

app_name = 'mensajeria'

urlpatterns = [
    # Vista principal de mensajería
    path('', views_mensajeria.mensajeria, name='mensajeria'),
    
    # Chats individuales
    path('chat/<int:user_id>/', views_mensajeria.chat_individual, name='chat_individual'),
    
    # Chats de grupo
    path('grupo/<int:chat_id>/', views_mensajeria.chat_grupo, name='chat_grupo'),
    path('crear-grupo/', views_mensajeria.crear_chat_grupo, name='crear_chat_grupo'),
    
    # APIs para mensajes
    path('api/enviar-mensaje/', views_mensajeria.enviar_mensaje, name='enviar_mensaje'),
    path('api/subir-archivo/', views_mensajeria.subir_archivo, name='subir_archivo'),
    path('api/mensajes/<int:chat_id>/', views_mensajeria.obtener_mensajes, name='obtener_mensajes'),
    path('api/buscar-usuarios/', views_mensajeria.buscar_usuarios, name='buscar_usuarios'),
    path('api/marcar-leido/<int:mensaje_id>/', views_mensajeria.marcar_leido, name='marcar_leido'),
    path('api/eliminar-mensaje/<int:mensaje_id>/', views_mensajeria.eliminar_mensaje, name='eliminar_mensaje'),
    path('api/editar-mensaje/<int:mensaje_id>/', views_mensajeria.editar_mensaje, name='editar_mensaje'),
]
