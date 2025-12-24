import cloudinary
import cloudinary.uploader
import os

# Se configura usando las variables que pusiste en Render
cloudinary.config( 
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'), 
    api_key = os.environ.get('CLOUDINARY_API_KEY'), 
    api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
    secure = True
)

def upload_to_cloudinary(file_path, file_name):
    """
    Sube un archivo a Cloudinary y devuelve la URL para acceder a él.
    """
    try:
        # 'resource_type="auto"' permite subir PDFs, Word y archivos de texto
        response = cloudinary.uploader.upload(
            file_path, 
            public_id = f"expedientes/{file_name}",
            resource_type = "auto"
        )
        # Devolvemos la URL segura (https)
        return response.get('secure_url')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al subir a Cloudinary: {e}")
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

