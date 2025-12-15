/**
 * escaneo.js - Módulo de escaneo de documentos
 * Maneja la comunicación con el servicio de escaneo local (NAPS2)
 */

// Configuración del servicio de escaneo
const SCANNER_SERVICE_URL = 'http://127.0.0.1:5001';

/**
 * Verificar si el servicio de escaneo está disponible
 * @returns {Promise<{available: boolean, data?: object, error?: string}>}
 */
async function verificarServicioEscaneo() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(`${SCANNER_SERVICE_URL}/health`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            return { available: true, data };
        } else {
            return { available: false, error: 'Servicio no disponible' };
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            return { available: false, error: 'Timeout al conectar con el servicio' };
        }
        return { available: false, error: error.message };
    }
}

/**
 * Iniciar escaneo de documento
 * @param {Object} params - Parámetros del escaneo
 * @param {number} params.expedienteId - ID del expediente
 * @param {string|number} params.areaId - ID del área
 * @param {string} params.nombreDocumento - Nombre del documento
 * @param {string} params.descripcion - Descripción opcional
 * @returns {Promise<{success: boolean, data?: object, error?: string}>}
 */
async function iniciarEscaneo(params) {
    const { expedienteId, areaId, nombreDocumento, descripcion = '' } = params;
    
    // Validaciones
    if (!expedienteId) {
        return { success: false, error: 'ID de expediente requerido' };
    }
    if (!areaId) {
        return { success: false, error: 'ID de área requerido' };
    }
    if (!nombreDocumento || !nombreDocumento.trim()) {
        return { success: false, error: 'Nombre del documento requerido' };
    }
    
    try {
        const response = await fetch(`${SCANNER_SERVICE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                expediente_id: expedienteId,
                etapa: areaId,
                area_id: parseInt(areaId),
                nombre_documento: nombreDocumento.trim(),
                descripcion: descripcion.trim()
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
            return { success: true, data };
        } else {
            return { 
                success: false, 
                error: data.msg || data.error || 'Error desconocido al escanear' 
            };
        }
    } catch (error) {
        console.error('Error de conexión con el servicio de escaneo:', error);
        return { 
            success: false, 
            error: `Error de conexión: ${error.message}. Verifica que el servicio esté corriendo en ${SCANNER_SERVICE_URL}` 
        };
    }
}

/**
 * Actualizar el estado visual del servicio de escaneo
 * @param {HTMLElement} statusIndicator - Indicador visual de estado
 * @param {HTMLElement} statusText - Texto de estado
 * @param {HTMLElement} btnEscanear - Botón de escanear
 * @param {boolean} available - Si el servicio está disponible
 * @param {string} message - Mensaje de estado opcional
 */
function actualizarEstadoServicio(statusIndicator, statusText, btnEscanear, available, message = '') {
    if (available) {
        if (statusIndicator) {
            statusIndicator.classList.remove('inactive');
            statusIndicator.classList.add('active');
        }
        if (statusText) {
            statusText.textContent = message || 'Servicio disponible y listo';
            statusText.style.color = '#10b981';
        }
        if (btnEscanear) {
            btnEscanear.disabled = false;
            btnEscanear.title = '';
        }
    } else {
        if (statusIndicator) {
            statusIndicator.classList.remove('active');
            statusIndicator.classList.add('inactive');
        }
        if (statusText) {
            statusText.textContent = message || 'Servicio no disponible';
            statusText.style.color = '#ef4444';
        }
        if (btnEscanear) {
            btnEscanear.disabled = true;
            btnEscanear.title = `El servicio de escaneo no está disponible. Asegúrate de que esté corriendo en ${SCANNER_SERVICE_URL}`;
        }
    }
}

/**
 * Mostrar/ocultar estado de carga en el botón de escaneo
 * @param {HTMLElement} btn - Botón de escanear
 * @param {boolean} loading - Si está cargando
 */
function setBotonEscaneoLoading(btn, loading) {
    if (!btn) return;
    
    const btnContent = btn.querySelector('.btn-scan-content');
    const btnLoading = btn.querySelector('.btn-scan-loading');
    
    btn.disabled = loading;
    
    if (loading) {
        if (btnContent) btnContent.classList.add('d-none');
        if (btnLoading) btnLoading.classList.remove('d-none');
    } else {
        if (btnContent) btnContent.classList.remove('d-none');
        if (btnLoading) btnLoading.classList.add('d-none');
    }
}

/**
 * Actualizar barra de progreso del escaneo
 * @param {HTMLElement} progressBar - Barra de progreso
 * @param {HTMLElement} progressText - Texto de progreso
 * @param {number} porcentaje - Porcentaje de progreso (0-100)
 * @param {string} texto - Texto a mostrar
 */
function actualizarProgresoEscaneo(progressBar, progressText, porcentaje, texto) {
    if (progressBar) {
        progressBar.style.width = `${porcentaje}%`;
    }
    if (progressText) {
        progressText.textContent = texto;
    }
}

/**
 * Mostrar/ocultar contenedor de progreso
 * @param {HTMLElement} progressContainer - Contenedor de progreso
 * @param {boolean} visible - Si debe ser visible
 */
function setProgresoVisible(progressContainer, visible) {
    if (!progressContainer) return;
    
    if (visible) {
        progressContainer.classList.remove('d-none');
    } else {
        progressContainer.classList.add('d-none');
    }
}

// Exportar funciones para uso global
window.EscaneoUtils = {
    SCANNER_SERVICE_URL,
    verificarServicioEscaneo,
    iniciarEscaneo,
    actualizarEstadoServicio,
    setBotonEscaneoLoading,
    actualizarProgresoEscaneo,
    setProgresoVisible
};

// Log de carga
console.log('✅ Módulo de escaneo cargado correctamente');

