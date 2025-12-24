import cloudinary
import cloudinary.uploader
import os
import re  # Para limpiar el nombre

# Configuración blindada contra espacios accidentales
cloudinary.config( 
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '').strip(), 
    api_key = os.environ.get('CLOUDINARY_API_KEY', '').strip(), 
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', '').strip(),
    secure = True
)

def upload_to_cloudinary(file_path, file_name):
    """
    Sube un archivo a Cloudinary y devuelve la URL para acceder a él.
    Limpia el nombre del archivo para evitar errores de firma.
    """
    try:
        # 1. Limpiamos el nombre: quitamos espacios y caracteres especiales
        # Esto evita el error de "Invalid Signature"
        # Reemplazamos todo lo que no sea letra, número, punto o guion con guion bajo
        clean_name = re.sub(r'[^a-zA-Z0-9.-]', '_', file_name)
        
        # 2. Subimos el archivo con el nombre limpio
        response = cloudinary.uploader.upload(
            file_path, 
            public_id = clean_name,  # Usamos el nombre limpio
            folder = "expedientes",  # Carpeta separada
            resource_type = "auto"
        )
        # Devolvemos la URL segura (https)
        return response.get('secure_url')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        # Esto imprimirá el error real si las llaves están mal
        logger.error(f"Error detallado en Cloudinary: {e}")
        print(f"Error detallado en Cloudinary: {e}")
        return None

# Funciones de compatibilidad (para no romper código existente)
def upload_to_drive(file_path, file_name, folder_id=None):
    """
    Función de compatibilidad: ahora usa Cloudinary en lugar de Drive
    El parámetro folder_id se ignora, pero se mantiene para compatibilidad
    """
    return upload_to_cloudinary(file_path, file_name)

def get_view_link(file_id_or_url):
    """
    Obtiene un enlace de visualización.
    Si es una URL de Cloudinary, la devuelve directamente.
    Si es un ID de Drive (legacy), intenta obtener el enlace.
    """
    # Si ya es una URL (Cloudinary), devolverla directamente
    if file_id_or_url and (file_id_or_url.startswith('http://') or file_id_or_url.startswith('https://')):
        return file_id_or_url
    
    # Si es un ID de Drive (legacy), intentar obtener el enlace
    # Nota: Esto solo funcionará si aún tienes configurado Google Drive
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import json
        
        token_path = os.environ.get('GOOGLE_TOKEN_PATH', 'google_token.json')
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                info = json.load(f)
            creds = Credentials.from_authorized_user_info(info)
            service = build('drive', 'v3', credentials=creds)
            file = service.files().get(file_id=file_id_or_url, fields='webViewLink').execute()
            return file.get('webViewLink')
    except Exception:
        pass
    
    return file_id_or_url

