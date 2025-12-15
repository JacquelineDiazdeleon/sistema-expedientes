# Guía Completa de Instalación - Sistema de Escaneo HP ScanJet Pro 2600 f1

Esta guía te llevará paso a paso para configurar el sistema de escaneo automático usando NAPS2 y Django.

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de Drivers HP](#instalación-de-drivers-hp)
3. [Instalación de NAPS2](#instalación-de-naps2)
4. [Configuración de NAPS2](#configuración-de-naps2)
5. [Instalación del Servicio de Escaneo](#instalación-del-servicio-de-escaneo)
6. [Configuración de Django](#configuración-de-django)
7. [Instalación como Servicio Windows](#instalación-como-servicio-windows)
8. [Pruebas y Verificación](#pruebas-y-verificación)
9. [Solución de Problemas](#solución-de-problemas)

---

## 1. Requisitos Previos

### Hardware
- ✅ HP ScanJet Pro 2600 f1 conectado y encendido
- ✅ Computadora con Windows 10/11
- ✅ Conexión USB o red al escáner

### Software
- ✅ Python 3.10 o superior instalado
- ✅ Django ejecutándose localmente
- ✅ Acceso de administrador a Windows

---

## 2. Instalación de Drivers HP

### Paso 1: Descargar Drivers
1. Ve a la página oficial de HP Support: https://support.hp.com
2. Busca "HP ScanJet Pro 2600 f1"
3. Descarga el paquete de drivers **Full Feature** (NO Basic)

### Paso 2: Instalar Drivers
1. Ejecuta el instalador descargado
2. Sigue las instrucciones del asistente
3. **IMPORTANTE**: Durante la instalación, asegúrate de seleccionar:
   - ✅ **Full Feature Software**
   - ✅ **TWAIN Driver**
   - ✅ **WIA Driver** (opcional pero recomendado)

### Paso 3: Verificar Instalación
1. Abre **Panel de Control** → **Dispositivos e Impresoras**
2. Deberías ver tu HP ScanJet Pro 2600 f1 listado
3. Haz clic derecho → **Propiedades del Escáner** → Verifica que esté funcionando

### Paso 4: Probar con HP Scan
1. Abre la aplicación **HP Scan** (debería estar instalada)
2. Intenta hacer un escaneo de prueba con el ADF (alimentador automático)
3. Verifica que:
   - ✅ El escáner detecta los documentos en el ADF
   - ✅ El escaneo funciona correctamente
   - ✅ La calidad es adecuada

---

## 3. Instalación de NAPS2

### Paso 1: Descargar NAPS2
1. Ve a https://naps2.com
2. Descarga la versión más reciente (Windows x64)
3. El archivo se llamará algo como `naps2-7.x.x-win-x64.exe`

### Paso 2: Instalar NAPS2
1. Ejecuta el instalador
2. Sigue las instrucciones (instalación estándar)
3. **IMPORTANTE**: Durante la instalación:
   - ✅ Acepta instalar para todos los usuarios (recomendado)
   - ✅ Marca la opción de instalar componentes adicionales si se ofrece

### Paso 3: Verificar Instalación
1. Abre **NAPS2** desde el menú de inicio
2. Verifica que detecte tu escáner HP
3. Deberías ver tu escáner en la lista de dispositivos disponibles

### Paso 4: Ubicar el Ejecutable CLI
1. El ejecutable CLI estará en: `C:\Program Files\NAPS2\NAPS2.Console.exe`
2. Si instalaste en otra ubicación, verifica la ruta
3. **Anota esta ruta** - la necesitarás para configurar el servicio

---

## 4. Configuración de NAPS2

### Crear el Perfil de Escaneo

1. **Abrir NAPS2 GUI**
   - Inicia NAPS2 desde el menú de inicio

2. **Crear Nuevo Perfil**
   - Ve a **Profiles** → **New Profile**
   - Nombre del perfil: `HP_ADF_300`
   - Descripción: `HP ScanJet Pro 2600 f1 - ADF 300 DPI`

3. **Configurar Fuente de Documentos**
   - En **Document Source**, selecciona tu **HP ScanJet Pro 2600 f1**
   - **IMPORTANTE**: Selecciona **Feeder (ADF)** o **Automatic Document Feeder**
   - NO uses "Flatbed" (cama plana)

4. **Configurar Calidad**
   - **DPI**: `300`
   - **Color Mode**: `Color` o `Auto`
   - **File Format**: `PDF`

5. **Opciones Avanzadas (Recomendadas)**
   - ✅ **Auto deskew** (corrección automática de inclinación)
   - ✅ **Auto crop** (recorte automático)
   - ✅ **Remove blank pages** (eliminar páginas en blanco)
   - ✅ **Despeckle** (reducción de ruido)

6. **Guardar Perfil**
   - Haz clic en **Save** o **OK**
   - El perfil quedará guardado con el nombre `HP_ADF_300`

### Probar el Perfil
1. En NAPS2, selecciona el perfil `HP_ADF_300`
2. Coloca documentos en el ADF del escáner
3. Haz clic en **Scan**
4. Verifica que:
   - ✅ Escanea todas las páginas del ADF
   - ✅ Genera un PDF correctamente
   - ✅ La calidad es buena

---

## 5. Instalación del Servicio de Escaneo

### Paso 1: Crear Directorio
```powershell
# Abre PowerShell como Administrador
mkdir C:\scanner_service
cd C:\scanner_service
```

### Paso 2: Copiar Archivos
1. Copia el archivo `scan_service.py` a `C:\scanner_service\`
2. Verifica que el archivo esté ahí

### Paso 3: Instalar Dependencias Python
```powershell
# Instalar Flask y Requests
pip install flask requests
```

### Paso 4: Configurar Variables de Entorno (Opcional pero Recomendado)

Crea un archivo `.env` en `C:\scanner_service\.env`:
```env
SCANNER_UPLOAD_TOKEN=TU_TOKEN_SECRETO_AQUI
DJANGO_UPLOAD_URL=http://127.0.0.1:8000/expedientes/api/documentos/escaneado/
NAPS2_CLI=C:\Program Files\NAPS2\NAPS2.Console.exe
NAPS2_PROFILE=HP_ADF_300
```

**IMPORTANTE**: Para usar variables de entorno, necesitarás instalar `python-dotenv`:
```powershell
pip install python-dotenv
```

Y agregar al inicio de `scan_service.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Paso 5: Configurar scan_service.py

Abre `scan_service.py` y ajusta las siguientes constantes al inicio del archivo:

```python
# Token (debe coincidir con Django)
AUTH_TOKEN = "TU_TOKEN_SECRETO_AQUI"  # ⚠️ CAMBIAR ESTO

# Ruta de NAPS2 (verifica tu instalación)
NAPS2_CLI = r"C:\Program Files\NAPS2\NAPS2.Console.exe"

# Perfil NAPS2
NAPS2_PROFILE = "HP_ADF_300"

# URL de Django
DJANGO_UPLOAD_URL = "http://127.0.0.1:8000/expedientes/api/documentos/escaneado/"
```

### Paso 6: Probar el Servicio Manualmente

```powershell
cd C:\scanner_service
python scan_service.py
```

Deberías ver:
```
INFO - Servicio de escaneo iniciado correctamente
INFO - Escuchando en http://127.0.0.1:5001
```

**Mantén esta ventana abierta** y prueba desde otra terminal:

```powershell
# Probar health check
curl http://127.0.0.1:5001/health
```

Deberías recibir una respuesta JSON con el estado del servicio.

---

## 6. Configuración de Django

### Paso 1: Configurar Token en Django

Abre `digitalizacion/api_views.py` y busca:

```python
INTERNAL_UPLOAD_TOKEN = os.environ.get('SCANNER_UPLOAD_TOKEN', 'CAMBIA_POR_TU_TOKEN_SECRETO_AQUI')
```

**IMPORTANTE**: Cambia el token o configúralo como variable de entorno.

**Opción A: Variable de entorno (Recomendado)**
```powershell
# En Windows PowerShell (antes de ejecutar Django)
$env:SCANNER_UPLOAD_TOKEN = "TU_TOKEN_SECRETO_AQUI"
```

**Opción B: En settings.py**
Agrega a `sistema_digitalizacion/settings.py`:
```python
import os

SCANNER_UPLOAD_TOKEN = os.environ.get('SCANNER_UPLOAD_TOKEN', 'TU_TOKEN_SECRETO_AQUI')
```

Y actualiza `api_views.py`:
```python
from django.conf import settings
INTERNAL_UPLOAD_TOKEN = settings.SCANNER_UPLOAD_TOKEN
```

### Paso 2: Verificar URL

Verifica que en `digitalizacion/urls_expedientes.py` esté:

```python
path('api/documentos/escaneado/', subir_documento_escaneado_api, name='api_subir_documento_escaneado'),
```

### Paso 3: Crear Usuario del Servicio (Opcional)

El endpoint creará automáticamente un usuario `servicio_local` si no existe. Si prefieres crearlo manualmente:

```python
python manage.py shell
```

```python
from django.contrib.auth.models import User
User.objects.create_user(
    username='servicio_local',
    email='servicio@local',
    first_name='Servicio',
    last_name='Escáner Local',
    is_active=True,
    is_staff=False
)
```

### Paso 4: Probar el Endpoint

Con Django corriendo, prueba desde PowerShell:

```powershell
# Crear un archivo de prueba
echo "test" > test.pdf

# Probar upload (reemplaza TOKEN y IDs)
$token = "TU_TOKEN_AQUI"
$headers = @{
    "Authorization" = "Bearer $token"
}
$body = @{
    area = "1"
    expediente = "1"
    nombre_documento = "test"
    descripcion = "prueba"
}
$files = @{
    archivo = Get-Item test.pdf
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/expedientes/api/documentos/escaneado/" `
    -Method Post `
    -Headers $headers `
    -Form $body `
    -InFile test.pdf
```

---

## 7. Instalación como Servicio Windows

### Usando NSSM (Recomendado)

#### Paso 1: Descargar NSSM
1. Ve a https://nssm.cc/download
2. Descarga la versión 2.24 o superior (64-bit)
3. Extrae el archivo ZIP

#### Paso 2: Instalar el Servicio
```powershell
# Abre PowerShell como Administrador
cd C:\nssm\win64  # o donde extrajiste NSSM

# Instalar servicio
.\nssm.exe install scanner_service
```

Se abrirá una ventana GUI. Configura:

**Tab: Application**
- **Path**: `C:\Python310\python.exe` (ajusta según tu instalación)
- **Startup directory**: `C:\scanner_service`
- **Arguments**: `scan_service.py`

**Tab: Details**
- **Display name**: `Scanner Service`
- **Description**: `Servicio de escaneo automático con NAPS2`

**Tab: Log on**
- Selecciona **This account**
- Usa una cuenta de servicio o tu cuenta de usuario con permisos

**Tab: Dependencies**
- Puedes dejar vacío

**Tab: Process**
- ✅ **App exit action**: Restart application
- **Restart delay**: 5000 ms

#### Paso 3: Configurar Logs (Opcional)

**Tab: I/O**
- **Input (stdin)**: `C:\scanner_service\logs\stdin.log`
- **Output (stdout)**: `C:\scanner_service\logs\stdout.log`
- **Error (stderr)**: `C:\scanner_service\logs\stderr.log`

Crea el directorio de logs:
```powershell
mkdir C:\scanner_service\logs
```

#### Paso 4: Iniciar el Servicio
```powershell
# Iniciar servicio
.\nssm.exe start scanner_service

# Verificar estado
.\nssm.exe status scanner_service
```

#### Paso 5: Configurar Arranque Automático
El servicio ya debería estar configurado para arrancar automáticamente. Si no:

```powershell
# Ver configuración
.\nssm.exe get scanner_service Start SERVICE_AUTO_START
```

Si no está en automático:
```powershell
.\nssm.exe set scanner_service Start SERVICE_AUTO_START
```

### Comandos Útiles de NSSM

```powershell
# Ver estado
nssm status scanner_service

# Iniciar
nssm start scanner_service

# Detener
nssm stop scanner_service

# Reiniciar
nssm restart scanner_service

# Ver logs en tiempo real
nssm tail scanner_service stdout
```

---

## 8. Pruebas y Verificación

### Prueba 1: Verificar Servicio Local
```powershell
curl http://127.0.0.1:5001/health
```

Respuesta esperada:
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

### Prueba 2: Verificar Endpoint Django
1. Abre tu aplicación Django en el navegador
2. Ve a un expediente existente
3. Haz clic en "Subir Documento" de cualquier área
4. Deberías ver el botón **"Escanear Documento con HP ScanJet"**

### Prueba 3: Escaneo Completo
1. Abre un expediente en Django
2. Haz clic en "Subir Documento" de un área
3. Completa el nombre del documento
4. Coloca documentos en el ADF del escáner
5. Haz clic en **"Escanear Documento con HP ScanJet"**
6. Espera mientras:
   - El servicio escanea los documentos
   - Sube el PDF a Django
   - Se crea el registro en la base de datos
7. Verifica que:
   - ✅ El documento aparece en la lista
   - ✅ Puedes descargarlo
   - ✅ El PDF tiene buena calidad

---

## 9. Solución de Problemas

### Problema: "NAPS2 no encontrado"
**Solución:**
- Verifica que NAPS2 esté instalado
- Ajusta `NAPS2_CLI` en `scan_service.py` con la ruta correcta
- Verifica permisos de ejecución

### Problema: "Error al invocar NAPS2"
**Solución:**
- Verifica que el escáner esté encendido y conectado
- Prueba escanear manualmente desde NAPS2 GUI
- Verifica que el perfil `HP_ADF_300` exista y esté configurado correctamente
- Revisa los logs del servicio: `C:\scanner_service\scanner_service.log`

### Problema: "Unauthorized - invalid token"
**Solución:**
- Verifica que el token en `scan_service.py` coincida con el de Django
- Verifica que el token esté configurado en ambos lugares
- Revisa las variables de entorno si las estás usando

### Problema: "Error de conexión con el servicio de escaneo"
**Solución:**
- Verifica que el servicio esté corriendo: `curl http://127.0.0.1:5001/health`
- Verifica que no haya firewall bloqueando el puerto 5001
- Verifica que el servicio esté escuchando en `127.0.0.1` (no `0.0.0.0`)

### Problema: "Área inválida" o "Expediente inválido"
**Solución:**
- Verifica que los IDs de área y expediente sean correctos
- Verifica que el área esté activa en Django
- Revisa los logs de Django para más detalles

### Problema: El servicio no inicia automáticamente
**Solución:**
- Verifica la configuración de NSSM
- Revisa los logs de Windows Event Viewer
- Verifica permisos de la cuenta del servicio

### Problema: Archivos temporales no se eliminan
**Solución:**
- Verifica permisos de escritura en `C:\Users\[Usuario]\AppData\Local\Temp`
- Revisa los logs del servicio para errores de eliminación
- Verifica que el servicio tenga permisos suficientes

---

## 🔒 Seguridad

### Tokens
- ✅ **NUNCA** compartas tu token
- ✅ Usa tokens fuertes (mínimo 32 caracteres aleatorios)
- ✅ Considera rotar tokens periódicamente
- ✅ No commits el token en repositorios públicos

### Red
- ✅ El servicio solo escucha en `127.0.0.1` (localhost)
- ✅ No expongas el puerto 5001 a la red externa
- ✅ Usa HTTPS en producción si el servicio está en otra máquina

### Permisos
- ✅ El servicio solo necesita permisos de lectura/escritura en directorios temporales
- ✅ No necesita permisos de administrador para funcionar

---

## 📝 Notas Finales

- El servicio elimina automáticamente todos los archivos temporales después de subirlos
- Los logs se guardan en `C:\scanner_service\scanner_service.log`
- El servicio puede reiniciarse automáticamente si falla (configurado en NSSM)
- Puedes ver el estado del servicio con: `nssm status scanner_service`

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `C:\scanner_service\scanner_service.log`
2. Revisa los logs de Django: `debug.log`
3. Verifica el estado del servicio: `nssm status scanner_service`
4. Verifica la conexión: `curl http://127.0.0.1:5001/health`

¡Buena suerte con tu sistema de escaneo! 🎉

