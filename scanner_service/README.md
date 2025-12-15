# Servicio de Escaneo Local - HP ScanJet Pro 2600 f1

Servicio local que permite escanear documentos desde Django usando NAPS2 y HP ScanJet Pro 2600 f1.

## 📁 Archivos

- `scan_service.py` - Servicio Flask que maneja el escaneo
- `INSTALACION.md` - Guía completa paso a paso de instalación
- `config_helper.py` - Script para verificar configuración
- `generate_token.py` - Script para generar tokens seguros

## 🚀 Inicio Rápido

1. **Instalar dependencias:**
   ```powershell
   pip install flask requests
   ```

2. **Configurar `scan_service.py`:**
   - Ajusta `AUTH_TOKEN` (debe coincidir con Django)
   - Ajusta `NAPS2_CLI` si es necesario
   - Ajusta `DJANGO_UPLOAD_URL` si Django está en otro puerto

3. **Ejecutar manualmente:**
   ```powershell
   python scan_service.py
   ```

4. **Verificar:**
   ```powershell
   curl http://127.0.0.1:5001/health
   ```

## 🔧 Configuración

### Variables de Entorno (Opcional)

Puedes usar variables de entorno en lugar de modificar el código:

```powershell
$env:SCANNER_UPLOAD_TOKEN = "tu_token_aqui"
$env:NAPS2_CLI = "C:\Program Files\NAPS2\NAPS2.Console.exe"
$env:NAPS2_PROFILE = "HP_ADF_300"
$env:DJANGO_UPLOAD_URL = "http://127.0.0.1:8000/expedientes/api/documentos/escaneado/"
```

### Archivo .env

Crea `C:\scanner_service\.env`:

```env
SCANNER_UPLOAD_TOKEN=tu_token_secreto_aqui
DJANGO_UPLOAD_URL=http://127.0.0.1:8000/expedientes/api/documentos/escaneado/
NAPS2_CLI=C:\Program Files\NAPS2\NAPS2.Console.exe
NAPS2_PROFILE=HP_ADF_300
```

Y en `scan_service.py` agrega al inicio:

```python
from dotenv import load_dotenv
load_dotenv()
```

Luego instala: `pip install python-dotenv`

## 📋 Endpoints

### GET `/`
Información del servicio

### GET `/health`
Verifica el estado del servicio y configuración

**Respuesta:**
```json
{
  "status": "ok",
  "service": "scanner_service",
  "naps2_path": "C:\\Program Files\\NAPS2\\NAPS2.Console.exe",
  "naps2_installed": true,
  "profile": "HP_ADF_300",
  "django_url": "http://127.0.0.1:8000/expedientes/api/documentos/escaneado/"
}
```

### POST `/scan`
Inicia el proceso de escaneo

**Request:**
```json
{
  "area": 1,
  "expediente": 5,
  "nombre_documento": "Documento escaneado",
  "descripcion": "Descripción opcional"
}
```

**Response (éxito):**
```json
{
  "status": "ok",
  "django": {
    "success": true,
    "documento_id": 123,
    "path": "expedientes/5/documentos/documento_123.pdf",
    "nombre": "Documento escaneado",
    "expediente_id": 5,
    "area_id": 1
  },
  "msg": "Escaneo completado y subido correctamente"
}
```

**Response (error):**
```json
{
  "status": "error",
  "msg": "Mensaje de error",
  "detail": "Detalles adicionales"
}
```

## 🛠️ Scripts Helper

### config_helper.py
Verifica que toda la configuración esté correcta:
```powershell
python config_helper.py
```

### generate_token.py
Genera un token seguro aleatorio:
```powershell
python generate_token.py
```

## 📝 Logs

Los logs se guardan en:
- `scanner_service.log` - Log del servicio
- `logs/stdout.log` - Salida estándar (si usas NSSM)
- `logs/stderr.log` - Errores (si usas NSSM)

## 🔒 Seguridad

- El servicio solo escucha en `127.0.0.1` (localhost)
- Requiere token Bearer para autenticación
- Los archivos temporales se eliminan automáticamente
- No almacena datos permanentes

## 📖 Ver También

- `INSTALACION.md` - Guía completa de instalación
- Documentación de Django sobre el endpoint

