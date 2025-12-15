# 🔍 Detección e Implementación - Sistema de Escaneo

## 📋 Resumen de Detección Automática

### ✅ 1. Vista que Recibe y Guarda Documentos

**Vista Detectada:**
- **Nombre**: `subir_documento`
- **Ubicación**: `digitalizacion/views_expedientes.py` (línea 612)
- **Decoradores**: `@login_required` y `@require_http_methods(["POST"])`

**Cómo se detectó:**
1. Búsqueda con `grep` de funciones que contienen "subir" y "documento"
2. Análisis del código en `views_expedientes.py`
3. Verificación de que es la función principal que maneja `request.FILES`

**Parámetros que espera:**
- **URL**: `expediente_id` (int), `etapa` (str)
- **POST**: `area_id` (int), `nombre_documento` (str), `descripcion` (str, opcional)
- **FILES**: `documento` (archivo)

---

### ✅ 2. Nombre del Campo del Archivo

**Campo Detectado:**
- **Nombre**: `'documento'`

**Cómo se detectó:**
1. Búsqueda en `views_expedientes.py` línea 638: `if 'documento' not in request.FILES:`
2. Búsqueda en `views_expedientes.py` línea 641: `archivo = request.FILES['documento']`
3. Verificación en template `modales_etapas.html` línea 50: `<input type="file" id="documento" name="documento"`

**Confirmación:**
- ✅ El campo se llama `'documento'` en el formulario HTML
- ✅ El campo se llama `'documento'` en la vista Django
- ✅ Es consistente en todo el código

---

### ✅ 3. URL Exacta de Django

**URL Detectada:**
- **Pattern**: `path('<int:expediente_id>/etapa/<str:etapa>/subir-documento/', subir_documento, name='subir_documento')`
- **URL Completa**: `/expedientes/<expediente_id>/etapa/<etapa>/subir-documento/`
- **App name**: `expedientes`

**Cómo se detectó:**
1. Lectura de `digitalizacion/urls_expedientes.py` línea 50-51
2. Verificación en template `modales_etapas.html` línea 613: `{% url 'expedientes:subir_documento' expediente.pk 'ETAPA_PLACEHOLDER' %}`
3. Confirmación de que esta es la URL que usa el formulario HTML

**Estructura:**
```
/expedientes/{expediente_id}/etapa/{etapa}/subir-documento/
```

---

## 🔧 Implementación Realizada

### 1. Servicio Local (`scan_service.py`)

**Características:**
- ✅ Usa NAPS2 CLI para escanear
- ✅ Escanea todo el ADF como un solo PDF
- ✅ No guarda copias locales (elimina temporales)
- ✅ Envía directamente a la URL detectada de Django
- ✅ Usa el campo `'documento'` detectado
- ✅ Configuración mediante `config.json`
- ✅ Endpoint local: `http://127.0.0.1:5001/scan`

**Archivo de Configuración (`config.json`):**
```json
{
    "AUTH_TOKEN": "token_secreto",
    "DJANGO_BASE_URL": "http://127.0.0.1:8000",
    "ARCHIVO_FIELD_NAME": "documento",
    "NAPS2_CLI": "C:\\Program Files\\NAPS2\\NAPS2.Console.exe",
    "NAPS2_PROFILE": "HP_ADF_300"
}
```

---

### 2. Modificaciones en Django

**Vista Modificada (`views_expedientes.py`):**
- ✅ Removido `@login_required` (ahora acepta token Bearer)
- ✅ Agregada verificación de token Bearer
- ✅ Crea usuario `servicio_local` automáticamente si no existe
- ✅ Usa la misma lógica de guardado que subida manual
- ✅ Registra en historial con acción `subir_documento_escaneado`

**Flujo de Autenticación:**
1. Si viene header `Authorization: Bearer <token>` → Verifica token
2. Si no viene token → Requiere usuario autenticado (comportamiento original)
3. Si token válido → Permite subida sin usuario autenticado

---

