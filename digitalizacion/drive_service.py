import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Mantendremos la estructura para que no rompa el resto del sistema
def get_drive_service():
    """
    Obtiene el servicio de Google Drive usando Service Account
    NOTA: Para cuentas @gmail.com personales, Domain-wide Delegation NO está disponible.
    Las Service Accounts no pueden usar el espacio de cuentas @gmail.com personales.
    """
    creds_path = os.environ.get('GOOGLE_KEYS_PATH', 'google_keys.json')
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Archivo de credenciales no encontrado: {creds_path}")
        
    scopes = ['https://www.googleapis.com/auth/drive']
    
    # Para cuentas @gmail.com personales, Domain-wide Delegation NO funciona
    # Usamos la Service Account directamente (aunque tendrá limitaciones de cuota)
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=scopes)
    
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, file_name, folder_id):
    """
    Sube un archivo a Google Drive
    NOTA: Para cuentas @gmail.com personales, las Service Accounts tienen limitaciones.
    Si falla, el sistema guardará el archivo localmente como respaldo.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        service = get_drive_service()
    except Exception as e:
        logger.error(f"Error al obtener servicio de Drive: {e}")
        raise e

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
        error_msg = str(e)
        # Si es error de cuota, proporcionar mensaje más claro
        if 'storageQuotaExceeded' in error_msg or 'storage quota' in error_msg.lower():
            logger.warning(
                "Error de cuota en Drive (Service Account sin espacio). "
                "Para cuentas @gmail.com personales, considera deshabilitar Drive "
                "o usar OAuth 2.0 en lugar de Service Account."
            )
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

