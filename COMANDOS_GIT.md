# 📋 Comandos para Subir Cambios a Git

## 🚀 Pasos para subir todos los cambios

### 1. Ver qué archivos han cambiado

```powershell
cd D:\Resp\Documents\Sistema_Digitalizacion
git status
```

Esto te mostrará todos los archivos modificados y nuevos.

### 2. Agregar todos los archivos

```powershell
git add .
```

O si quieres ser más específico:

```powershell
# Archivos del sistema de escaneo remoto
git add digitalizacion/models.py
git add digitalizacion/views_escaneo.py
git add digitalizacion/views_archivos.py
git add digitalizacion/urls.py
git add digitalizacion/admin.py
git add digitalizacion/migrations/0018_solicitudescaneo.py
git add digitalizacion/migrations/0019_documentoexpediente_ruta_externa.py
git add digitalizacion/management/commands/limpiar_render.py
git add digitalizacion/templates/digitalizacion/expedientes/modales_etapas.html
git add digitalizacion/templates/digitalizacion/expedientes/detalle_expediente.html
git add digitalizacion/static/digitalizacion/js/escaneo.js
git add digitalizacion/search_utils.py

# Archivos del servicio de escaneo
git add scanner_service/scan_service.py
git add scanner_service/config.json
git add scanner_service/run_scanner.bat

# Scripts y documentación
git add descargar_archivos.py
git add README_DESCARGA_ARCHIVOS.md
git add GUIA_TASK_SCHEDULER_ESCANER.md
```

### 3. Crear commit con mensaje descriptivo

```powershell
git commit -m "Agregar sistema de escaneo remoto y gestión de archivos

- Sistema de escaneo remoto: permite escanear desde cualquier dispositivo
- Modelo SolicitudEscaneo para solicitudes de escaneo
- Endpoints API para listar y marcar archivos descargados
- Script descargar_archivos.py para descargar archivos desde Render
- Comando limpiar_render.py para limpiar archivos antiguos en Render
- Guardado automático y respaldo en scan_service.py
- Script run_scanner.bat para Task Scheduler
- Documentación completa en guías"
```

### 4. Subir a GitHub

```powershell
git push
```

Si tienes problemas de autenticación:

```powershell
git push origin main
```

O si tu rama se llama `master`:

```powershell
git push origin master
```

## 📝 Resumen de cambios principales

### Sistema de Escaneo Remoto
- ✅ Modelo `SolicitudEscaneo` para solicitudes remotas
- ✅ APIs para crear y consultar solicitudes
- ✅ Polling automático en scan_service.py
- ✅ JavaScript actualizado para modo remoto

### Gestión de Archivos
- ✅ Campo `ruta_externa` en DocumentoExpediente
- ✅ API para listar archivos pendientes
- ✅ Script de descarga automática
- ✅ Comando de limpieza para Render

### Guardado Automático
- ✅ Guardado en C:\servidor\Expedientes\
- ✅ Respaldo en D:\Resp\Respaldo_SistemaDigitalizacion\
- ✅ Organización por expediente
- ✅ Limpieza automática de archivos antiguos

## ⚠️ Si hay errores

### Error: "no se encontró git"
- Instala Git desde: https://git-scm.com/download/win
- O usa GitHub Desktop

### Error: "fatal: not a git repository"
- Asegúrate de estar en el directorio correcto:
  ```powershell
  cd D:\Resp\Documents\Sistema_Digitalizacion
  ```

### Error: "authentication failed"
- Configura tus credenciales:
  ```powershell
  git config --global user.name "Tu Nombre"
  git config --global user.email "tu@email.com"
  ```

### Error: "remote origin already exists"
- Eso está bien, solo continúa con `git push`

## ✅ Verificar después del push

1. Ve a tu repositorio en GitHub
2. Verifica que los cambios aparezcan
3. Render detectará automáticamente los cambios y se re-desplegará