### 3. JavaScript del Botón

**Template Modificado (`modales_etapas.html`):**
- ✅ Botón "Escanear Documento con HP ScanJet" agregado
- ✅ Función `iniciarEscaneo()` implementada
- ✅ Muestra "Escaneando... por favor espere" durante el proceso
- ✅ Deshabilita el botón mientras escanea
- ✅ Recarga la lista de documentos al finalizar
- ✅ Manejo de errores completo

**Datos que envía:**
```javascript
{
    expediente_id: <id>,
    etapa: <etapa>,
    area_id: <id>,
    nombre_documento: <nombre>,
    descripcion: <descripcion>
}
```

---

### 4. Documentación

**Archivos Creados:**
- ✅ `README_SCAN.md` - Guía completa de instalación
- ✅ `config.json` - Archivo de configuración
- ✅ `requirements.txt` - Dependencias Python
- ✅ `DETECCION_IMPLEMENTACION.md` - Este archivo

---

## ✅ Validaciones Realizadas

### Antes de Generar Código:

1. **Vista Detectada Correctamente:**
   - ✅ `subir_documento` en `views_expedientes.py`
   - ✅ Maneja `request.FILES['documento']`
   - ✅ Crea `DocumentoExpediente`

2. **Campo Detectado Correctamente:**
   - ✅ `'documento'` en formulario HTML
   - ✅ `'documento'` en `request.FILES`
   - ✅ Consistente en todo el código

3. **URL Detectada Correctamente:**
   - ✅ `/expedientes/<expediente_id>/etapa/<etapa>/subir-documento/`
   - ✅ Usada en template con `{% url 'expedientes:subir_documento' %}`
   - ✅ Coincide con el pattern en `urls_expedientes.py`

---

## 🎯 Flujo Completo Implementado

1. **Usuario hace clic en "Escanear"**
   - JavaScript llama a `http://127.0.0.1:5001/scan`
   - Envía: `expediente_id`, `etapa`, `area_id`, `nombre_documento`, `descripcion`

2. **Servicio Local (`scan_service.py`)**
   - Ejecuta NAPS2 CLI con perfil `HP_ADF_300`
   - Escanea todos los documentos del ADF
   - Genera PDF temporal

3. **Servicio sube a Django**
   - POST a: `/expedientes/{expediente_id}/etapa/{etapa}/subir-documento/`
   - Archivo en campo: `documento`
   - Headers: `Authorization: Bearer <token>`
   - Datos POST: `area_id`, `nombre_documento`, `descripcion`

4. **Django procesa**
   - Verifica token Bearer
   - Valida área y expediente
   - Guarda documento usando la misma lógica que subida manual
   - Crea usuario `servicio_local` si no existe
   - Registra en historial

5. **Servicio limpia**
   - Elimina PDF temporal
   - Elimina directorio temporal
   - No deja copias locales

6. **Frontend actualiza**
   - Cierra modal
   - Recarga lista de documentos
   - Muestra mensaje de éxito

---

## 📝 Archivos Modificados/Creados

### Archivos Creados:
1. `scanner_service/scan_service.py` - Servicio Flask
2. `scanner_service/config.json` - Configuración
3. `scanner_service/README_SCAN.md` - Documentación
4. `scanner_service/requirements.txt` - Dependencias
5. `scanner_service/DETECCION_IMPLEMENTACION.md` - Este archivo

### Archivos Modificados:
1. `digitalizacion/views_expedientes.py` - Vista `subir_documento` modificada
2. `digitalizacion/templates/digitalizacion/expedientes/modales_etapas.html` - Botón y JS agregados

---

## ✅ Todo Listo para Usar

El sistema está completamente implementado y listo para:
1. Instalar drivers HP
2. Instalar NAPS2
3. Configurar token
4. Configurar `config.json`
5. Probar el flujo completo

Sigue `README_SCAN.md` para la instalación paso a paso.

---

**Fecha de Implementación**: 2025-01-XX
**Versión**: 1.0.0

