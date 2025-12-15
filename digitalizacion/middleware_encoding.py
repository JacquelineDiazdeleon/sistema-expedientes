from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class UTF8ResponseMiddleware(MiddlewareMixin):
    """
    Middleware para asegurar que todas las respuestas usen UTF-8
    """
    def process_response(self, request, response):
        # Asegurar que la respuesta sea tratada como UTF-8
        if 'Content-Type' in response:
            if ';' in response['Content-Type']:
                # Si ya hay parámetros, agregar charset si no existe
                if 'charset=' not in response['Content-Type'].lower():
                    response['Content-Type'] = response['Content-Type'].split(';')[0] + '; charset=utf-8'
            else:
                # Si no hay parámetros, agregar charset
                if response['Content-Type'].startswith('text/') or 'json' in response['Content-Type']:
                    response['Content-Type'] += '; charset=utf-8'
        
        # Para respuestas que son instancias de HttpResponse
        if hasattr(response, 'charset') and response.charset is None:
            response.charset = 'utf-8'
            
        return response
