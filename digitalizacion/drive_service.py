import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuración de las credenciales
SERVICE_ACCOUNT_FILE = 'google_keys.json' # El nombre que le pusiste al archivo
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
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

