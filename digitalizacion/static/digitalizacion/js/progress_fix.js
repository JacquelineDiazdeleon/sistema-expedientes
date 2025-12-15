// progress_fix.js - Mejoras para el manejo de la barra de progreso

/**
 * Inicializa el sistema de progreso con control de actualización automática
 * @param {number} expedienteId - ID del expediente
 */
function inicializarProgreso(expedienteId) {
    // Inicializar bandera de control
    window.deshabilitarActualizacionAutomatica = false;
    
    // Función para actualizar el progreso
    const actualizar = async () => {
        // No actualizar si está deshabilitado
        if (window.deshabilitarActualizacionAutomatica) {
            console.log('Actualización automática deshabilitada temporalmente');
            return;
        }
        
        try {
            const progreso = await obtenerProgreso(expedienteId);
            if (progreso) {
                actualizarBarraProgreso(progreso);
            }
        } catch (error) {
            console.error('Error al actualizar progreso:', error);
        }
    };

    // Actualizar el progreso inicial
    actualizar();
    
    // Limpiar intervalo anterior si existe
    if (window.intervaloProgreso) {
        clearInterval(window.intervaloProgreso);
    }
    
    // Actualizar el progreso cada 30 segundos, pero solo si no está deshabilitado
    window.intervaloProgreso = setInterval(() => {
        if (!window.deshabilitarActualizacionAutomatica) {
            actualizar();
        }
    }, 30000);
    
    // Guardar la función de actualización para uso manual
    window.actualizarProgresoManual = actualizar;
    
    return actualizar;
}

/**
 * Función para deshabilitar temporalmente la actualización automática
 * @param {number} segundos - Tiempo en segundos para deshabilitar la actualización
 */
function deshabilitarActualizacionAutomatica(segundos = 5) {
    window.deshabilitarActualizacionAutomatica = true;
    console.log(`Actualización automática deshabilitada por ${segundos} segundos`);
    
    // Volver a habilitar después del tiempo especificado
    setTimeout(() => {
        window.deshabilitarActualizacionAutomatica = false;
        console.log('Actualización automática habilitada nuevamente');
    }, segundos * 1000);
}

/**
 * Actualiza manualmente el progreso
 */
function forzarActualizacionProgreso() {
    if (window.actualizarProgresoManual) {
        console.log('Forzando actualización manual del progreso');
        window.actualizarProgresoManual();
    } else {
        console.warn('La función de actualización manual no está disponible');
    }
}

// Sobrescribir la función original si existe
if (window.ProgressManager) {
    window.ProgressManager.inicializarProgreso = inicializarProgreso;
    window.ProgressManager.deshabilitarActualizacionAutomatica = deshabilitarActualizacionAutomatica;
    window.ProgressManager.forzarActualizacionProgreso = forzarActualizacionProgreso;
}

// Exportar funciones para uso en otros archivos
window.ProgressManager = window.ProgressManager || {};
Object.assign(window.ProgressManager, {
    inicializarProgreso,
    deshabilitarActualizacionAutomatica,
    forzarActualizacionProgreso
});
