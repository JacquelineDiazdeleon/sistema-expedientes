# 📋 Guía Completa: Configurar Escáner Automático con Task Scheduler

Esta guía te ayudará a configurar tu escáner para que funcione automáticamente, guarde expedientes en la carpeta principal y cree respaldos automáticos usando Task Scheduler de Windows.

## 📁 Estructura de Carpetas

El sistema guardará los archivos en:

```
C:\servidor\Expedientes\          ← Carpeta principal
├── EXP-123\
│   ├── documento_20240115_143022.pdf
│   └── otro_doc_20240115_150000.pdf
└── EXP-456\
    └── documento_20240115_160000.pdf

D:\Resp\Respaldo_SistemaDigitalizacion\  ← Carpeta de respaldo
├── documento_20240115_143022.pdf
├── otro_doc_20240115_150000.pdf
└── documento_20240115_160000.pdf
```

## ✅ Paso 1: Preparar Carpetas

### 1.1 Crear las carpetas necesarias

Abre PowerShell como Administrador y ejecuta:

```powershell
# Crear carpeta principal
New-Item -ItemType Directory -Path "C:\servidor\Expedientes" -Force

# Crear carpeta de respaldo
New-Item -ItemType Directory -Path "D:\Resp\Respaldo_SistemaDigitalizacion" -Force
```

O créalas manualmente desde el Explorador de Windows.

### 1.2 Verificar permisos

Asegúrate de que tu usuario tenga permisos de escritura en ambas carpetas:
- Clic derecho en la carpeta → Propiedades → Seguridad
- Verifica que tu usuario tenga "Control total" o al menos "Modificar"

## ✅ Paso 2: Configurar el Script

### 2.1 Verificar config.json

Abre `scanner_service/config.json` y verifica que tenga estas líneas:

```json
{
    "CARPETA_PRINCIPAL": "C:\\servidor\\Expedientes",
    "CARPETA_RESPALDO": "D:\\Resp\\Respaldo_SistemaDigitalizacion",
    "MAX_ARCHIVOS_PRINCIPAL": 1000
}
```

### 2.2 Verificar run_scanner.bat

El archivo `scanner_service/run_scanner.bat` ya está creado. Si necesitas ajustar la ruta de Python, edítalo:

```batch
REM Cambia esta línea si Python no está en el PATH:
python scan_service.py

REM O usa la ruta completa:
C:\Users\TuUsuario\AppData\Local\Programs\Python\Python312\python.exe scan_service.py
```

### 2.3 Probar el script manualmente

1. Haz doble clic en `run_scanner.bat`
2. Deberías ver el servicio iniciándose
3. Prueba escanear un documento desde la web
4. Verifica que:
   - El archivo aparezca en `C:\servidor\Expedientes\`
   - El respaldo aparezca en `D:\Resp\Respaldo_SistemaDigitalizacion\`

## ✅ Paso 3: Configurar Task Scheduler

### 3.1 Abrir Task Scheduler

1. Presiona `Win + R`
2. Escribe `taskschd.msc` y presiona Enter
3. O busca "Programador de tareas" en el menú Inicio

### 3.2 Crear Tarea Básica

1. En el panel derecho, clic en **"Crear tarea básica..."**

2. **Pestaña General:**
   - **Nombre:** `Servicio Escaneo Digitalizacion`
   - **Descripción:** `Ejecuta el servicio de escaneo automáticamente al iniciar Windows`
   - ✅ Marcar: **"Ejecutar con los privilegios más altos"** (importante para acceso a carpetas)
   - ✅ Marcar: **"Ejecutar tanto si el usuario ha iniciado sesión como si no"**
   - ✅ Marcar: **"No almacenar contraseña"** (si no hay contraseña)

3. **Pestaña Activadores:**
   - Clic en **"Nuevo..."**
   - **Iniciar la tarea:** `Al iniciar sesión` (o `Al iniciar el equipo`)
   - ✅ Marcar: **"Habilitado"**
   - Clic en **"Aceptar"**

4. **Pestaña Acciones:**
   - Clic en **"Nuevo..."**
   - **Acción:** `Iniciar un programa`
   - **Programa o script:** 
     ```
     D:\Resp\Documents\Sistema_Digitalizacion\scanner_service\run_scanner.bat
     ```
     (Ajusta la ruta según tu instalación)
   - **Iniciar en (opcional):**
     ```
     D:\Resp\Documents\Sistema_Digitalizacion\scanner_service
     ```
   - Clic en **"Aceptar"**

5. **Pestaña Condiciones:**
   - ✅ Desmarcar: **"Iniciar la tarea solo si el equipo está conectado a la alimentación de CA"**
   - ✅ Desmarcar: **"Activar la tarea solo si el equipo está conectado a la alimentación de CA"**
   - ✅ Marcar: **"Activar la tarea"** (para que funcione siempre)

6. **Pestaña Configuración:**
   - ✅ Marcar: **"Permitir ejecutar la tarea a petición"**
   - ✅ Marcar: **"Ejecutar la tarea tan pronto como sea posible después de una programación omitida"**
   - ✅ Marcar: **"Si la tarea falla, reiniciar cada:"** `1 minuto`
   - **Número máximo de intentos de reinicio:** `3`
   - ✅ Marcar: **"Si la tarea en ejecución no finaliza cuando se solicita, forzar su detención"**

7. Clic en **"Aceptar"** y confirma con tu contraseña si se solicita

### 3.3 Configurar para Ejecución Continua

Para que el servicio se reinicie automáticamente si se cierra:

1. Clic derecho en la tarea → **"Propiedades"**
2. **Pestaña Configuración:**
   - ✅ Marcar: **"Si la tarea ya está en ejecución, aplicar la siguiente regla:"**
   - Seleccionar: **"Reiniciar la tarea"**

## ✅ Paso 4: Verificar Funcionamiento

### 4.1 Ejecutar la tarea manualmente

1. En Task Scheduler, busca tu tarea
2. Clic derecho → **"Ejecutar"**
3. Verifica que:
   - El servicio se inicie correctamente
   - Aparezca en la lista de procesos (Ctrl+Shift+Esc → Procesos)
   - Los logs se generen en `scanner_service/scanner_service.log`

### 4.2 Verificar al iniciar Windows

1. Reinicia tu computadora
2. Inicia sesión
3. Espera unos segundos
4. Verifica que el servicio esté corriendo:
   - Abre `http://127.0.0.1:5001/health` en el navegador
   - O revisa los procesos en el Administrador de tareas

