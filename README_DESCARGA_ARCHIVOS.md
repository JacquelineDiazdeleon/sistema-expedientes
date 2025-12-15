# Sistema de Descarga de Archivos desde Render

Este sistema permite descargar automáticamente los archivos subidos a Render hacia tu PC local, organizándolos y creando respaldos.

## 📁 Estructura del Sistema

```
Render (Temporal)
    ↓
    API /api/archivos/pendientes/
    ↓
Script descargar_archivos.py (Tu PC)
    ↓
C:/servidor/Expedientes/ (Principal)
    └── EXP-2024-001/
        └── documento.pdf
    └── EXP-2024-002/
        └── documento2.pdf
    ↓
D:/Resp/Respaldo_SistemaDigitalizacion/ (Respaldo)
    └── documento.pdf
    └── documento2.pdf
```

## 🔧 Configuración

### 1. Configurar Django (Render)

Los archivos se suben a `MEDIA_ROOT` en Render temporalmente. La configuración ya está lista:

- `MEDIA_URL = "/media/"`
- `MEDIA_ROOT = BASE_DIR / "media"`

### 2. Ejecutar Migraciones

```bash
python manage.py migrate
```

Esto agregará los campos `ruta_externa` y `fecha_descargado` a `DocumentoExpediente`.

### 3. Configurar el Script de Descarga

Edita `descargar_archivos.py` y ajusta las rutas si es necesario:

```python
# Carpeta principal
BASE_PC = Path("C:/servidor/Expedientes")

# Carpeta de respaldo
BACKUP = Path("D:/Resp/Respaldo_SistemaDigitalizacion")

# URL de tu aplicación en Render
URL_BASE = "https://sistema-expedientes-u2em.onrender.com"
```

### 4. Instalar Dependencias del Script

```bash
pip install requests
```

### 5. Programar Ejecución Automática

#### Windows Task Scheduler:

1. Abre **Task Scheduler** (Programador de tareas)
2. Clic en "Crear tarea básica"
3. Nombre: "Descargar Archivos Render"
4. Activación: "Diariamente" o "Cada hora"
5. Acción: "Iniciar un programa"
6. Programa: `python` (o ruta completa a python.exe)
7. Argumentos: `"D:\Resp\Documents\Sistema_Digitalizacion\descargar_archivos.py"`
8. Iniciar en: `D:\Resp\Documents\Sistema_Digitalizacion`

### 6. Configurar Limpieza Automática en Render

En Render, crea un **Scheduled Job** (Cron Job):

**Comando:**
```bash
cd sistema_digitalizacion && python manage.py limpiar_render
```

**Horario:** Diariamente a las 3:00 AM (o cuando prefieras)

**Opciones del comando:**
```bash
# Limpiar archivos más antiguos de 24 horas (default)
python manage.py limpiar_render

# Cambiar tiempo máximo (48 horas)
python manage.py limpiar_render --horas 48

# Cambiar tamaño máximo (200 MB)
python manage.py limpiar_render --tamano-max 200

# Ver qué se eliminaría sin eliminar (dry run)
python manage.py limpiar_render --dry-run
```

## 📋 Endpoints API

### Listar archivos pendientes

```
GET /api/archivos/pendientes/
```

Retorna:
```json
{
  "success": true,
  "count": 5,
  "archivos": [
    {
      "id": 123,
      "tipo": "expediente",
      "nombre": "documento.pdf",
      "nombre_documento": "Documento Principal",
      "url": "https://.../media/documentos/documento.pdf",
      "expediente_id": 45,
      "expediente_numero": "EXP-2024-001",
      "fecha_subida": "2024-01-15T10:30:00Z",
      "tamano": 1024000
    }
  ]
}
```

### Marcar como descargado

```
POST /api/archivos/<documento_id>/marcar-descargado/
Content-Type: application/json

{
  "ruta_externa": "C:/servidor/Expedientes/EXP-2024-001/documento.pdf",
  "tipo": "expediente"
}
```

## 🔍 Uso Manual

### Descargar archivos manualmente

```bash
python descargar_archivos.py
```

El script:
1. Consulta los archivos pendientes
2. Los descarga a `C:/servidor/Expedientes/`
3. Crea respaldos en `D:/Resp/Respaldo_SistemaDigitalizacion/`
4. Marca los archivos como descargados en Django

### Limpiar archivos en Render manualmente

```bash
python manage.py limpiar_render
```

## 📊 Logs

El script genera logs en:
- `descargar_archivos.log` - Log del script de descarga
- Console output - Ver en tiempo real

## 🎯 Organización de Archivos

Los archivos se organizan así:

```
C:/servidor/Expedientes/
├── EXP-2024-001/
│   ├── documento1.pdf
│   └── documento2.pdf
├── EXP-2024-002/
│   └── documento3.pdf
└── documentos/
    └── archivo_antiguo.pdf
```

## ⚙️ Personalización

### Cambiar rutas de descarga

Edita `descargar_archivos.py`:

```python
BASE_PC = Path("D:/MisExpedientes")  # Cambiar aquí
BACKUP = Path("D:/Respaldos")        # Cambiar aquí
```

### Cambiar límites de limpieza

Edita `digitalizacion/management/commands/limpiar_render.py`:

```python
TIEMPO_MAX_HORAS = 48  # Cambiar tiempo
TAM_MAX_MB = 200       # Cambiar tamaño
```

## ✅ Verificación

Para verificar que todo funciona:

1. **Sube un documento** desde la web
2. **Espera unos minutos** o ejecuta manualmente:
   ```bash
   python descargar_archivos.py
   ```
3. **Verifica** que el archivo esté en `C:/servidor/Expedientes/`
4. **Verifica** que el respaldo esté en `D:/Resp/Respaldo_SistemaDigitalizacion/`
5. **Verifica** en la web que el documento ya no aparezca como pendiente

## 🔒 Seguridad

- El script no requiere autenticación especial para los endpoints públicos
- Los archivos se organizan por expediente automáticamente
- Se mantienen respaldos automáticos
- Los archivos antiguos se eliminan de Render automáticamente

## 📝 Notas

- Los archivos se eliminan de Render después de 24 horas (configurable)
- El script evita descargar archivos duplicados
- Si un archivo ya existe, se marca como descargado sin sobrescribir
- Los logs se guardan automáticamente para auditoría

