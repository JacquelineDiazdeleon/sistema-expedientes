from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete
from django.contrib.sessions.models import Session
from .models import HistorialExpediente, UserSession, DocumentoExpediente
from .search_utils import index_document, remove_document
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Signal handler for user login events.
    Creates a HistorialExpediente entry when a user logs in
    and updates the UserSession.
    """
    # Create a login activity entry without requiring an expediente
    try:
        HistorialExpediente.objects.create(
            usuario=user,
            accion="Inicio de sesión",
            descripcion=f"{user.get_full_name() or user.username} inició sesión"
            # No pasamos el parámetro expediente ya que es opcional
        )
    except Exception as e:
        # Log the error but don't prevent login
        logger.error(f"Error al registrar inicio de sesión: {str(e)}")
    
    # Update or create user session
    if hasattr(request, 'session'):
        UserSession.update_user_activity(user, request.session.session_key)

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Signal handler for user logout events.
    Updates the UserSession to mark user as offline.
    """
    if hasattr(request, 'session') and user.is_authenticated:
        UserSession.objects.filter(
            user=user, 
            session_key=request.session.session_key
        ).update(is_online=False)

@receiver(post_save, sender=DocumentoExpediente)
def index_documento(sender, instance, created, **kwargs):
    """
    Signal handler para indexar documentos cuando se crean o actualizan
    """
    try:
        # Solo indexar si el documento tiene un archivo y el archivo existe
        if instance.archivo:
            import os
            from django.conf import settings
            
            # Verificar que el archivo existe en el sistema de archivos
            file_path = instance.archivo.path if hasattr(instance.archivo, 'path') else None
            if file_path and os.path.exists(file_path):
                index_document(instance)
                logger.info(f"Documento {instance.id} indexado correctamente")
            elif created:
                # Si es nuevo y aún no tiene archivo, intentar indexar de todas formas
                # (puede que el archivo se esté guardando)
                index_document(instance)
                logger.info(f"Documento {instance.id} indexado (nuevo documento)")
            else:
                logger.warning(f"Documento {instance.id} no se pudo indexar: archivo no encontrado en {file_path}")
    except Exception as e:
        logger.error(f"Error al indexar documento {instance.id}: {str(e)}", exc_info=True)

@receiver(pre_delete, sender=DocumentoExpediente)
def eliminar_documento_indice(sender, instance, **kwargs):
    """
    Signal handler para eliminar documentos del índice cuando se eliminan
    """
    try:
        remove_document(instance.id)
        logger.info(f"Documento {instance.id} eliminado del índice")
    except Exception as e:
        logger.error(f"Error al eliminar documento {instance.id} del índice: {str(e)}")

def update_last_activity(sender, **kwargs):
    """
    Middleware to update last activity time for the current user session
    """
    request = kwargs.get('request')
    if request.user.is_authenticated and hasattr(request, 'session'):
        UserSession.objects.filter(
            user=request.user,
            session_key=request.session.session_key
        ).update(last_activity=timezone.now())
