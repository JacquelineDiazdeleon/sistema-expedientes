/**
 * escaneo.js - Módulo de escaneo de documentos
 * Maneja la comunicación con el servicio de escaneo local (NAPS2)
 * Soporta escaneo desde la PC local o desde otros dispositivos en la red
 */

// Configuración del servicio de escaneo
const SCANNER_PORT = 5001;
const SCANNER_LOCAL_URL = `http://127.0.0.1:${SCANNER_PORT}`;

// Obtener URL del servidor de escaneo (puede ser localhost o IP de red)
function getScannerServiceUrl() {
    // Primero verificar si hay una IP guardada en localStorage
    const savedIp = localStorage.getItem('scanner_server_ip');
    if (savedIp) {
        return `http://${savedIp}:${SCANNER_PORT}`;
    }
    return SCANNER_LOCAL_URL;
}

// Guardar IP del servidor de escaneo
function setScannerServerIp(ip) {
    if (ip && ip.trim()) {
        localStorage.setItem('scanner_server_ip', ip.trim());
        console.log(`✅ IP del servidor de escaneo guardada: ${ip}`);
        return true;
    }
    return false;
}

// Limpiar IP guardada (volver a localhost)
function clearScannerServerIp() {
    localStorage.removeItem('scanner_server_ip');
    console.log('✅ IP del servidor de escaneo eliminada. Usando localhost.');
}

// Obtener la IP guardada actual
function getScannerServerIp() {
    return localStorage.getItem('scanner_server_ip') || '127.0.0.1';
}

/**
 * Verificar si el servicio de escaneo está disponible
 * @param {string} customUrl - URL personalizada para verificar (opcional)
 * @returns {Promise<{available: boolean, data?: object, error?: string, url?: string}>}
 */
async function verificarServicioEscaneo(customUrl = null) {
    const urlsToTry = [];
    
    if (customUrl) {
        urlsToTry.push(customUrl);
    } else {
        // Intentar primero con la URL guardada/local
        urlsToTry.push(getScannerServiceUrl());
        
        // Si no es localhost, también intentar localhost
        if (getScannerServiceUrl() !== SCANNER_LOCAL_URL) {
            urlsToTry.push(SCANNER_LOCAL_URL);
        }
    }
    
    for (const url of urlsToTry) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            
            const response = await fetch(`${url}/health`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                return { available: true, data, url };
            }
        } catch (error) {
            console.log(`No se pudo conectar a ${url}: ${error.message}`);
        }
    }
    
    return { 
        available: false, 
        error: 'Servicio de escaneo no disponible. Verifica que esté corriendo.' 
    };
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
    
    // Primero verificar disponibilidad
    const status = await verificarServicioEscaneo();
    if (!status.available) {
        return { success: false, error: status.error };
    }
    
    const scannerUrl = status.url || getScannerServiceUrl();
    
    try {
        const response = await fetch(`${scannerUrl}/scan`, {
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
            error: `Error de conexión: ${error.message}. Verifica que el servicio esté corriendo.` 
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
    const scannerUrl = getScannerServiceUrl();
    
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
            const ipInfo = getScannerServerIp() !== '127.0.0.1' 
                ? ` (IP: ${getScannerServerIp()})` 
                : '';
            statusText.textContent = message || `Servicio no disponible${ipInfo}`;
            statusText.style.color = '#ef4444';
        }
        if (btnEscanear) {
            btnEscanear.disabled = true;
            btnEscanear.title = `El servicio de escaneo no está disponible. Asegúrate de que esté corriendo en ${scannerUrl}`;
        }
    }
}

/**
 * Mostrar diálogo para configurar IP del servidor de escaneo
 */
function mostrarConfiguracionEscaner() {
    const currentIp = getScannerServerIp();
    const newIp = prompt(
        '📡 Configurar servidor de escaneo\n\n' +
        'Si el escáner está conectado a otra computadora en la red, ' +
        'ingresa su dirección IP.\n\n' +
        'Ejemplos:\n' +
        '• 192.168.1.100\n' +
        '• 10.0.0.50\n\n' +
        'Deja vacío o ingresa "127.0.0.1" para usar el escáner local.',
        currentIp
    );
    
    if (newIp === null) return; // Cancelado
    
    if (!newIp.trim() || newIp.trim() === '127.0.0.1' || newIp.trim() === 'localhost') {
        clearScannerServerIp();
        alert('✅ Configurado para usar escáner local');
    } else {
        setScannerServerIp(newIp.trim());
        alert(`✅ Servidor de escaneo configurado: ${newIp.trim()}`);
    }
    
    // Recargar página para aplicar cambios
    location.reload();
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
    SCANNER_PORT,
    SCANNER_LOCAL_URL,
    getScannerServiceUrl,
    setScannerServerIp,
    clearScannerServerIp,
    getScannerServerIp,
    verificarServicioEscaneo,
    iniciarEscaneo,
    actualizarEstadoServicio,
    mostrarConfiguracionEscaner,
    setBotonEscaneoLoading,
    actualizarProgresoEscaneo,
    setProgresoVisible
};

// Log de carga
console.log('✅ Módulo de escaneo cargado correctamente');
console.log(`📡 Servidor de escaneo: ${getScannerServiceUrl()}`);
