import os
from pathlib import Path
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuración de las credenciales
# Buscar el archivo en la raíz del proyecto o usar variable de entorno
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SERVICE_ACCOUNT_FILE = os.environ.get(
    'GOOGLE_KEYS_PATH',
    os.path.join(BASE_DIR, 'google_keys.json')
)
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Obtiene el servicio de Google Drive"""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Archivo de credenciales no encontrado: {SERVICE_ACCOUNT_FILE}. "
            "Asegúrate de que google_keys.json esté en la raíz del proyecto o "
            "configura GOOGLE_KEYS_PATH como variable de entorno."
        )
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, file_name, folder_id):
    """
    Sube un archivo a una carpeta específica de Google Drive
    El secreto está en definir el 'parents' para que use el espacio de tu cuenta
    """
    service = get_drive_service()
    
    # El secreto está en definir el 'parents' para que use el espacio de tu cuenta
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # Esto obliga a que use el espacio de la carpeta, no del robot
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        # IMPORTANTE: Añadir supportsAllDrives=True por seguridad
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True  # Añade esto por seguridad
        ).execute()
        return file.get('id')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error detallado en Drive: {e}")
        raise e

def get_storage_usage():
    """
    Consulta cuánto espacio queda en la cuenta (Fase 4 y 5)
    Nota: Las Service Accounts no tienen cuota propia, usan el espacio de las carpetas compartidas.
    Si la Service Account no tiene cuota, retorna None, None para indicar que no se puede verificar.
    """
    try:
        service = get_drive_service()
        about = service.about().get(fields="storageQuota").execute()
        
        # Verificar si la Service Account tiene cuota propia
        storage_quota = about.get('storageQuota', {})
        
        # Si no hay 'limit', significa que la Service Account no tiene cuota propia
        if 'limit' not in storage_quota:
            return None, None
        
        usage = int(storage_quota.get('usage', 0)) / (1024**3)  # Convertido a GB
        limit = int(storage_quota.get('limit', 0)) / (1024**3)  # Convertido a GB
        
        return usage, limit
    except Exception as e:
        # Si hay error al consultar (por ejemplo, Service Account sin cuota), retornar None
        # Esto permite que la subida continúe usando el espacio de la carpeta compartida
        return None, None

def get_view_link(file_id):
    """
    Obtiene un enlace de visualización para el archivo de Drive.
    """
    service = get_drive_service()
    # Obtenemos el enlace webViewLink
    file = service.files().get(file_id=file_id, fields='webViewLink').execute()
    return file.get('webViewLink')

