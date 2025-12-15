/**
 * escaneo.js - Módulo de escaneo de documentos
 * Maneja la comunicación con el servicio de escaneo local (NAPS2)
 * Soporta escaneo desde la PC local o escaneo remoto vía servidor web
 * 
 * MODO LOCAL: Escaneo directo si el servicio local está disponible
 * MODO REMOTO: Crea solicitud en el servidor, la PC con el escáner la procesa
 */

// Configuración del servicio de escaneo
const SCANNER_PORT = 5001;
const SCANNER_LOCAL_URL = `http://127.0.0.1:${SCANNER_PORT}`;

// Estado del modo de escaneo
let modoEscaneoRemoto = false;
let solicitudActiva = null;

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
 * Intenta primero el modo local, si no está disponible usa el modo remoto
 * @param {Object} params - Parámetros del escaneo
 * @param {number} params.expedienteId - ID del expediente
 * @param {string|number} params.areaId - ID del área
 * @param {string} params.nombreDocumento - Nombre del documento
 * @param {string} params.descripcion - Descripción opcional
 * @param {boolean} params.duplex - Escanear ambos lados (opcional)
 * @param {boolean} params.forzarRemoto - Forzar modo remoto (opcional)
 * @returns {Promise<{success: boolean, data?: object, error?: string, modo?: string}>}
 */
async function iniciarEscaneo(params) {
    const { expedienteId, areaId, nombreDocumento, descripcion = '', duplex = false, forzarRemoto = false } = params;
    
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
    
    // Si no se fuerza remoto, primero intentar modo local
    if (!forzarRemoto) {
        const status = await verificarServicioEscaneo();
        if (status.available) {
            return await iniciarEscaneoLocal(params, status.url);
        }
    }
    
    // Si llegamos aquí, usar modo remoto
    console.log('📡 Servicio local no disponible, usando modo REMOTO');
    return await iniciarEscaneoRemoto(params);
}

/**
 * Iniciar escaneo en modo local (servicio en la misma máquina o red)
 */
async function iniciarEscaneoLocal(params, scannerUrl) {
    const { expedienteId, areaId, nombreDocumento, descripcion = '', duplex = false } = params;
    
    scannerUrl = scannerUrl || getScannerServiceUrl();
    
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
                descripcion: descripcion.trim(),
                duplex: duplex
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
            return { success: true, data, modo: 'local' };
        } else {
            return { 
                success: false, 
                error: data.msg || data.error || 'Error desconocido al escanear',
                modo: 'local'
            };
        }
    } catch (error) {
        console.error('Error de conexión con el servicio de escaneo local:', error);
        return { 
            success: false, 
            error: `Error de conexión: ${error.message}`,
            modo: 'local'
        };
    }
}

/**
 * Iniciar escaneo en modo remoto (solicitud al servidor web)
 * La PC con el escáner procesará la solicitud automáticamente
 */
async function iniciarEscaneoRemoto(params) {
    const { expedienteId, areaId, nombreDocumento, descripcion = '', duplex = false } = params;
    
    try {
        // Obtener CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value 
                       || document.querySelector('meta[name="csrf-token"]')?.content
                       || '';
        
        const response = await fetch('/api/escaneo/solicitar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                expediente_id: expedienteId,
                area_id: parseInt(areaId),
                nombre_documento: nombreDocumento.trim(),
                descripcion: descripcion.trim(),
                duplex: duplex
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            solicitudActiva = data.solicitud_id;
            modoEscaneoRemoto = true;
            
            return { 
                success: true, 
                data: {
                    solicitud_id: data.solicitud_id,
                    mensaje: data.mensaje
                },
                modo: 'remoto',
                pendiente: true  // Indica que hay que esperar
            };
        } else {
            return { 
                success: false, 
                error: data.error || 'Error al crear solicitud de escaneo',
                modo: 'remoto'
            };
        }
    } catch (error) {
        console.error('Error al crear solicitud de escaneo remoto:', error);
        return { 
            success: false, 
            error: `Error de conexión: ${error.message}`,
            modo: 'remoto'
        };
    }
}

/**
 * Verificar el estado de una solicitud de escaneo remoto
 * @param {number} solicitudId - ID de la solicitud
 * @returns {Promise<{success: boolean, estado: string, completado: boolean, error?: string}>}
 */
