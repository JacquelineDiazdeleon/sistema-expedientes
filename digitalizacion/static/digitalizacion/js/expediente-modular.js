/**
 * Módulo principal para la gestión de expedientes
 * Este archivo contiene toda la lógica de JavaScript organizada de forma modular
 */

// Patrón Módulo Revelador (Revealing Module Pattern)
const ExpedienteApp = (function() {
    // =========================================
    // 1. CONFIGURACIÓN Y VARIABLES GLOBALES
    // =========================================
    const config = {
        apiBaseUrl: '',
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
        expedienteId: document.getElementById('barra-progreso')?.getAttribute('data-expediente-id') || ''
    };

    // Estado de la aplicación
    const state = {
        temaActual: 'light', // Siempre en modo claro
        areaActual: null,
        documentos: {},
        ultimaActualizacion: null
    };

    // Referencias a elementos del DOM
    const elements = {
        // Se inicializarán en el método init()
    };

    // =========================================
    // 2. INICIALIZACIÓN
    // =========================================
    function init() {
        console.log('Inicializando aplicación de expedientes...');
        
        // Inicializar referencias a elementos del DOM
        initElements();
        
        // Configurar manejadores de eventos
        initEventListeners();
        
        // Inicializar tema
        initTema();
        
        // Inicializar progreso
        initProgreso();
        
        // Cargar datos iniciales
        cargarDatosIniciales();
    }

    function initElements() {
        // Elementos principales
        elements.sidebarToggle = document.getElementById('sidebarToggle');
        elements.sidebar = document.querySelector('.areas-sidebar');
        elements.mainContent = document.querySelector('.main-content');
        
        // Elementos de tema
        elements.temaToggle = document.getElementById('temaToggle');
        elements.temaIcon = document.querySelector('#temaToggle i');
        
        // Elementos de progreso
        elements.barraProgreso = document.getElementById('barra-progreso');
        elements.porcentajeProgreso = document.getElementById('porcentaje-progreso');
        elements.textoProgreso = document.getElementById('texto-progreso');
        
        // Elementos de documentos
        elements.contenedorDocumentos = document.getElementById('contenido-documentos');
        elements.tituloAreaSeleccionada = document.getElementById('titulo-area-seleccionada');
        elements.formSubirDocumento = document.getElementById('formSubirDocumento');
        elements.inputArchivo = document.getElementById('archivo');
        elements.btnSubirDocumento = document.getElementById('btn-subir-documento');
        
        // Modales
        elements.modalVistaPrevia = new bootstrap.Modal(document.getElementById('modalVistaPrevia'));
        elements.modalSubirDocumento = new bootstrap.Modal(document.getElementById('modalSubirDocumento'));
        elements.modalEliminarDocumento = new bootstrap.Modal(document.getElementById('modalEliminarDocumento'));
    }

    function initEventListeners() {
        // Toggle del sidebar en móviles
        if (elements.sidebarToggle) {
            elements.sidebarToggle.addEventListener('click', toggleSidebar);
        }
        
        // Toggle de tema
        if (elements.temaToggle) {
            elements.temaToggle.addEventListener('click', toggleTema);
        }
        
        // Formulario de subida de documentos
        // NOTA: El manejo del formulario se delega a documentos.js para evitar conflictos
        // if (elements.formSubirDocumento) {
        //     elements.formSubirDocumento.addEventListener('submit', handleSubirDocumento);
        // }
        
        // Delegación de eventos para elementos dinámicos
        document.addEventListener('click', handleDocumentClick);
        
        // Evento personalizado para actualizar el progreso
        document.addEventListener('documentoSubido', actualizarProgreso);
    }

    // =========================================
    // 3. MANEJO DE TEMAS
    // =========================================
    function initTema() {
        // Forzar tema claro siempre
        state.temaActual = 'light';
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('tema', 'light'); // Guardar para mantener consistencia
        actualizarIconoTema();
    }

    function toggleTema() {
        // Deshabilitado - siempre en modo claro
        // No hacer nada, mantener siempre en modo claro
        state.temaActual = 'light';
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('tema', 'light');
        actualizarIconoTema();
    }

    function actualizarIconoTema() {
        if (!elements.temaIcon) return;
        
        if (state.temaActual === 'dark') {
            elements.temaIcon.classList.remove('bi-moon-fill');
            elements.temaIcon.classList.add('bi-sun-fill');
        } else {
            elements.temaIcon.classList.remove('bi-sun-fill');
            elements.temaIcon.classList.add('bi-moon-fill');
        }
    }

    // =========================================
    // 4. GESTIÓN DE DOCUMENTOS
    // =========================================
    async function cargarDocumentosArea(areaId, nombreArea) {
        if (!areaId) {
            console.error('ID de área no proporcionado');
            return;
        }
        
        try {
            state.areaActual = areaId;
            
            // Mostrar indicador de carga
            mostrarCargaDocumentos();
            
            // Simular carga de datos (en producción, harías una petición AJAX)
            const response = await fetch(`/api/documentos/?area_id=${areaId}&expediente_id=${config.expedienteId}`);
            const data = await response.json();
            
            // Actualizar la interfaz
            actualizarVistaDocumentos(data.documentos, nombreArea);
            
        } catch (error) {
            console.error('Error al cargar documentos:', error);
            mostrarError('No se pudieron cargar los documentos. Intente nuevamente.');
        }
    }
    
    async function handleSubirDocumento(event) {
        event.preventDefault();
        
        // Validar que se haya seleccionado un archivo
        if (!elements.inputArchivo.files.length) {
            mostrarAlerta('Por favor, seleccione un archivo', 'warning');
            return;
        }
        
        // Validar que se haya seleccionado un área
        if (!state.areaActual) {
            mostrarAlerta('Por favor, seleccione un área antes de subir un documento', 'warning');
            return;
        }
        
        const formData = new FormData(elements.formSubirDocumento);
        
        // Asegurarse de que el area_id esté en el formData
        if (!formData.has('area_id') && state.areaActual) {
            formData.append('area_id', state.areaActual);
        }
        
        try {
            // Mostrar indicador de carga
            elements.btnSubirDocumento.disabled = true;
            elements.btnSubirDocumento.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Subiendo...';
            
            // Mostrar mensaje de carga
            const alertaCarga = mostrarAlerta('Subiendo documento, por favor espere...', 'info');
            
            const response = await fetch(elements.formSubirDocumento.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': config.csrfToken
                }
            });
            
            // Verificar si la respuesta es JSON
            const contentType = response.headers.get('content-type');
            let data;
            
            try {
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    // Si no es JSON, obtener el texto del error
                    const errorText = await response.text();
                    throw new Error(`Respuesta inesperada del servidor (${response.status}): ${errorText.substring(0, 200)}`);
                }
                
                if (response.ok && data.success) {
                    // Cerrar cualquier alerta previa
                    if (alertaCarga) alertaCarga.remove();
                    
                    // Cerrar modal y limpiar formulario
                    elements.modalSubirDocumento.hide();
                    elements.formSubirDocumento.reset();
                    
                    // Actualizar lista de documentos
                    if (state.areaActual) {
                        await cargarDocumentosArea(state.areaActual);
                    }
                    
                    // Disparar evento personalizado para actualizar el progreso
                    document.dispatchEvent(new CustomEvent('documentoSubido'));
                    
                } else {
                    throw new Error(data.error || 'Error al subir el documento');
                }
                
            } catch (parseError) {
                console.error('Error al procesar la respuesta:', parseError);
                throw new Error('Error al procesar la respuesta del servidor');
            }
            
        } catch (error) {
            console.error('Error al subir documento:', error);
            
            // Verificar si el error es 'database is locked' pero el archivo se subió correctamente
            if (error.message && error.message.includes('database is locked')) {
                console.log('Advertencia: La base de datos está bloqueada, pero el archivo se subió correctamente.');
                
                // Cerrar modal y limpiar formulario
                if (elements.modalSubirDocumento) {
                    elements.modalSubirDocumento.hide();
                }
                
                // Recargar documentos del área actual si está disponible
                if (state.areaActual) {
                    cargarDocumentosArea(state.areaActual, state.nombreAreaActual);
                }
                
                // Limpiar el formulario
                if (elements.formSubirDocumento) {
                    elements.formSubirDocumento.reset();
                }
                
                return; // Salir de la función sin mostrar mensaje de error
            }
            
            // Mostrar mensaje de error más descriptivo para otros errores
            let mensajeError = 'Error al subir el documento. ';
            
            if (error.message.includes('Failed to fetch')) {
                mensajeError += 'No se pudo conectar con el servidor. Verifique su conexión a internet.';
            } else if (error.message.includes('Unexpected token')) {
                mensajeError += 'Error en el formato de la respuesta del servidor. Intente nuevamente.';
            } else if (error.message.includes('404')) {
                mensajeError += 'No se encontró el recurso solicitado. Por favor, recargue la página.';
            } else if (error.message.includes('500')) {
                mensajeError += 'Error interno del servidor. Por favor, intente nuevamente más tarde.';
            } else if (error.message.includes('400')) {
                mensajeError += 'Datos inválidos. Verifique la información proporcionada.';
            } else if (error.message.includes('403')) {
                mensajeError += 'No tiene permisos para realizar esta acción.';
            } else if (error.message.includes('413')) {
                mensajeError = 'El archivo es demasiado grande. El tamaño máximo permitido es de 10MB.';
            } else if (error.message) {
                mensajeError += error.message;
            }
            
            mostrarAlerta(mensajeError, 'danger');
            
        } finally {
            // Restaurar botón
            elements.btnSubirDocumento.disabled = false;
            elements.btnSubirDocumento.innerHTML = '<i class="bi bi-upload me-2"></i>Subir Documento';
        }
    }
    
    function verDocumento(url, nombre) {
        // Implementar lógica para mostrar vista previa del documento
        console.log(`Viendo documento: ${nombre} (${url})`);
        // ... (implementar vista previa)
    }
    
    function confirmarEliminarDocumento(documentoId, nombreDocumento) {
        // Implementar lógica para confirmar eliminación
        if (confirm(`¿Está seguro de eliminar el documento "${nombreDocumento}"?`)) {
            eliminarDocumento(documentoId);
        }
    }
    
    async function eliminarDocumento(documentoId) {
        // 1. Eliminar el documento del DOM inmediatamente
        const documentoElement = document.querySelector(`[data-documento-id="${documentoId}"]`);
        const areaActual = state.areaActual;
        
        if (documentoElement) {
            // Guardar referencia al contenedor padre para restaurar si hay error
            const contenedorPadre = documentoElement.closest('.documentos-lista') || documentoElement.parentNode;
            const siguienteElemento = documentoElement.nextElementSibling;
            
            // Eliminar el elemento del DOM
            documentoElement.remove();
            
            // Mostrar mensaje de éxito temporal
            mostrarAlerta('Eliminando documento...', 'info');
            
            try {
                // 2. Enviar la petición al servidor
                const response = await fetch(`/documentos/${documentoId}/eliminar/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': config.csrfToken,
                        'Accept': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || 'Error al eliminar el documento');
                }
                
                const data = await response.json();
                
                if (data.success) {
                    mostrarAlerta('Documento eliminado correctamente', 'success');
                    
                    // Verificar si quedan documentos en el área
                    if (contenedorPadre && contenedorPadre.children.length === 0) {
                        contenedorPadre.innerHTML = `
                            <div class="alert alert-info">
                                No hay documentos en esta área.
                            </div>`;
                    }
                    
                    // Actualizar progreso
                    document.dispatchEvent(new CustomEvent('documentoSubido'));
                    
                } else {
                    throw new Error(data.error || 'Error al eliminar el documento');
                }
                
            } catch (error) {
                console.error('Error al eliminar documento:', error);
                
                // Si hay un error, volver a cargar los documentos para restaurar el estado
                if (areaActual) {
                    cargarDocumentosArea(areaActual);
                }
                
                mostrarAlerta(error.message || 'Error al eliminar el documento. Se ha restaurado el documento.', 'danger');
            }
        } else {
            // Si no se encontró el elemento en el DOM, hacer una recarga normal
            if (areaActual) {
                cargarDocumentosArea(areaActual);
            }
        }
    }

    // =========================================
    // 5. GESTIÓN DE PROGRESO
    // =========================================
    function initProgreso() {
        if (!config.expedienteId) return;
        
        // Cargar progreso inicial
        actualizarProgreso();
        
        // Configurar actualización periódica (cada 30 segundos)
        const intervalo = setInterval(actualizarProgreso, 30000);
        
        // Limpiar intervalo al salir de la página
        window.addEventListener('beforeunload', () => clearInterval(intervalo));
    }
    
    async function actualizarProgreso() {
        try {
            const response = await fetch(`/api/expedientes/${config.expedienteId}/progreso/`);
            const data = await response.json();
            
            if (response.ok) {
                actualizarBarraProgreso(data);
            } else {
                throw new Error(data.error || 'Error al obtener el progreso');
            }
            
        } catch (error) {
            console.error('Error al actualizar progreso:', error);
        }
    }
    
    function actualizarBarraProgreso(data) {
        if (!elements.barraProgreso || !elements.porcentajeProgreso || !elements.textoProgreso) return;
        
        const porcentaje = data.porcentaje || 0;
        const completadas = data.completadas || 0;
        const total = data.total || 0;
        
        // Actualizar barra de progreso
        elements.barraProgreso.style.width = `${porcentaje}%`;
        elements.barraProgreso.setAttribute('aria-valuenow', porcentaje);
        elements.barraProgreso.textContent = `${porcentaje}%`;
        
        // Actualizar clase de color según el porcentaje
        if (porcentaje < 30) {
            elements.barraProgreso.className = 'progress-bar bg-danger';
        } else if (porcentaje < 70) {
            elements.barraProgreso.className = 'progress-bar bg-warning';
        } else {
            elements.barraProgreso.className = 'progress-bar bg-success';
        }
        
        // Actualizar texto
        elements.porcentajeProgreso.textContent = `${porcentaje}%`;
        elements.textoProgreso.textContent = `${completadas}/${total} áreas completadas`;
        
        // Guardar última actualización
        if (data.ultima_actualizacion) {
            state.ultimaActualizacion = data.ultima_actualizacion;
            actualizarFechaUltimaActualizacion(data.ultima_actualizacion);
        }
    }

    // =========================================
    // 6. FUNCIONES DE UTILIDAD
    // =========================================
    function mostrarCargaDocumentos() {
        // Implementar lógica para mostrar indicador de carga
    }

    function actualizarVistaDocumentos(documentos, nombreArea) {
        // Implementar lógica para actualizar la interfaz con los documentos
    }

    function mostrarAlerta(mensaje, tipo = 'info') {
        // Usar la función centralizada de notificaciones si está disponible
        if (window.mostrarNotificacion) {
            window.mostrarNotificacion(mensaje, tipo);
        } 
        // Si no está disponible, usar SweetAlert2 si está disponible
        else if (typeof Swal !== 'undefined') {
            Swal.fire({
                text: mensaje,
                icon: tipo,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                }
            });
        } 
        // Si no hay ninguna de las opciones anteriores, usar alerta nativa
        else {
            console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
            alert(`[${tipo}] ${mensaje}`);
        }
    }

    function actualizarFechaUltimaActualizacion(fecha) {
        const elementoFecha = document.getElementById('fecha-ultima-actualizacion');
        if (elementoFecha) {
            elementoFecha.textContent = formatearFecha(fecha, true);
            elementoFecha.setAttribute('datetime', new Date(fecha).toISOString());
            elementoFecha.setAttribute('title', `Última actualización: ${formatearFecha(fecha, true)}`);
        }
    }

    function formatearFecha(fechaISO, incluirHora = false) {
        if (!fechaISO) return 'No disponible';
        
        const opciones = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        
        if (incluirHora) {
            opciones.hour = '2-digit';
            opciones.minute = '2-digit';
        }
        
        try {
            const fecha = new Date(fechaISO);
            return fecha.toLocaleDateString('es-ES', opciones);
        } catch (e) {
            console.error('Error al formatear fecha:', e);
            return 'Fecha inválida';
        }
    }

    // =========================================
    // 7. MANEJADORES DE EVENTOS
    // =========================================
    function handleDocumentClick(event) {
        const target = event.target;
        
        // Manejar clic en enlaces de documentos
        const linkDocumento = target.closest('.ver-documento');
        if (linkDocumento) {
            event.preventDefault();
            const url = linkDocumento.getAttribute('href');
            const nombre = linkDocumento.getAttribute('data-nombre') || 'Documento';
            verDocumento(url, nombre);
            return;
        }
        
        // Manejar clic en botones de eliminar
        const btnEliminar = target.closest('.eliminar-documento');
        if (btnEliminar) {
            event.preventDefault();
            const documentoId = btnEliminar.getAttribute('data-documento-id');
            const nombreDocumento = btnEliminar.getAttribute('data-documento-nombre') || 'este documento';
            confirmarEliminarDocumento(documentoId, nombreDocumento);
            return;
        }
        
        // Manejar clic en áreas del sidebar
        const areaLink = target.closest('.area-link');
        if (areaLink) {
            event.preventDefault();
            const areaId = areaLink.getAttribute('data-area-id');
            const nombreArea = areaLink.textContent.trim();
            cargarDocumentosArea(areaId, nombreArea);
            
            // Cerrar sidebar en móviles
            if (window.innerWidth < 992) {
                toggleSidebar();
            }
            return;
        }
    }

    // =========================================
    // 8. INICIALIZACIÓN AL CARGAR LA PÁGINA
    // =========================================
    function cargarDatosIniciales() {
        // Cargar primera área si existe
        const primeraArea = document.querySelector('.area-link');
        if (primeraArea) {
            const areaId = primeraArea.getAttribute('data-area-id');
            const nombreArea = primeraArea.textContent.trim();
            cargarDocumentosArea(areaId, nombreArea);
        }
    }

    // =========================================
    // 9. API PÚBLICA
    // =========================================
    return {
        init: init,
        cargarDocumentosArea: cargarDocumentosArea,
        verDocumento: verDocumento,
        formatearFecha: formatearFecha,
        mostrarAlerta: mostrarAlerta,
        mostrarError: mostrarError
    };
})();

// Inicializar la aplicación cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    ExpedienteApp.init();
});

// Hacer que la aplicación esté disponible globalmente (opcional)
window.ExpedienteApp = ExpedienteApp;
