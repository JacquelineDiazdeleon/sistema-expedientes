/**
 * Utilidades globales para la aplicación de digitalización
 */

/**
 * Obtiene el icono correspondiente al tipo de archivo
 * @param {string} nombreArchivo - Nombre o extensión del archivo
 * @returns {string} Clase del ícono de Bootstrap Icons
 */
function obtenerIconoTipoArchivo(nombreArchivo) {
    if (!nombreArchivo) return 'bi-file-earmark';
    
    const extension = nombreArchivo.split('.').pop().toLowerCase();
    
    const tipos = {
        // Documentos
        'pdf': 'bi-file-pdf',
        'doc': 'bi-file-word',
        'docx': 'bi-file-word',
        'xls': 'bi-file-excel',
        'xlsx': 'bi-file-excel',
        'ppt': 'bi-file-ppt',
        'pptx': 'bi-file-ppt',
        'txt': 'bi-file-text',
        'rtf': 'bi-file-text',
        'csv': 'bi-file-spreadsheet',
        
        // Imágenes
        'jpg': 'bi-file-image',
        'jpeg': 'bi-file-image',
        'png': 'bi-file-image',
        'gif': 'bi-file-image',
        'bmp': 'bi-file-image',
        'svg': 'bi-file-image',
        'webp': 'bi-file-image',
        
        // Comprimidos
        'zip': 'bi-file-zip',
        'rar': 'bi-file-zip',
        '7z': 'bi-file-zip',
        'tar': 'bi-file-zip',
        'gz': 'bi-file-zip',
        
        // Código
        'html': 'bi-file-code',
        'css': 'bi-file-code',
        'js': 'bi-file-code',
        'json': 'bi-file-code',
        'py': 'bi-file-code',
        'java': 'bi-file-code',
        'c': 'bi-file-code',
        'cpp': 'bi-file-code',
        'h': 'bi-file-code',
        'php': 'bi-file-code',
        'sql': 'bi-file-code',
    };
    
    return tipos[extension] || 'bi-file-earmark';
}

/**
 * Formatea el tamaño de un archivo en un formato legible
 * @param {number} bytes - Tamaño en bytes
 * @returns {string} Tamaño formateado (ej: "1.5 MB")
 */
function formatearTamanoArchivo(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Calcula el tiempo transcurrido desde una fecha
 * @param {string} fechaISO - Fecha en formato ISO
 * @returns {string} Tiempo transcurrido (ej: "hace 2 horas")
 */
function tiempoTranscurrido(fechaISO) {
    if (!fechaISO) return 'Nunca';
    
    const fecha = new Date(fechaISO);
    const ahora = new Date();
    const segundos = Math.floor((ahora - fecha) / 1000);
    
    const intervalos = {
        año: 31536000,
        mes: 2592000,
        semana: 604800,
        día: 86400,
        hora: 3600,
        minuto: 60,
        segundo: 1
    };
    
    for (const [unidad, segundosEnUnidad] of Object.entries(intervalos)) {
        const intervalo = Math.floor(segundos / segundosEnUnidad);
        
        if (intervalo >= 1) {
            return intervalo === 1 
                ? `hace 1 ${unidad}` 
                : `hace ${intervalo} ${unidad}${intervalo !== 1 ? 's' : ''}`;
        }
    }
    
    return 'ahora';
}

/**
 * Formatea una fecha en un formato legible
 * @param {string} fechaISO - Fecha en formato ISO
 * @param {boolean} incluirHora - Si se debe incluir la hora
 * @returns {string} Fecha formateada
 */
function formatearFecha(fechaISO, incluirHora = true) {
    if (!fechaISO) return 'No disponible';
    
    const opciones = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: incluirHora ? '2-digit' : undefined,
        minute: incluirHora ? '2-digit' : undefined,
        hour12: true
    };
    
    try {
        return new Date(fechaISO).toLocaleString('es-MX', opciones);
    } catch (e) {
        console.error('Error al formatear fecha:', e);
        return fechaISO;
    }
}

/**
 * Obtiene el valor de una cookie por su nombre
 * @param {string} name - Nombre de la cookie
 * @returns {string|null} Valor de la cookie o null si no existe
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Cambia el tema de la aplicación entre claro y oscuro
 * @param {string} tema - 'light' o 'dark'
 */
function cambiarTema(tema) {
    const html = document.documentElement;
    const temaActual = html.getAttribute('data-theme');
    
    // Si no se especifica un tema, alternar entre claro/oscuro
    if (!tema) {
        tema = temaActual === 'dark' ? 'light' : 'dark';
    }
    
    // Aplicar el tema
    html.setAttribute('data-theme', tema);
    localStorage.setItem('tema', tema);
    
    // Actualizar el ícono del tema
    const iconoTemaClaro = document.getElementById('icono-tema-claro');
    const iconoTemaOscuro = document.getElementById('icono-tema-oscuro');
    
    if (tema === 'dark') {
        if (iconoTemaClaro) iconoTemaClaro.classList.add('d-none');
        if (iconoTemaOscuro) iconoTemaOscuro.classList.remove('d-none');
    } else {
        if (iconoTemaClaro) iconoTemaClaro.classList.remove('d-none');
        if (iconoTemaOscuro) iconoTemaOscuro.classList.add('d-none');
    }
    
    // Disparar evento personalizado
    document.dispatchEvent(new CustomEvent('temaCambiado', { detail: { tema } }));
}

// Hacer que las funciones estén disponibles globalmente
window.obtenerIconoTipoArchivo = obtenerIconoTipoArchivo;
window.formatearTamanoArchivo = formatearTamanoArchivo;
window.tiempoTranscurrido = tiempoTranscurrido;
window.formatearFecha = formatearFecha;
window.getCookie = getCookie;
window.cambiarTema = cambiarTema;
