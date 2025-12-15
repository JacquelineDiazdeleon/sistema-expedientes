/**
 * Módulo centralizado para mostrar notificaciones animadas en la aplicación
 * 
 * Este archivo ha sido actualizado para usar el nuevo sistema avanzado de notificaciones.
 * Todas las llamadas a mostrarNotificacion serán redirigidas al nuevo sistema.
 */

// Cargar el nuevo sistema de notificaciones
const cargarSistemaNotificaciones = () => {
    // Verificar si ya está cargado
    if (window.notificaciones) return Promise.resolve();
    
    return new Promise((resolve, reject) => {
        // Crear script dinámico
        const script = document.createElement('script');
        script.src = '/static/digitalizacion/js/notificaciones-avanzado.js';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Error al cargar el sistema de notificaciones avanzado'));
        document.head.appendChild(script);
    });
};

// Función de compatibilidad para mantener la API existente
const mostrarNotificacion = async (mensaje = '', tipo = 'info', tiempo = 3000) => {
    try {
        // Cargar el sistema de notificaciones si no está cargado
        if (!window.notificaciones) {
            await cargarSistemaNotificaciones();
        }
        
        // Usar el nuevo sistema de notificaciones
        if (window.notificaciones) {
            return window.notificaciones.mostrar(mensaje, tipo, tiempo);
        } else {
            console.error('No se pudo cargar el sistema de notificaciones');
        }
    } catch (error) {
        console.error('Error al mostrar notificación:', error);
    }
};

// Hacer la función global
window.mostrarNotificacion = mostrarNotificacion;

// Cargar el sistema de notificaciones automáticamente
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cargarSistemaNotificaciones);
} else {
    cargarSistemaNotificaciones().catch(console.error);
}
