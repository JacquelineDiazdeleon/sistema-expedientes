import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Mantendremos la estructura para que no rompa el resto del sistema
def get_drive_service():
    # Intentaremos usar la cuenta de servicio con "Impersonación"
    # Si tienes habilitada la delegación de dominio.
    # Si no, este bloque asegura la conexión básica.
    creds_path = os.environ.get('GOOGLE_KEYS_PATH', 'google_keys.json')
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Archivo de credenciales no encontrado: {creds_path}")
        
    scopes = ['https://www.googleapis.com/auth/drive']
    
    # Aquí está el truco: le decimos que el sujeto de la subida es tu correo
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=scopes)
    
    # Delegamos la autoridad a tu cuenta personal para usar tus 15GB
    # Nota: Esto solo funciona si activaste "Domain-wide Delegation" en la consola
    delegate_creds = creds.with_subject('leondiazdeleondiazdeleon@gmail.com')
    
    return build('drive', 'v3', credentials=delegate_creds)

def upload_to_drive(file_path, file_name, folder_id):
    try:
        service = get_drive_service()
    except Exception:
        # Si la delegación falla, usamos el service normal para el intento final
        from google.oauth2 import service_account
        creds_path = os.environ.get('GOOGLE_KEYS_PATH', 'google_keys.json')
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, resumable=False)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return file.get('id')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error crítico en Drive: {e}")
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

