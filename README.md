# 📁 Sistema de Digitalización de Archivos

Un sistema web moderno desarrollado en Django para la gestión y digitalización de expedientes municipales con trazabilidad completa y validaciones por modalidad.

## 🌟 Características Principales

### ✨ Gestión de Expedientes
- **Dashboard moderno** con estadísticas en tiempo real
- **Creación por flujos**: Giro, Fuente, Tipo o Monto
- **17 etapas completas** del proceso de adquisición
- **Sistema de validaciones** según modalidad seleccionada
- **Búsqueda avanzada** con múltiples filtros
- **Vistas flexibles**: Tarjetas y tabla

### 🔒 Seguridad y Trazabilidad
- **Autenticación de usuarios** con roles
- **Historial completo** de cambios
- **Expedientes confidenciales**
- **Auditoría detallada** de acciones
- **Control de versiones** de documentos

### 📊 Modalidades Soportadas
- **Compra Directa**
- **Concurso por Invitación** 
- **Licitación**
- **Adjudicación Directa**

### 📑 Tipos de Adquisición
- **Bienes**
- **Servicios**
- **Arrendamientos**

### 💰 Fuentes de Financiamiento
- **Propio Municipal**
- **Estatal**
- **Federal**

## 🚀 Instalación

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd Sistema_Digitalizacion
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar migraciones**
   ```bash
   python manage.py migrate
   ```

4. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

5. **Cargar datos de prueba (opcional)**
   ```bash
   python manage.py crear_datos_prueba
   ```

6. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

7. **Acceder al sistema**
   - Abrir navegador en: `http://localhost:8000`
   - Administración: `http://localhost:8000/admin`

## 👥 Usuarios Demo

El comando `crear_datos_prueba` crea los siguientes usuarios:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | (la que configures) | Superusuario |
| jperez | demo123 | Usuario |
| mlopez | demo123 | Usuario |
| cgarcia | demo123 | Usuario |

## 🏗️ Estructura del Proyecto

```
Sistema_Digitalizacion/
├── digitalizacion/           # Aplicación principal
│   ├── models.py            # Modelos de datos
│   ├── views.py             # Lógica de vistas
│   ├── forms.py             # Formularios
│   ├── admin.py             # Configuración admin
│   ├── urls.py              # URLs de la app
│   ├── templates/           # Templates HTML
│   └── management/          # Comandos personalizados
├── static/                  # Archivos estáticos
│   ├── css/                # Estilos personalizados
│   └── js/                 # JavaScript
├── media/                   # Archivos subidos
├── sistema_digitalizacion/  # Configuración del proyecto
│   ├── settings.py         # Configuración
│   └── urls.py             # URLs principales
├── requirements.txt         # Dependencias
└── manage.py               # Gestor de Django
```

## 📋 Modelos de Datos

### 📄 Documento (Expediente)
- **Información básica**: Número, título, descripción
- **Clasificación**: Tipo, departamento, giro
- **Proceso**: Fuente financiamiento, tipo adquisición, modalidad
- **Estado**: Pendiente, en proceso, digitalizado, verificado, archivado
- **Archivos**: Documentos digitales con metadatos
- **Fechas**: Creación, documento, vencimiento, digitalización
- **Usuarios**: Creado por, digitalizado por, verificado por

### 🏢 Departamento
- Nombre y descripción
- Estado activo/inactivo
- Fecha de creación

### 📋 TipoDocumento
- Nombre y descripción
- Estado activo/inactivo
- Fecha de creación

### 📊 HistorialDocumento
- Registro de cambios
- Usuario que realizó la acción
- Fecha y hora
- Estados anterior y nuevo
- Descripción detallada

### ⚙️ ConfiguracionSistema
- Configuraciones clave-valor
- Parámetros del sistema
- Valores predeterminados

## 🎨 Tecnologías Utilizadas

### Backend
- **Django 5.0** - Framework web
- **SQLite** - Base de datos (por defecto)
- **Pillow** - Procesamiento de imágenes
- **Python Decouple** - Configuración

### Frontend
- **Bootstrap 5** - Framework CSS
- **Bootstrap Icons** - Iconografía
- **Django Crispy Forms** - Formularios mejorados
- **JavaScript Vanilla** - Interactividad

### Características del Diseño
- **Tema oscuro moderno** (zinc-950 palette)
- **Colores de acento** en verde esmeralda
- **Interfaz responsiva**
- **Animaciones suaves**
- **UX optimizada**

## 🔧 Configuración

### Variables de Entorno
Puedes usar un archivo `.env` con:

```env
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Configuraciones del Sistema
Accede a `/admin` para configurar:

- **max_file_size**: Tamaño máximo de archivo (bytes)
- **allowed_extensions**: Extensiones permitidas
- **auto_archive_days**: Días para archivado automático
- **notification_email**: Email para notificaciones

## 📱 Funcionalidades

### Dashboard Principal
- Estadísticas en tiempo real
- Actividad reciente
- Búsqueda rápida de expedientes
- Indicadores de rendimiento

### Gestión de Expedientes
- Creación guiada por modalidad
- Edición completa de información
- Cambio de estados del proceso
- Subida de archivos digitales

### Sistema de Búsqueda
- Búsqueda por texto libre
- Filtros por departamento
- Filtros por tipo de documento
- Filtros por estado
- Vista de tarjetas o tabla

### Administración
- Gestión de usuarios
- Configuración de tipos de documento
- Gestión de departamentos
- Configuraciones del sistema
- Reportes y auditoría

## 🚀 Próximas Mejoras

### Funcionalidades Planificadas
- [ ] **Sistema completo de etapas** (17 etapas del proceso)
- [ ] **Gestión de comentarios** por etapa
- [ ] **Notificaciones automáticas**
- [ ] **Reportes avanzados** con gráficas
- [ ] **API REST** para integraciones
- [ ] **Exportación** a PDF y Excel
- [ ] **Firma digital** de documentos
- [ ] **Dashboard ejecutivo** con KPIs

### Mejoras Técnicas
- [ ] **Tests automatizados**
- [ ] **Documentación API**
- [ ] **Docker containerization**
- [ ] **Base de datos PostgreSQL**
- [ ] **Cache con Redis**
- [ ] **Búsqueda con Elasticsearch**

## 🐛 Solución de Problemas

### Error: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Error: No such table
```bash
python manage.py migrate
```

### Error: Permission denied (media files)
Verificar permisos de escritura en carpeta `media/`

### Error: Static files not loading
```bash
python manage.py collectstatic
```

## 📞 Soporte

Para problemas o mejoras:

1. **Revisar la documentación**
2. **Verificar logs** en la consola del servidor
3. **Comprobar configuración** en `settings.py`
4. **Validar datos** en el admin de Django

## 📝 Licencia

Este proyecto está desarrollado para uso interno municipal. Todos los derechos reservados.

## 🏆 Créditos

Desarrollado como sistema integral de digitalización de expedientes municipales con enfoque en:
- **Transparencia administrativa**
- **Eficiencia en procesos**
- **Trazabilidad completa**
- **Cumplimiento normativo**

---

### 🎯 Objetivo del Sistema

Modernizar y digitalizar los procesos de adquisición municipal mediante un sistema web robusto que garantice:

- ✅ **Trazabilidad completa** de documentos
- ✅ **Validaciones automáticas** por modalidad
- ✅ **Interfaces modernas** y fáciles de usar
- ✅ **Cumplimiento normativo** en cada etapa
- ✅ **Auditoría detallada** de todas las acciones
- ✅ **Eficiencia operativa** en los procesos


-.\.venv\Scripts\activate