### 4.3 Probar escaneo completo

1. Abre la aplicación web
2. Selecciona un expediente
3. Haz clic en "Escanear documento"
4. Coloca documentos en el escáner
5. Espera a que termine
6. Verifica que:
   - El documento aparezca en la web
   - El archivo esté en `C:\servidor\Expedientes\EXP-XXX\`
   - El respaldo esté en `D:\Resp\Respaldo_SistemaDigitalizacion\`

## 🔧 Solución de Problemas

### Problema: El servicio no inicia automáticamente

**Solución:**
1. Verifica que la ruta en Task Scheduler sea correcta
2. Verifica que Python esté en el PATH o usa la ruta completa
3. Revisa los logs en `scanner_service/scanner_service.log`
4. Ejecuta `run_scanner.bat` manualmente para ver errores

### Problema: "Acceso denegado" al guardar archivos

**Solución:**
1. Verifica permisos de las carpetas (Paso 1.2)
2. Ejecuta Task Scheduler como Administrador
3. En las propiedades de la tarea, marca "Ejecutar con los privilegios más altos"

### Problema: El servicio se cierra después de un tiempo

**Solución:**
1. En Task Scheduler → Propiedades → Configuración
2. Marca "Reiniciar la tarea" si ya está en ejecución
3. Configura reintentos automáticos

### Problema: No se guardan archivos en las carpetas

**Solución:**
1. Verifica que `config.json` tenga las rutas correctas
2. Verifica que las carpetas existan y tengan permisos
3. Revisa los logs para ver errores específicos

## 📊 Monitoreo

### Ver estado del servicio

```powershell
# Ver si el proceso está corriendo
Get-Process python | Where-Object {$_.Path -like "*scanner*"}

# Ver logs en tiempo real
Get-Content scanner_service\scanner_service.log -Wait -Tail 50
```

### Verificar archivos guardados

```powershell
# Contar archivos en carpeta principal
(Get-ChildItem "C:\servidor\Expedientes" -Recurse -Filter "*.pdf").Count

# Ver tamaño total
(Get-ChildItem "C:\servidor\Expedientes" -Recurse -Filter "*.pdf" | Measure-Object -Property Length -Sum).Sum / 1MB
```

## 🔄 Mantenimiento

### Limpiar archivos antiguos

El script automáticamente elimina archivos antiguos cuando hay más de 1000 archivos (configurable en `config.json`).

Para limpiar manualmente:

```powershell
# Eliminar archivos más antiguos de 30 días
Get-ChildItem "C:\servidor\Expedientes" -Recurse -Filter "*.pdf" | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item
```

### Actualizar el servicio

1. Detén la tarea en Task Scheduler
2. Actualiza los archivos del servicio
3. Reinicia la tarea

## ✅ Checklist Final

- [ ] Carpetas creadas y con permisos
- [ ] `config.json` configurado correctamente
- [ ] `run_scanner.bat` probado manualmente
- [ ] Tarea creada en Task Scheduler
- [ ] Tarea configurada para iniciar al arrancar
- [ ] Tarea probada manualmente
- [ ] Servicio verificado después de reiniciar
- [ ] Escaneo de prueba completado exitosamente
- [ ] Archivos verificados en carpetas principales y respaldo

## 📝 Notas Importantes

1. **El servicio debe estar corriendo** para que funcione el escaneo remoto
2. **Los archivos se guardan automáticamente** después de cada escaneo
3. **Los respaldos se crean automáticamente** para cada archivo
4. **Task Scheduler es la mejor opción** para scripts que necesitan acceso a GUI (como NAPS2)
5. **El servicio se reinicia automáticamente** si se cierra inesperadamente

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs en `scanner_service/scanner_service.log`
2. Ejecuta `run_scanner.bat` manualmente para ver errores
3. Verifica que todas las rutas sean correctas
4. Asegúrate de que NAPS2 esté instalado y configurado

