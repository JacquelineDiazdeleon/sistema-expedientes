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
        # Solo indexar si el documento tiene un archivo
        if not instance.archivo:
            logger.debug(f"Documento {instance.id} no tiene archivo, no se indexará")
            return
            
        import os
        from django.conf import settings
        from django.db import transaction
        
        # Obtener la ruta del archivo
        file_path = None
        if hasattr(instance.archivo, 'path'):
            file_path = instance.archivo.path
        else:
            # Construir la ruta desde el name
            file_path = os.path.join(settings.MEDIA_ROOT, instance.archivo.name)
        
        # Verificar que el archivo existe en el sistema de archivos
        if file_path and os.path.exists(file_path):
            # Verificar que el archivo no esté vacío
            if os.path.getsize(file_path) > 0:
                # Indexar el documento
                if index_document(instance):
                    logger.info(f"Documento {instance.id} indexado correctamente desde signal")
                else:
                    logger.warning(f"No se pudo indexar documento {instance.id} desde signal")
            else:
                logger.warning(f"Archivo vacío para documento {instance.id}: {file_path}")
        elif created:
            # Si es nuevo y el archivo aún no existe, intentar indexar de todas formas
            # (puede que el archivo se esté guardando aún)
            # Usar transaction.on_commit para indexar después de que la transacción se complete
            def index_after_commit():
                try:
                    # Refrescar el documento desde la BD
                    instance.refresh_from_db()
                    if instance.archivo:
                        index_document(instance)
                        logger.info(f"Documento {instance.id} indexado después de commit (nuevo documento)")
                except Exception as e:
                    logger.error(f"Error al indexar documento {instance.id} después de commit: {str(e)}", exc_info=True)
            
            transaction.on_commit(index_after_commit)
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
