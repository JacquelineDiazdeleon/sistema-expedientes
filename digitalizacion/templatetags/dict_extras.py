from django import template

register = template.Library()

# Paleta de colores para los gráficos
CHART_COLORS = [
    '#6366f1',  # indigo-500
    '#8b5cf6',  # violet-500
    '#a855f7',  # purple-500
    '#d946ef',  # fuchsia-500
    '#ec4899',  # pink-500
    '#f43f5e',  # rose-500
    '#ef4444',  # red-500
    '#f97316',  # orange-500
    '#f59e0b',  # amber-500
    '#10b981',  # emerald-500
    '#14b8a6',  # teal-500
    '#06b6d4',  # cyan-500
]

@register.filter
def get_item(dictionary, key):
    """Template filter para acceder a elementos de diccionario por clave"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_chart_color(index):
    """Devuelve un color de la paleta basado en el índice"""
    return CHART_COLORS[index % len(CHART_COLORS)]

@register.filter
def get_icono(filename):
    """Devuelve el ícono correspondiente al tipo de archivo"""
    if not filename:
        return 'bi-file-earmark'
    
    extension = filename.split('.')[-1].lower()
    
    # Mapeo de extensiones a íconos de Bootstrap Icons
    icon_map = {
        # Documentos
        'pdf': 'bi-file-earmark-pdf',
        'doc': 'bi-file-earmark-word',
        'docx': 'bi-file-earmark-word',
        'txt': 'bi-file-earmark-text',
        'rtf': 'bi-file-earmark-text',
        'odt': 'bi-file-earmark-text',
        'xls': 'bi-file-earmark-excel',
        'xlsx': 'bi-file-earmark-excel',
        'csv': 'bi-file-earmark-spreadsheet',
        'ppt': 'bi-file-earmark-ppt',
        'pptx': 'bi-file-earmark-ppt',
        
        # Imágenes
        'jpg': 'bi-file-earmark-image',
        'jpeg': 'bi-file-earmark-image',
        'png': 'bi-file-earmark-image',
        'gif': 'bi-file-earmark-image',
        'bmp': 'bi-file-earmark-image',
        'svg': 'bi-file-earmark-image',
        'webp': 'bi-file-earmark-image',
        
        # Archivos comprimidos
        'zip': 'bi-file-earmark-zip',
        'rar': 'bi-file-earmark-zip',
        '7z': 'bi-file-earmark-zip',
        'tar': 'bi-file-earmark-zip',
        'gz': 'bi-file-earmark-zip',
        
        # Código fuente
        'py': 'bi-file-earmark-code',
        'js': 'bi-file-earmark-code',
        'html': 'bi-file-earmark-code',
        'css': 'bi-file-earmark-code',
        'json': 'bi-file-earmark-code',
        'xml': 'bi-file-earmark-code',
        
        # Por defecto
        'default': 'bi-file-earmark'
    }

    return icon_map.get(extension, icon_map['default'])

@register.filter
def get_tipo_archivo(filename):
    """Devuelve el tipo de archivo formateado (PDF, DOCX, etc.) basado en la extensión"""
    if not filename:
        return 'ARCHIVO'
    
    extension = filename.split('.')[-1].lower()
    
    # Mapeo de extensiones a tipos legibles
    tipo_map = {
        'pdf': 'PDF',
        'doc': 'DOC',
        'docx': 'DOCX',
        'xls': 'XLS',
        'xlsx': 'XLSX',
        'ppt': 'PPT',
        'pptx': 'PPTX',
        'txt': 'TXT',
        'rtf': 'RTF',
        'jpg': 'JPG',
        'jpeg': 'JPG',
        'png': 'PNG',
        'gif': 'GIF',
        'bmp': 'BMP',
        'svg': 'SVG',
        'zip': 'ZIP',
        'rar': 'RAR',
        '7z': '7Z',
    }
    
    return tipo_map.get(extension, extension.upper() if extension else 'ARCHIVO')
