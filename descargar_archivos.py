"""
Script para descargar archivos desde Render a la PC local.
Este script debe ejecutarse periódicamente (por ejemplo, cada hora) usando Task Scheduler.

Configuración:
- Carpeta principal: C:/servidor/Expedientes
- Carpeta de respaldo: D:/Resp/Respaldo_SistemaDigitalizacion
- Endpoint de Django: https://sistema-expedientes-u2em.onrender.com/api/archivos/pendientes/
"""

import os
import requests
from pathlib import Path
import shutil
import json
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('descargar_archivos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN ==========
# Carpeta principal donde se guardarán los archivos
BASE_PC = Path("C:/servidor/Expedientes")
BASE_PC.mkdir(exist_ok=True, parents=True)

# Carpeta de respaldo
BACKUP = Path("D:/Resp/Respaldo_SistemaDigitalizacion")
BACKUP.mkdir(exist_ok=True, parents=True)

# Endpoint de Django
URL_BASE = "https://sistema-expedientes-u2em.onrender.com"
URL_LISTAR = f"{URL_BASE}/api/archivos/pendientes/"

# Timeout para las peticiones (segundos)
TIMEOUT = 30

# ====================================

def descargar_archivo(url, destino):
    """
    Descarga un archivo desde una URL.
    
    Args:
        url: URL del archivo
        destino: Path donde guardar el archivo
        
    Returns:
        True si se descargó correctamente, False en caso contrario
    """
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True)
        response.raise_for_status()
        
        # Crear directorios si no existen
        destino.parent.mkdir(parents=True, exist_ok=True)
        
        # Descargar en bloques para archivos grandes
        with open(destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        logger.error(f"Error al descargar {url}: {str(e)}")
        return False


def marcar_descargado(documento_id, ruta_externa, tipo='expediente'):
    """
    Marca un documento como descargado en Django.
    
    Args:
        documento_id: ID del documento
        ruta_externa: Ruta del archivo en la PC local
        tipo: Tipo de documento ('expediente' o 'documento')
    """
    try:
        url = f"{URL_BASE}/api/archivos/{documento_id}/marcar-descargado/"
        data = {
            'ruta_externa': str(ruta_externa),
            'tipo': tipo
        }
        response = requests.post(url, json=data, timeout=TIMEOUT)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error al marcar documento {documento_id} como descargado: {str(e)}")
        return False


def hacer_respaldo(archivo_origen, carpeta_backup):
    """
    Hace una copia de respaldo del archivo.
    
    Args:
        archivo_origen: Path del archivo original
        carpeta_backup: Carpeta donde guardar el respaldo
    """
    try:
        destino_backup = carpeta_backup / archivo_origen.name
        
        # Solo hacer respaldo si no existe
        if not destino_backup.exists():
            carpeta_backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo_origen, destino_backup)
            logger.info(f"✓ Respaldo creado: {destino_backup}")
            return True
        else:
            logger.debug(f"Respaldo ya existe: {destino_backup}")
            return False
    except Exception as e:
        logger.error(f"Error al crear respaldo de {archivo_origen}: {str(e)}")
        return False


def main():
    """Función principal del script."""
    logger.info("=" * 60)
    logger.info("Iniciando descarga de archivos desde Render")
    logger.info(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Obtener la lista de archivos pendientes
        logger.info(f"Consultando: {URL_LISTAR}")
        response = requests.get(URL_LISTAR, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success', False):
            logger.error(f"Error en la respuesta: {data.get('error', 'Error desconocido')}")
            return
        
        archivos = data.get('archivos', [])
        total = len(archivos)
        
        logger.info(f"Archivos pendientes encontrados: {total}")
        logger.info("-" * 60)
        
        if total == 0:
            logger.info("No hay archivos pendientes de descargar.")
            return
        
        # Estadísticas
        descargados = 0
        errores = 0
        ya_existian = 0
        
        # Procesar cada archivo
        for idx, doc in enumerate(archivos, 1):
            nombre_archivo = doc['nombre']
            url_archivo = doc['url']
            doc_id = doc['id']
            tipo = doc.get('tipo', 'expediente')
            nombre_documento = doc.get('nombre_documento', nombre_archivo)
            
            logger.info(f"[{idx}/{total}] Procesando: {nombre_documento}")
            
            # Construir ruta de destino
            # Organizar por tipo de documento y nombre
            if tipo == 'expediente':
                expediente_numero = doc.get('expediente_numero', 'sin_expediente')
                # Crear subdirectorio por expediente
                destino = BASE_PC / expediente_numero / nombre_archivo
            else:
                destino = BASE_PC / 'documentos' / nombre_archivo
            
            # Verificar si el archivo ya existe
            if destino.exists():
                logger.info(f"  ⏭ Archivo ya existe: {destino}")
                ya_existian += 1
                
                # Aunque exista, marcar como descargado para no intentarlo de nuevo
                if marcar_descargado(doc_id, destino, tipo):
                    logger.info(f"  ✓ Marcado como descargado en la base de datos")
                continue
            
            # Descargar el archivo
            logger.info(f"  ⬇ Descargando desde: {url_archivo}")
            if descargar_archivo(url_archivo, destino):
                logger.info(f"  ✓ Descargado: {destino}")
                descargados += 1
                
                # Hacer respaldo
                hacer_respaldo(destino, BACKUP)
                
                # Marcar como descargado en Django
                if marcar_descargado(doc_id, destino, tipo):
                    logger.info(f"  ✓ Marcado como descargado en la base de datos")
                else:
                    logger.warning(f"  ⚠ Descargado pero no se pudo marcar en la base de datos")
            else:
                logger.error(f"  ✗ Error al descargar: {nombre_archivo}")
                errores += 1
            
            logger.info("-" * 60)
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("RESUMEN DE DESCARGA")
        logger.info("=" * 60)
        logger.info(f"Total de archivos: {total}")
        logger.info(f"Descargados: {descargados}")
        logger.info(f"Ya existían: {ya_existian}")
        logger.info(f"Errores: {errores}")
        logger.info("=" * 60)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

