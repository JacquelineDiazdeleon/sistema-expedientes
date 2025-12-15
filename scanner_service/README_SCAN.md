# 📖 Guía Completa de Instalación - Sistema de Escaneo Automático

Esta guía te llevará paso a paso para configurar el sistema de escaneo automático usando NAPS2, HP ScanJet Pro 2600 f1 y Django.

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de Programas](#instalación-de-programas)
3. [Configuración del Token](#configuración-del-token)
4. [Configuración de NAPS2](#configuración-de-naps2)
5. [Configuración del Servicio de Escaneo](#configuración-del-servicio-de-escaneo)
6. [Instalación como Servicio Windows con NSSM](#instalación-como-servicio-windows-con-nssm)
7. [Pruebas del Flujo Completo](#pruebas-del-flujo-completo)
8. [Solución de Problemas](#solución-de-problemas)

---

## 1. Requisitos Previos

### Hardware
- ✅ HP ScanJet Pro 2600 f1 conectado y encendido
- ✅ Computadora con Windows 10/11
- ✅ Conexión USB o red al escáner

### Software Necesario
- ✅ Python 3.10 o superior
- ✅ Django ejecutándose localmente
- ✅ Acceso de administrador a Windows

---

## 2. Instalación de Programas

### 2.1 Instalar Drivers HP ScanJet Pro 2600 f1

1. **Descargar Drivers**
   - Ve a https://support.hp.com
   - Busca "HP ScanJet Pro 2600 f1"
   - Descarga el paquete de drivers **Full Feature** (NO Basic)

2. **Instalar Drivers**
   - Ejecuta el instalador descargado
   - Durante la instalación, asegúrate de seleccionar:
     - ✅ **Full Feature Software**
     - ✅ **TWAIN Driver**
     - ✅ **WIA Driver** (opcional pero recomendado)

3. **Verificar Instalación**
   - Abre **Panel de Control** → **Dispositivos e Impresoras**
   - Deberías ver tu HP ScanJet Pro 2600 f1 listado
   - Haz clic derecho → **Propiedades del Escáner** → Verifica que esté funcionando

4. **Probar con HP Scan**
   - Abre la aplicación **HP Scan**
   - Intenta hacer un escaneo de prueba con el ADF (alimentador automático)
   - Verifica que el escáner detecta los documentos y escanea correctamente

### 2.2 Instalar NAPS2

1. **Descargar NAPS2**
   - Ve a https://naps2.com
   - Descarga la versión más reciente (Windows x64)
   - El archivo se llamará algo como `naps2-7.x.x-win-x64.exe`

2. **Instalar NAPS2**
   - Ejecuta el instalador
   - Sigue las instrucciones (instalación estándar)
   - **IMPORTANTE**: Acepta instalar para todos los usuarios (recomendado)

3. **Verificar Instalación**
   - Abre **NAPS2** desde el menú de inicio
   - Verifica que detecte tu escáner HP
   - Deberías ver tu escáner en la lista de dispositivos disponibles

4. **Ubicar el Ejecutable CLI**
   - El ejecutable CLI estará en: `C:\Program Files\NAPS2\NAPS2.Console.exe`
   - Si instalaste en otra ubicación, verifica la ruta
   - **Anota esta ruta** - la necesitarás para configurar el servicio

### 2.3 Instalar Python (si no está instalado)

1. **Descargar Python**
   - Ve a https://www.python.org/downloads/
   - Descarga Python 3.10 o superior
   - **IMPORTANTE**: Durante la instalación, marca la opción "Add Python to PATH"

2. **Verificar Instalación**
   ```powershell
   python --version
   ```
   Deberías ver algo como: `Python 3.10.x`

3. **Instalar Dependencias**
   ```powershell
   pip install flask requests
   ```

### 2.4 Instalar NSSM (para servicio Windows)

1. **Descargar NSSM**
   - Ve a https://nssm.cc/download
   - Descarga la versión 2.24 o superior (64-bit)
   - Extrae el archivo ZIP en `C:\nssm\`

2. **Verificar Instalación**
   ```powershell
   cd C:\nssm\win64
   .\nssm.exe
   ```
   Debería abrirse la GUI de NSSM

---

## 3. Configuración del Token

El token es una clave secreta que permite que el servicio de escaneo se comunique de forma segura con Django.

### 3.1 Generar Token Seguro

```powershell
cd C:\scanner_service
python generate_token.py
```

Esto generará un token aleatorio seguro. **Copia este token**.

### 3.2 Configurar Token en Django

**Opción A: Variable de Entorno (Recomendado)**

1. Abre PowerShell como administrador
2. Configura la variable de entorno:
   ```powershell
   $env:SCANNER_UPLOAD_TOKEN = "TU_TOKEN_AQUI"
   ```
3. Para hacerlo permanente, agrega al registro de Windows o usa `setx`:
   ```powershell
   setx SCANNER_UPLOAD_TOKEN "TU_TOKEN_AQUI"
   ```

**Opción B: En settings.py**

1. Abre `sistema_digitalizacion/settings.py`
2. Agrega al final del archivo:
   ```python
   import os
   SCANNER_UPLOAD_TOKEN = os.environ.get('SCANNER_UPLOAD_TOKEN', 'TU_TOKEN_AQUI')
   ```

### 3.3 Configurar Token en config.json

1. Abre `C:\scanner_service\config.json`
2. Reemplaza `"CAMBIA_POR_TU_TOKEN_SECRETO_AQUI"` con tu token:
   ```json
   {
       "AUTH_TOKEN": "TU_TOKEN_AQUI",
       ...
   }
   ```

**IMPORTANTE**: El token debe ser **exactamente el mismo** en Django y en `config.json`.

---

## 4. Configuración de NAPS2

### 4.1 Crear Perfil de Escaneo

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

### 4.2 Probar el Perfil

1. En NAPS2, selecciona el perfil `HP_ADF_300`
2. Coloca documentos en el ADF del escáner
3. Haz clic en **Scan**
4. Verifica que:
   - ✅ Escanea todas las páginas del ADF
   - ✅ Genera un PDF correctamente
   - ✅ La calidad es buena

---

## 5. Configuración del Servicio de Escaneo

### 5.1 Crear Directorio

```powershell
mkdir C:\scanner_service
cd C:\scanner_service
```

### 5.2 Copiar Archivos

1. Copia los siguientes archivos a `C:\scanner_service\`:
   - `scan_service.py`
   - `config.json`
   - `generate_token.py` (opcional, solo para generar tokens)

### 5.3 Configurar config.json

Abre `C:\scanner_service\config.json` y verifica/ajusta:

```json
{
    "AUTH_TOKEN": "TU_TOKEN_SECRETO_AQUI",
    "DJANGO_BASE_URL": "http://127.0.0.1:8000",
    "ARCHIVO_FIELD_NAME": "documento",
    "NAPS2_CLI": "C:\\Program Files\\NAPS2\\NAPS2.Console.exe",
    "NAPS2_PROFILE": "HP_ADF_300",
    "SCAN_TIMEOUT": 180,
    "UPLOAD_TIMEOUT": 120
}
```

**Ajusta según tu instalación:**
- `AUTH_TOKEN`: El mismo token que configuraste en Django
- `DJANGO_BASE_URL`: URL base de Django (por defecto `http://127.0.0.1:8000`)
- `NAPS2_CLI`: Ruta al ejecutable NAPS2 (verifica si está en otra ubicación)
- `NAPS2_PROFILE`: Nombre del perfil que creaste en NAPS2 (debe ser `HP_ADF_300`)

### 5.4 Probar el Servicio Manualmente

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

## 6. Instalación como Servicio Windows con NSSM

### 6.1 Instalar el Servicio

```powershell
# Abre PowerShell como Administrador
cd C:\nssm\win64

# Instalar servicio
.\nssm.exe install scanner_service
```

Se abrirá una ventana GUI. Configura:

**Tab: Application**
- **Path**: `C:\Python310\python.exe` (ajusta según tu instalación de Python)
- **Startup directory**: `C:\scanner_service`
- **Arguments**: `scan_service.py`

**Tab: Details**
- **Display name**: `Scanner Service`
- **Description**: `Servicio de escaneo automático con NAPS2 para HP ScanJet Pro 2600 f1`

**Tab: Log on**
- Selecciona **This account**
- Usa una cuenta de servicio o tu cuenta de usuario con permisos

**Tab: Dependencies**
- Puedes dejar vacío

**Tab: Process**
- ✅ **App exit action**: Restart application
- **Restart delay**: 5000 ms

**Tab: I/O (Opcional - para logs)**
- **Input (stdin)**: `C:\scanner_service\logs\stdin.log`
- **Output (stdout)**: `C:\scanner_service\logs\stdout.log`
- **Error (stderr)**: `C:\scanner_service\logs\stderr.log`

Crea el directorio de logs:
```powershell
mkdir C:\scanner_service\logs
```

### 6.2 Iniciar el Servicio

```powershell
# Iniciar servicio
.\nssm.exe start scanner_service

# Verificar estado
.\nssm.exe status scanner_service
```

### 6.3 Configurar Arranque Automático

El servicio ya debería estar configurado para arrancar automáticamente. Si no:

```powershell
.\nssm.exe set scanner_service Start SERVICE_AUTO_START
```

### 6.4 Comandos Útiles de NSSM

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

## 7. Pruebas del Flujo Completo

### 7.1 Verificar Servicio Local

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
  "django_url": "http://127.0.0.1:8000",
  "archivo_field": "documento"
}
```

### 7.2 Verificar Endpoint Django

1. Abre tu aplicación Django en el navegador
2. Ve a un expediente existente
3. Haz clic en "Subir Documento" de cualquier área
4. Deberías ver el botón **"Escanear Documento con HP ScanJet"**

### 7.3 Prueba de Escaneo Completo

1. **Preparar**
   - Abre un expediente en Django
   - Haz clic en "Subir Documento" de un área
   - Completa el nombre del documento
   - Coloca documentos en el ADF del escáner HP

2. **Escanear**
   - Haz clic en **"Escanear Documento con HP ScanJet"**
   - El botón cambiará a "Escaneando... por favor espere"
   - Espera mientras:
     - El servicio escanea los documentos
     - Sube el PDF a Django
     - Se crea el registro en la base de datos

3. **Verificar**
   - ✅ El documento aparece en la lista
   - ✅ Puedes descargarlo
   - ✅ El PDF tiene buena calidad
   - ✅ No quedan archivos temporales en el sistema

---

## 8. Solución de Problemas

### Problema: "NAPS2 no encontrado"
**Solución:**
- Verifica que NAPS2 esté instalado
- Ajusta `NAPS2_CLI` en `config.json` con la ruta correcta
- Verifica permisos de ejecución

### Problema: "Error al invocar NAPS2"
**Solución:**
- Verifica que el escáner esté encendido y conectado
- Prueba escanear manualmente desde NAPS2 GUI
- Verifica que el perfil `HP_ADF_300` exista y esté configurado correctamente
- Revisa los logs del servicio: `C:\scanner_service\scanner_service.log`

### Problema: "Unauthorized - invalid token" o "Token inválido"
**Solución:**
- Verifica que el token en `config.json` coincida con el de Django
- Verifica que el token esté configurado en ambos lugares
- Revisa las variables de entorno si las estás usando
- Asegúrate de que el token no tenga espacios extra

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
- Verifica que Python esté en el PATH del sistema

### Problema: Archivos temporales no se eliminan
**Solución:**
- Verifica permisos de escritura en `C:\Users\[Usuario]\AppData\Local\Temp`
- Revisa los logs del servicio para errores de eliminación
- Verifica que el servicio tenga permisos suficientes

### Problema: "Falta la etapa" en el escaneo
**Solución:**
- Verifica que el modal de subir documento tenga el campo `etapa` configurado
- Revisa el JavaScript en el template para asegurar que se envía la etapa

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
- El campo de archivo usado es `documento` (como se detectó en el código existente)
- La URL de Django usada es: `/expedientes/<expediente_id>/etapa/<etapa>/subir-documento/`

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `C:\scanner_service\scanner_service.log`
2. Revisa los logs de Django: `debug.log`
3. Verifica el estado del servicio: `nssm status scanner_service`
4. Verifica la conexión: `curl http://127.0.0.1:5001/health`

¡Buena suerte con tu sistema de escaneo! 🎉

