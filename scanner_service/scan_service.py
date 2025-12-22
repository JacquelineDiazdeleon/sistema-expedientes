"""
Servicio local de escaneo con NAPS2 CLI para HP ScanJet Pro 2600 f1
Este servicio escanea documentos usando NAPS2 y los sube directamente a Django.

Requisitos:
- NAPS2 instalado: https://naps2.com
- Drivers HP ScanJet Pro 2600 f1 instalados
- Python 3.10+
- Dependencias: pip install flask requests

Uso:
    python scan_service.py

Para instalarlo como servicio Windows:
    Ver README_SCAN.md
"""

import os
import json
import tempfile
import subprocess
import requests
import time
import logging
import threading
import shutil
from pathlib import Path
from flask import Flask, request, jsonify
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Habilitar CORS para permitir peticiones desde el navegador
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Scanner-Service')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Manejar preflight OPTIONS requests
@app.route('/scan', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def handle_options():
    return '', 204

# ========== CONFIGURACIÓN ==========
# Cargar configuración desde config.json
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Carga la configuración desde config.json"""
    default_config = {
        "AUTH_TOKEN": "CAMBIA_POR_TU_TOKEN_SECRETO_AQUI",
        "DJANGO_BASE_URL": "http://127.0.0.1:8000",
        "ARCHIVO_FIELD_NAME": "documento",
        "NAPS2_CLI": r"C:\Program Files\NAPS2\NAPS2.Console.exe",
        "NAPS2_PROFILE": "HP_ADF_300",
        "SCAN_TIMEOUT": 180,
        "UPLOAD_TIMEOUT": 120
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Configuración cargada desde {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"Error al cargar config.json: {e}. Usando valores por defecto.")
    else:
        logger.warning(f"config.json no encontrado. Creando archivo de ejemplo...")
        # Crear archivo de ejemplo
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            logger.info(f"Archivo de ejemplo creado: {CONFIG_FILE}")
            logger.info("Por favor, edita config.json con tus valores reales")
        except Exception as e:
            logger.error(f"No se pudo crear config.json: {e}")
    
    return default_config

# Cargar configuración
config = load_config()

# Variables de configuración
AUTH_TOKEN = config.get("AUTH_TOKEN", "CAMBIA_POR_TU_TOKEN_SECRETO_AQUI")
DJANGO_BASE_URL = config.get("DJANGO_BASE_URL", "http://127.0.0.1:8000")
ARCHIVO_FIELD_NAME = config.get("ARCHIVO_FIELD_NAME", "documento")
NAPS2_CLI = config.get("NAPS2_CLI", r"C:\Program Files\NAPS2\NAPS2.Console.exe")
NAPS2_PROFILE = config.get("NAPS2_PROFILE", "HP_ADF_300")
SCAN_TIMEOUT = int(config.get("SCAN_TIMEOUT", 180))
UPLOAD_TIMEOUT = int(config.get("UPLOAD_TIMEOUT", 120))

# Carpetas para guardar expedientes y respaldo
CARPETA_PRINCIPAL = Path(config.get("CARPETA_PRINCIPAL", r"C:\servidor\Expedientes"))
CARPETA_RESPALDO = Path(config.get("CARPETA_RESPALDO", r"D:\Resp\Respaldo_SistemaDigitalizacion"))
MAX_ARCHIVOS_PRINCIPAL = int(config.get("MAX_ARCHIVOS_PRINCIPAL", 1000))  # Límite de archivos antes de limpiar

# Crear carpetas si no existen
CARPETA_PRINCIPAL.mkdir(parents=True, exist_ok=True)
CARPETA_RESPALDO.mkdir(parents=True, exist_ok=True)

# ===================================


def verificar_naps2():
    """Verifica que NAPS2 esté instalado y accesible"""
    if not os.path.exists(NAPS2_CLI):
        raise FileNotFoundError(
            f"NAPS2 no encontrado en: {NAPS2_CLI}\n"
            f"Verifica la instalación de NAPS2 o ajusta NAPS2_CLI en config.json."
        )
    logger.info(f"NAPS2 encontrado en: {NAPS2_CLI}")


def guardar_archivo_local(archivo_origen, nombre_archivo, expediente_id=None):
    """
    Guarda el archivo escaneado en la carpeta principal y crea un respaldo.
    
    Args:
        archivo_origen: Ruta del archivo escaneado
        nombre_archivo: Nombre del archivo (sin extensión)
        expediente_id: ID del expediente (opcional, para organizar por carpeta)
    
    Returns:
        tuple: (ruta_principal, ruta_respaldo) o (None, None) si hay error
    """
    try:
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_completo = f"{nombre_archivo}_{timestamp}.pdf"
        
        # Si hay expediente_id, crear subdirectorio por expediente
        if expediente_id:
            carpeta_expediente = CARPETA_PRINCIPAL / f"EXP-{expediente_id}"
            carpeta_expediente.mkdir(parents=True, exist_ok=True)
            ruta_principal = carpeta_expediente / nombre_completo
        else:
            ruta_principal = CARPETA_PRINCIPAL / nombre_completo
        
        # Copiar a carpeta principal
        shutil.copy2(archivo_origen, ruta_principal)
        logger.info(f"✓ Archivo guardado en carpeta principal: {ruta_principal}")
        
        # Crear respaldo
        ruta_respaldo = CARPETA_RESPALDO / nombre_completo
        shutil.copy2(archivo_origen, ruta_respaldo)
        logger.info(f"✓ Respaldo creado: {ruta_respaldo}")
        
        # Limpiar archivos antiguos si hay demasiados
        limpiar_archivos_antiguos(CARPETA_PRINCIPAL, MAX_ARCHIVOS_PRINCIPAL)
        
        return str(ruta_principal), str(ruta_respaldo)
        
    except Exception as e:
        logger.error(f"Error al guardar archivo local: {str(e)}")
        return None, None


def limpiar_archivos_antiguos(carpeta, max_archivos):
    """
    Elimina los archivos más antiguos si hay más de max_archivos.
    
    Args:
        carpeta: Path de la carpeta a limpiar
        max_archivos: Número máximo de archivos permitidos
    """
    try:
        # Obtener todos los archivos con su fecha de modificación
        archivos = []
        for archivo in carpeta.rglob("*.pdf"):
            if archivo.is_file():
                archivos.append((archivo.stat().st_mtime, archivo))
        
        # Si hay más archivos de los permitidos, eliminar los más antiguos
        if len(archivos) > max_archivos:
            archivos.sort()  # Ordenar por fecha (más antiguos primero)
            archivos_a_eliminar = archivos[:len(archivos) - max_archivos]
            
            for _, archivo in archivos_a_eliminar:
                try:
                    archivo.unlink()
                    logger.info(f"✓ Archivo antiguo eliminado: {archivo.name}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar {archivo}: {e}")
                    
    except Exception as e:
        logger.warning(f"Error al limpiar archivos antiguos: {e}")


def run_naps2_scan(output_path, duplex=False):
    """
    Ejecuta NAPS2 para escanear usando el perfil y generar el PDF en output_path.
    
    Args:
        output_path: Ruta donde se guardará el PDF escaneado
        duplex: Si True, escanea por ambos lados de la página
        
    Raises:
        subprocess.CalledProcessError: Si NAPS2 falla
        FileNotFoundError: Si NAPS2 no está instalado
    """
    scan_mode = "dúplex (ambos lados)" if duplex else "simplex (un lado)"
    logger.info(f"Iniciando escaneo con perfil: {NAPS2_PROFILE}, modo: {scan_mode}")
    logger.info(f"Salida: {output_path}")
    
    # Comando NAPS2 CLI
    # --profile: nombre del perfil (el perfil ya tiene configurado el alimentador ADF)
    # -o: archivo de salida
    # --force: forzar escaneo sin confirmación
    # --source: fuente del papel (feeder, duplex, glass)
    cmd = [
        NAPS2_CLI,
        "--profile", NAPS2_PROFILE,
        "-o", output_path,
        "--force"
    ]
    
    # Agregar opción de dúplex si está habilitada
    if duplex:
        cmd.extend(["--source", "duplex"])
        logger.info("Modo dúplex activado - escaneando ambos lados")
    
    logger.info(f"Ejecutando: {' '.join(cmd)}")
    
    try:
        # Ejecutar NAPS2 con timeout
        result = subprocess.run(
            cmd,
            timeout=SCAN_TIMEOUT,
            capture_output=True,
            text=True,
            check=False  # No lanzar excepción automáticamente
        )
        
        # Log de salida para debug
        if result.stdout:
            logger.info(f"NAPS2 stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"NAPS2 stderr: {result.stderr}")
        
        logger.info(f"NAPS2 código de salida: {result.returncode}")
        
        # Verificar que el archivo se creó
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"NAPS2 no generó el archivo: {output_path}")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"PDF generado: {output_path} ({file_size} bytes)")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout al escanear (>{SCAN_TIMEOUT}s)")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar NAPS2: {e}")
        logger.error(f"stderr: {e.stderr}")
        logger.error(f"stdout: {e.stdout}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al escanear: {e}")
        raise


@app.route("/scan", methods=["POST"])
def scan_route():
    """
    Endpoint que recibe la solicitud de escaneo desde el navegador.
    
    Espera JSON con:
      - expediente_id (int): ID del expediente
      - etapa (str): Etapa del expediente
      - area_id (int): ID del área
      - nombre_documento (string): Nombre del documento
      - descripcion (string, opcional): Descripción del documento
    
    Retorna JSON con status "ok" o "error"
    """
    try:
        # Obtener datos JSON
        data = request.get_json() or {}
        
        expediente_id = data.get("expediente_id")
        etapa = data.get("etapa")
        area_id = data.get("area_id")
        nombre_documento = data.get("nombre_documento", "").strip()
        descripcion = data.get("descripcion", "").strip()
        duplex = data.get("duplex", False)  # Escaneo dúplex (dos lados)
        
        # Validar campos requeridos
        if not expediente_id or not etapa or not area_id:
            logger.warning("Faltan campos requeridos")
            return jsonify({
                "status": "error",
                "msg": "Faltan campos requeridos: expediente_id, etapa y area_id son obligatorios"
            }), 400
        
        duplex_str = " (dúplex)" if duplex else ""
        logger.info(f"Recibida solicitud de escaneo{duplex_str}: expediente={expediente_id}, etapa={etapa}, área={area_id}, nombre={nombre_documento}")
        
        # Crear directorio temporal
        tmpdir = tempfile.mkdtemp(prefix="scan_")
        out_pdf = os.path.join(tmpdir, "scanned.pdf")
        
        try:
            # 1) Ejecutar NAPS2 para escanear ADF y crear PDF
            logger.info("Iniciando escaneo con NAPS2...")
            run_naps2_scan(out_pdf, duplex=duplex)
            
            # 2) Construir URL de Django usando la misma URL que el formulario
            django_url = f"{DJANGO_BASE_URL}/expedientes/{expediente_id}/etapa/{etapa}/subir-documento/"
            logger.info(f"Subiendo PDF a Django: {django_url}")
            
            # 3) Subir PDF a Django usando la misma estructura que el formulario HTML
            with open(out_pdf, "rb") as f:
                # Usar el mismo nombre de campo que el formulario HTML
                files = {
                    ARCHIVO_FIELD_NAME: (f"{nombre_documento}.pdf", f, "application/pdf")
                }
                
                # Datos POST que espera la vista subir_documento
                data_post = {
                    "area_id": str(area_id),
                    "nombre_documento": nombre_documento,
                    "descripcion": descripcion
                }
                
                # Headers con token de autenticación
                headers = {
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "X-Scanner-Service": "true"  # Header adicional para identificar que viene del servicio
                }
                
                # Hacer POST a Django
                resp = requests.post(
                    django_url,
                    files=files,
                    data=data_post,
                    headers=headers,
                    timeout=UPLOAD_TIMEOUT
                )
                
                resp.raise_for_status()
                
                # Intentar parsear JSON si la respuesta es JSON
                try:
                    resp_json = resp.json()
                    logger.info(f"Documento subido exitosamente a Django: {resp_json}")
                except:
                    resp_json = {"message": "Documento subido exitosamente"}
                    logger.info("Documento subido exitosamente a Django (respuesta no JSON)")
            
            # 4) Guardar copia local y crear respaldo
            logger.info("Guardando copia local y creando respaldo...")
            ruta_principal, ruta_respaldo = guardar_archivo_local(
                out_pdf,
                nombre_documento,
                expediente_id
            )
            
            if ruta_principal:
                logger.info(f"✓ Archivo guardado localmente: {ruta_principal}")
                logger.info(f"✓ Respaldo creado: {ruta_respaldo}")
            else:
                logger.warning("⚠ No se pudo guardar copia local (el archivo ya está en Django)")
            
            return jsonify({
                "status": "ok",
                "django": resp_json,
                "ruta_local": ruta_principal,
                "ruta_respaldo": ruta_respaldo,
                "msg": "Escaneo completado, subido a Django y guardado localmente"
            }), 200
            
        except subprocess.CalledProcessError as cpe:
            error_msg = f"Error al invocar NAPS2: {str(cpe)}"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "msg": error_msg,
                "detail": str(cpe)
            }), 500
            
        except requests.exceptions.RequestException as re:
            error_msg = f"Error al subir a Django: {str(re)}"
            logger.error(error_msg)
            if hasattr(re, 'response') and re.response is not None:
                try:
                    error_detail = re.response.json()
                    logger.error(f"Detalle del error Django: {error_detail}")
                except:
                    logger.error(f"Respuesta Django: {re.response.text}")
            return jsonify({
                "status": "error",
                "msg": error_msg,
                "detail": str(re)
            }), 500
            
        finally:
            # 4) Limpiar archivos temporales (IMPORTANTE: no dejar copias)
            try:
                if os.path.exists(out_pdf):
                    os.remove(out_pdf)
                    logger.debug(f"Archivo temporal eliminado: {out_pdf}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {out_pdf}: {e}")
            
            try:
                if os.path.exists(tmpdir):
                    os.rmdir(tmpdir)
                    logger.debug(f"Directorio temporal eliminado: {tmpdir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal {tmpdir}: {e}")
        
    except Exception as e:
        logger.error(f"Error inesperado en scan_route: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "msg": f"Error inesperado: {str(e)}"
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud para verificar que el servicio está corriendo"""
    try:
        verificar_naps2()
        return jsonify({
            "status": "ok",
            "service": "scanner_service",
            "naps2_path": NAPS2_CLI,
            "naps2_installed": os.path.exists(NAPS2_CLI),
            "profile": NAPS2_PROFILE,
            "django_url": DJANGO_BASE_URL,
            "archivo_field": ARCHIVO_FIELD_NAME
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/", methods=["GET"])
def index():
    """Página de información del servicio"""
    return jsonify({
        "service": "Scanner Service",
        "version": "2.0.0",
        "endpoints": {
            "/scan": "POST - Escanear documento y subir a Django",
            "/health": "GET - Verificar estado del servicio"
        },
        "config": {
            "naps2_profile": NAPS2_PROFILE,
            "django_url": DJANGO_BASE_URL,
            "archivo_field": ARCHIVO_FIELD_NAME
        },
        "remote_scanning": "enabled"
    }), 200


# ========== ESCANEO REMOTO (POLLING) ==========

# Control del hilo de polling
polling_active = True
polling_interval = 5  # segundos entre cada consulta
is_scanning = False  # Flag para evitar escaneos simultáneos


def procesar_solicitud_remota(solicitud):
    """
    Procesa una solicitud de escaneo remota.
    
    Args:
        solicitud: dict con los datos de la solicitud
    """
    global is_scanning
    
    solicitud_id = solicitud.get('id')
    expediente_id = solicitud.get('expediente_id')
    area_id = solicitud.get('area_id')
    nombre_documento = solicitud.get('nombre_documento', f"scan_{int(time.time())}")
    descripcion = solicitud.get('descripcion', '')
    duplex = solicitud.get('duplex', False)
    
    logger.info(f"[REMOTO] Procesando solicitud #{solicitud_id}: {nombre_documento}")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1) Marcar como "procesando"
        resp = requests.post(
            f"{DJANGO_BASE_URL}/scanner/solicitud/{solicitud_id}/procesando/",
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        logger.info(f"[REMOTO] Solicitud #{solicitud_id} marcada como procesando")
        
        # 2) Crear directorio temporal y escanear
        tmpdir = tempfile.mkdtemp(prefix="scan_remote_")
        out_pdf = os.path.join(tmpdir, "scanned.pdf")
        
        try:
            is_scanning = True
            logger.info(f"[REMOTO] Iniciando escaneo para solicitud #{solicitud_id}...")
            run_naps2_scan(out_pdf, duplex=duplex)
            
            # 3) Subir el documento a Django
            # Usamos el endpoint normal de subir documento por etapa
            # Pero primero necesitamos obtener la etapa del expediente
            # Por simplicidad, usamos el endpoint que ya conocemos
            
            django_url = f"{DJANGO_BASE_URL}/expedientes/{expediente_id}/etapa/inicial/subir-documento/"
            logger.info(f"[REMOTO] Subiendo PDF a Django: {django_url}")
            
            with open(out_pdf, "rb") as f:
                files = {
                    ARCHIVO_FIELD_NAME: (f"{nombre_documento}.pdf", f, "application/pdf")
                }
                
                data_post = {
                    "area_id": str(area_id),
                    "nombre_documento": nombre_documento,
                    "descripcion": descripcion
                }
                
                upload_headers = {
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "X-Scanner-Service": "true",
                    "X-Remote-Scan": "true"
                }
                
                resp_upload = requests.post(
                    django_url,
                    files=files,
                    data=data_post,
                    headers=upload_headers,
                    timeout=UPLOAD_TIMEOUT
                )
                
                resp_upload.raise_for_status()
                
                try:
                    resp_json = resp_upload.json()
                    documento_id = resp_json.get('documento_id')
                except:
                    resp_json = {}
                    documento_id = None
                
                logger.info(f"[REMOTO] Documento subido exitosamente para solicitud #{solicitud_id}")
            
            # 4) Guardar copia local y crear respaldo
            logger.info(f"[REMOTO] Guardando copia local y creando respaldo...")
            ruta_principal, ruta_respaldo = guardar_archivo_local(
                out_pdf,
                nombre_documento,
                expediente_id
            )
            
            if ruta_principal:
                logger.info(f"[REMOTO] ✓ Archivo guardado localmente: {ruta_principal}")
                logger.info(f"[REMOTO] ✓ Respaldo creado: {ruta_respaldo}")
            
            # 5) Marcar como completada
            resp_complete = requests.post(
                f"{DJANGO_BASE_URL}/scanner/solicitud/{solicitud_id}/completado/",
                headers=headers,
                json={"documento_id": documento_id},
                timeout=30
            )
            resp_complete.raise_for_status()
            logger.info(f"[REMOTO] ✓ Solicitud #{solicitud_id} completada exitosamente")
            
        except Exception as scan_error:
            # Marcar como error
            logger.error(f"[REMOTO] Error en solicitud #{solicitud_id}: {str(scan_error)}")
            try:
                requests.post(
                    f"{DJANGO_BASE_URL}/scanner/solicitud/{solicitud_id}/error/",
                    headers=headers,
                    json={"error": str(scan_error)},
                    timeout=30
                )
            except:
                pass
                
        finally:
            is_scanning = False
            # Limpiar archivos temporales
            try:
                if os.path.exists(out_pdf):
                    os.remove(out_pdf)
                if os.path.exists(tmpdir):
                    os.rmdir(tmpdir)
            except:
                pass
                
    except Exception as e:
        is_scanning = False
        logger.error(f"[REMOTO] Error al procesar solicitud #{solicitud_id}: {str(e)}")


def polling_solicitudes():
    """
    Hilo que consulta periódicamente las solicitudes pendientes en Render.
    """
    global polling_active, is_scanning
    
    logger.info("[POLLING] Iniciando servicio de polling para solicitudes remotas...")
    logger.info(f"[POLLING] Intervalo: {polling_interval} segundos")
    logger.info(f"[POLLING] Servidor: {DJANGO_BASE_URL}")
    
    while polling_active:
        try:
            # No consultar si ya estamos escaneando
            if is_scanning:
                time.sleep(polling_interval)
                continue
            
            # Consultar solicitudes pendientes
            headers = {
                "Authorization": f"Bearer {AUTH_TOKEN}"
            }
            
            resp = requests.get(
                f"{DJANGO_BASE_URL}/scanner/solicitudes-pendientes/",
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                solicitudes = data.get('solicitudes', [])
                
                if solicitudes:
                    logger.info(f"[POLLING] Encontradas {len(solicitudes)} solicitudes pendientes")
                    
                    # Procesar la primera solicitud (una a la vez)
                    solicitud = solicitudes[0]
                    procesar_solicitud_remota(solicitud)
            else:
                # Solo loggear errores importantes, no cada polling
                if resp.status_code != 401:  # 401 es normal si no hay token
                    logger.debug(f"[POLLING] Respuesta del servidor: {resp.status_code}")
                    
        except requests.exceptions.ConnectionError:
            logger.debug("[POLLING] No hay conexión con el servidor. Reintentando...")
        except Exception as e:
            logger.debug(f"[POLLING] Error en polling: {str(e)}")
        
        # Esperar antes de la siguiente consulta
        time.sleep(polling_interval)
    
    logger.info("[POLLING] Servicio de polling detenido")


def iniciar_polling():
    """Inicia el hilo de polling en segundo plano"""
    thread = threading.Thread(target=polling_solicitudes, daemon=True)
    thread.start()
    logger.info("[POLLING] Hilo de polling iniciado")
    return thread


if __name__ == "__main__":
    # Verificar NAPS2 al iniciar
    try:
        verificar_naps2()
        logger.info("Servicio de escaneo iniciado correctamente")
        logger.info(f"NAPS2 Profile: {NAPS2_PROFILE}")
        logger.info(f"Django URL: {DJANGO_BASE_URL}")
        logger.info(f"Campo archivo: {ARCHIVO_FIELD_NAME}")
        
        # Obtener IP de la red local
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        logger.info(f"=" * 50)
        logger.info(f"Servicio de escaneo disponible en:")
        logger.info(f"  - Local:     http://127.0.0.1:5001")
        logger.info(f"  - Red local: http://{local_ip}:5001")
        logger.info(f"=" * 50)
        logger.info(f"Otros dispositivos pueden escanear usando: http://{local_ip}:5001")
        logger.info(f"")
        logger.info(f"[ESCANEO REMOTO HABILITADO]")
        logger.info(f"Otros dispositivos pueden solicitar escaneos desde la web.")
        logger.info(f"El servicio consultará {DJANGO_BASE_URL} cada {polling_interval} segundos.")
        logger.info(f"=" * 50)
        
    except FileNotFoundError as e:
        logger.error(f"Error de configuración: {e}")
        logger.error("Por favor, verifica la instalación de NAPS2 o ajusta NAPS2_CLI en config.json")
        exit(1)
    
    # Iniciar el servicio de polling para solicitudes remotas
    iniciar_polling()
    
    # Iniciar servidor Flask en todas las interfaces (accesible desde la red)
    app.run(host='0.0.0.0', port=5001, debug=False)
