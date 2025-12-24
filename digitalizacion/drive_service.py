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
    """
    service = get_drive_service()
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return file.get('id')

def get_storage_usage():
    """
    Consulta cuánto espacio queda en la cuenta (Fase 4 y 5)
    """
    service = get_drive_service()
    about = service.about().get(fields="storageQuota").execute()
    usage = int(about['storageQuota']['usage']) / (1024**3) # Convertido a GB
    limit = int(about['storageQuota']['limit']) / (1024**3) # Convertido a GB
    
    return usage, limit

def get_view_link(file_id):
    """
    Obtiene un enlace de visualización para el archivo de Drive.
    """
    service = get_drive_service()
    # Obtenemos el enlace webViewLink
    file = service.files().get(file_id=file_id, fields='webViewLink').execute()
    return file.get('webViewLink')