async function verificarSolicitudEscaneo(solicitudId) {
    try {
        const response = await fetch(`/api/escaneo/${solicitudId}/estado/`);
        const data = await response.json();
        
        if (response.ok && data.success) {
            const solicitud = data.solicitud;
            return {
                success: true,
                estado: solicitud.estado,
                completado: solicitud.estado === 'completado',
                error: solicitud.estado === 'error' ? solicitud.mensaje_error : null,
                documento_id: solicitud.documento_id
            };
        } else {
            return { success: false, error: data.error };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Esperar a que una solicitud de escaneo remoto se complete
 * @param {number} solicitudId - ID de la solicitud
 * @param {function} onProgress - Callback para actualizar progreso (opcional)
 * @param {number} maxIntentos - Número máximo de intentos (por defecto 60 = 5 minutos)
 * @returns {Promise<{success: boolean, data?: object, error?: string}>}
 */
async function esperarSolicitudEscaneo(solicitudId, onProgress = null, maxIntentos = 60) {
    let intentos = 0;
    const intervalo = 5000; // 5 segundos
    
    while (intentos < maxIntentos) {
        intentos++;
        
        // Callback de progreso
        if (onProgress) {
            const progreso = Math.min(90, (intentos / maxIntentos) * 100);
            let mensaje = 'Esperando escaneo...';
            if (intentos > 2) mensaje = 'Procesando escaneo...';
            if (intentos > 10) mensaje = 'Subiendo documento...';
            onProgress(progreso, mensaje, intentos);
        }
        
        // Verificar estado
        const estado = await verificarSolicitudEscaneo(solicitudId);
        
        if (!estado.success) {
            // Error al verificar, reintentar
            await sleep(intervalo);
            continue;
        }
        
        if (estado.completado) {
            solicitudActiva = null;
            return {
                success: true,
                data: {
                    status: 'ok',
                    msg: 'Documento escaneado y subido correctamente',
                    documento_id: estado.documento_id
                }
            };
        }
        
        if (estado.error) {
            solicitudActiva = null;
            return {
                success: false,
                error: estado.error
            };
        }
        
        if (estado.estado === 'cancelado') {
            solicitudActiva = null;
            return {
                success: false,
                error: 'La solicitud fue cancelada'
            };
        }
        
        // Esperar antes de la siguiente verificación
        await sleep(intervalo);
    }
    
    // Timeout
    solicitudActiva = null;
    return {
        success: false,
        error: 'Tiempo de espera agotado. La solicitud puede seguir procesándose en segundo plano.'
    };
}

/**
 * Cancelar solicitud de escaneo activa
 */
async function cancelarSolicitudEscaneo() {
    if (!solicitudActiva) return { success: false, error: 'No hay solicitud activa' };
    
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        
        const response = await fetch(`/api/escaneo/${solicitudActiva}/cancelar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            solicitudActiva = null;
            return { success: true };
        } else {
            return { success: false, error: data.error };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Helper para esperar
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Verificar si hay una solicitud de escaneo activa
 */
function haySolicitudActiva() {
    return solicitudActiva !== null;
}

/**
 * Obtener ID de solicitud activa
 */
function getSolicitudActiva() {
    return solicitudActiva;
}

/**
 * Actualizar el estado visual del servicio de escaneo
 * @param {HTMLElement} statusIndicator - Indicador visual de estado
 * @param {HTMLElement} statusText - Texto de estado
 * @param {HTMLElement} btnEscanear - Botón de escanear
 * @param {boolean} available - Si el servicio local está disponible
 * @param {string} message - Mensaje de estado opcional
 */
function actualizarEstadoServicio(statusIndicator, statusText, btnEscanear, available, message = '') {
    const scannerUrl = getScannerServiceUrl();
    
    if (available) {
        // Servicio LOCAL disponible
        modoEscaneoRemoto = false;
        if (statusIndicator) {
            statusIndicator.classList.remove('inactive', 'remote');
            statusIndicator.classList.add('active');
        }
        if (statusText) {
            statusText.textContent = message || '🖨️ Escáner local disponible';
            statusText.style.color = '#10b981';
        }
        if (btnEscanear) {
            btnEscanear.disabled = false;
            btnEscanear.title = 'Escanear directamente desde este equipo';
        }
    } else {
        // Servicio local NO disponible -> Usar modo REMOTO
        modoEscaneoRemoto = true;
        if (statusIndicator) {
            statusIndicator.classList.remove('active', 'inactive');
            statusIndicator.classList.add('remote');
        }
        if (statusText) {
            statusText.textContent = '📡 Modo remoto: El escaneo se enviará a la PC con el escáner';
            statusText.style.color = '#f59e0b';  // Naranja/amarillo para modo remoto
        }
        if (btnEscanear) {
            // En modo remoto, el botón SÍ está habilitado
            btnEscanear.disabled = false;
            btnEscanear.title = 'Crear solicitud de escaneo (se procesará en la PC con el escáner)';
        }
    }
}

/**
 * Verificar si estamos en modo remoto
 */
function esModoRemoto() {
    return modoEscaneoRemoto;
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
    // Configuración
    SCANNER_PORT,
    SCANNER_LOCAL_URL,
    getScannerServiceUrl,
    setScannerServerIp,
    clearScannerServerIp,
    getScannerServerIp,
    
    // Verificación
    verificarServicioEscaneo,
    
    // Escaneo
    iniciarEscaneo,
    iniciarEscaneoLocal,
    iniciarEscaneoRemoto,
    
    // Solicitudes remotas
    verificarSolicitudEscaneo,
    esperarSolicitudEscaneo,
    cancelarSolicitudEscaneo,
    haySolicitudActiva,
    getSolicitudActiva,
    esModoRemoto,
    
    // UI
    actualizarEstadoServicio,
    mostrarConfiguracionEscaner,
    setBotonEscaneoLoading,
    actualizarProgresoEscaneo,
    setProgresoVisible
};

// Log de carga
console.log('✅ Módulo de escaneo v2.0 cargado correctamente');
console.log(`📡 Servidor de escaneo local: ${getScannerServiceUrl()}`);
console.log('📡 Modo remoto habilitado: El escaneo funcionará desde cualquier dispositivo');
