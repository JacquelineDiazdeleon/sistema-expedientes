from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import json
import logging

from .models import UserSession

logger = logging.getLogger(__name__)

class SuppressChromeDevToolsMiddleware(MiddlewareMixin):
    """
    Middleware para suprimir warnings de Chrome DevTools
    """
    def process_request(self, request):
        # Ignorar peticiones de Chrome DevTools
        if '/.well-known/appspecific/com.chrome.devtools.json' in request.path:
            return HttpResponse(status=404)
        return None


class JsonErrorHandlerMiddleware(MiddlewareMixin):
    """
    Middleware para manejar errores en respuestas JSON
    """
    def process_response(self, request, response):
        # Solo procesar si es una respuesta JSON y hay un error
        if response.get('Content-Type') == 'application/json' and 400 <= response.status_code < 600:
            try:
                # Intentar cargar el contenido JSON
                data = json.loads(response.content)
                
                # Si ya es un objeto con 'error', no hacer nada
                if 'error' in data:
                    return response
                    
                # Si es una lista, envolver en un objeto
                if isinstance(data, list):
                    data = {'data': data}
                    
                # Asegurarse de que hay un mensaje de error
                if 'message' not in data and 'detail' not in data:
                    if response.status_code == 400:
                        data['message'] = 'Solicitud incorrecta'
                    elif response.status_code == 401:
                        data['message'] = 'No autorizado'
                    elif response.status_code == 403:
                        data['message'] = 'Permiso denegado'
                    elif response.status_code == 404:
                        data['message'] = 'Recurso no encontrado'
                    elif response.status_code == 500:
                        data['message'] = 'Error interno del servidor'
                    
                # Crear una nueva respuesta con el formato estándar
                response = JsonResponse({
                    'error': True,
                    'status_code': response.status_code,
                    **data
                }, status=response.status_code)
                
            except json.JSONDecodeError:
                # Si hay un error al decodificar el JSON, crear un mensaje de error genérico
                response = JsonResponse({
                    'error': True,
                    'status_code': response.status_code,
                    'message': 'Error en el servidor al procesar la respuesta',
                    'original_status': response.status_code
                }, status=response.status_code)
            except Exception as e:
                # Registrar cualquier otro error
                logger = logging.getLogger(__name__)
                logger.error(f'Error en JsonErrorHandlerMiddleware: {str(e)}')
                
        return response


class UpdateLastActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity and update last activity time
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process the request and update the user's last activity time
        """
        if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request, 'session'):
            # Only update every 5 minutes to reduce database writes
            threshold = timezone.now() - timezone.timedelta(minutes=5)
            
            # Get or create the user session
            user_session, created = UserSession.objects.get_or_create(
                user=request.user,
                session_key=request.session.session_key,
                defaults={
                    'last_activity': timezone.now(),
                    'is_online': True
                }
            )
            
            # Update if it's not new and last activity is older than threshold
            if not created and user_session.last_activity < threshold:
                user_session.last_activity = timezone.now()
                user_session.is_online = True
                user_session.save(update_fields=['last_activity', 'is_online'])
        return None
