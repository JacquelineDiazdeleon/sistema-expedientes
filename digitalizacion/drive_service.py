import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_drive_service():
    """
    Obtiene el servicio de Google Drive usando OAuth 2.0 Token personal
    Este método usa tu cuenta personal directamente, usando tus 15GB
    """
    token_path = os.environ.get('GOOGLE_TOKEN_PATH', 'google_token.json')
    
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"No se encontró el token en {token_path}")
        
    with open(token_path, 'r') as f:
        info = json.load(f)
        
    creds = Credentials.from_authorized_user_info(info)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, file_name, folder_id):
    """
    Sube un archivo a Google Drive usando OAuth 2.0 Token personal
    Este método usa tu cuenta personal directamente, usando tus 15GB
    """
    service = get_drive_service()
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=False)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error definitivo con Token: {e}")
        raise e

def get_storage_usage():
    """
    Consulta cuánto espacio queda en la cuenta (Fase 4 y 5)
    Nota: Con Domain-wide Delegation, consulta el espacio de tu cuenta personal
    """
    try:
        service = get_drive_service()
        about = service.about().get(fields="storageQuota").execute()
        
        storage_quota = about.get('storageQuota', {})
        
        # Si no hay 'limit', significa que no se puede verificar
        if 'limit' not in storage_quota:
            return None, None
        
        usage = int(storage_quota.get('usage', 0)) / (1024**3)  # Convertido a GB
        limit = int(storage_quota.get('limit', 0)) / (1024**3)  # Convertido a GB
        
        return usage, limit
    except Exception as e:
        # Si hay error al consultar, retornar None
        return None, None

def get_view_link(file_id):
    """
    Obtiene un enlace de visualización para el archivo de Drive.
    """
    service = get_drive_service()
    # Obtenemos el enlace webViewLink
    file = service.files().get(file_id=file_id, fields='webViewLink').execute()
    return file.get('webViewLink')

