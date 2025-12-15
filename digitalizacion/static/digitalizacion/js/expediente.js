/**
 * Archivo principal de JavaScript para el detalle de expediente
 * Maneja la lógica principal de la interfaz de usuario y las interacciones
 * 
 * Este archivo sirve como punto de entrada principal y coordina los diferentes
 * módulos de la aplicación.
 */

// Variables globales
let areaSeleccionada = null;

/**
 * Objeto principal de la aplicación
 * Maneja la inicialización y coordinación de los módulos
 */
const ExpedienteApp = {
    // Inicialización de la aplicación
    init: function() {
        console.log('Inicializando aplicación de expediente');
        this.initTema();
        this.initManejadorAreas();
        this.initEventListeners();
        this.cargarDatosIniciales();
        
        // Inicializar módulos
        if (typeof DocumentosApp !== 'undefined') {
            DocumentosApp.init();
        } else {
            console.warn('Módulo DocumentosApp no encontrado');
        }
        
        if (typeof ProgresoApp !== 'undefined') {
            ProgresoApp.init();
        } else {
            console.warn('Módulo ProgresoApp no encontrado');
        }
        
        console.log('Aplicación de expediente inicializada correctamente');
    },

    // Inicializar el tema - siempre en modo claro
    initTema: function() {
        // Forzar tema claro siempre
        const temaGuardado = 'light';
        document.documentElement.setAttribute('data-theme', temaGuardado);
        localStorage.setItem('tema', temaGuardado); // Guardar para mantener consistencia
        this.actualizarIconosTema(temaGuardado);
    },

    // Alternar entre temas claro/oscuro - Deshabilitado, siempre en modo claro
    toggleTema: function() {
        // Forzar siempre modo claro
        const nuevoTema = 'light';
        document.documentElement.setAttribute('data-theme', nuevoTema);
        localStorage.setItem('tema', nuevoTema);
        this.actualizarIconosTema(nuevoTema);
    },

    // Actualizar los íconos según el tema
    actualizarIconosTema: function(tema) {
        const iconoClaro = document.getElementById('icono-tema-claro');
        const iconoOscuro = document.getElementById('icono-tema-oscuro');
        
        if (tema === 'dark') {
            if (iconoClaro) iconoClaro.classList.add('d-none');
            if (iconoOscuro) iconoOscuro.classList.remove('d-none');
        } else {
            if (iconoClaro) iconoClaro.classList.remove('d-none');
            if (iconoOscuro) iconoOscuro.classList.add('d-none');
        }
    },

    // Inicializar manejador de áreas
    initManejadorAreas: function() {
        console.log('Inicializando manejador de áreas...');
        
        // Asignar manejador de eventos a cada área
        document.querySelectorAll('.area-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const areaId = item.getAttribute('data-area-id');
                const areaNombre = item.getAttribute('data-area-nombre');
                
                // Actualizar la clase activa
                document.querySelectorAll('.area-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                
                // Cargar documentos del área
                this.cargarDocumentosArea(areaId, areaNombre);
            });
        });
        
        // Cargar automáticamente el área activa
        const areaActiva = document.querySelector('.area-item.active');
        if (areaActiva) {
            const areaId = areaActiva.getAttribute('data-area-id');
            const areaNombre = areaActiva.getAttribute('data-area-nombre');
            this.cargarDocumentosArea(areaId, areaNombre);
        }
    },

    // Inicializar manejadores de eventos
    initEventListeners: function() {
        // Toggle sidebar en móviles
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Toggle tema
        const toggleTemaBtn = document.getElementById('toggleTema');
        if (toggleTemaBtn) {
            toggleTemaBtn.addEventListener('click', () => this.toggleTema());
        }
        
        // Cerrar sesión
        const cerrarSesionBtn = document.getElementById('cerrarSesion');
        if (cerrarSesionBtn) {
            cerrarSesionBtn.addEventListener('click', () => {
                window.location.href = '{% url "logout" %}';
            });
        }
    },

    // Cargar datos iniciales
    cargarDatosIniciales: function() {
        console.log('Cargando datos iniciales...');
        // Aquí se pueden cargar datos iniciales si es necesario
    },

    // Alternar visibilidad del sidebar
    toggleSidebar: function() {
        const sidebar = document.querySelector('.areas-sidebar');
        const mainContent = document.querySelector('.main-content');
        if (sidebar && mainContent) {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }
    },

    /**
     * Carga los documentos de un área específica
     * @param {string} areaId - ID del área
     * @param {string} nombreArea - Nombre del área
     */
    cargarDocumentosArea: function(areaId, nombreArea) {
        console.log('Cargando documentos para el área:', { areaId, nombreArea });
        
        if (!areaId) {
            const errorMsg = 'Error: No se proporcionó un ID de área válido';
            console.error(errorMsg);
            this.mostrarNotificacion('No se proporcionó un ID de área válido', 'error');
            return;
        }
        
        try {
            // Actualizar el área seleccionada
            areaSeleccionada = { id: areaId, nombre: nombreArea };
            
            // Actualizar el título del área en la interfaz
            const tituloAreaElement = document.getElementById('titulo-area-seleccionada');
            if (tituloAreaElement) {
                tituloAreaElement.textContent = nombreArea || 'Área sin nombre';
            }
            
            // Ocultar la pantalla de bienvenida
            const bienvenidaElement = document.getElementById('bienvenida-area');
            if (bienvenidaElement) {
                bienvenidaElement.classList.add('d-none');
            }
            
            // Mostrar indicador de carga
            this.mostrarCargaDocumentos();
            
            // Delegar al módulo de documentos si está disponible
            if (typeof DocumentosApp !== 'undefined') {
                if (typeof DocumentosApp.cargarDocumentosArea === 'function') {
                    console.log('Delegando a DocumentosApp.cargarDocumentosArea con areaId:', areaId, 'tipo:', typeof areaId);
                    DocumentosApp.cargarDocumentosArea(areaId, nombreArea);
                } else {
                    console.warn('DocumentosApp.cargarDocumentosArea no es una función');
                    this.mostrarNotificacion('Error al cargar documentos: función no disponible', 'error');
                }
            } else {
                console.warn('DocumentosApp no está definido');
                this.mostrarNotificacion('Error: Módulo de documentos no disponible', 'error');
            }
        } catch (error) {
            console.error('Error en cargarDocumentosArea:', error);
            this.mostrarNotificacion('Error al cargar los documentos', 'error');
        }
    },

    // Mostrar indicador de carga de documentos
    mostrarCargaDocumentos: function() {
        const contenedor = document.getElementById('contenido-documentos');
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <span class="ms-2">Cargando documentos...</span>
                </div>`;
        }
    },

    /**
     * Muestra una notificación al usuario
     * @param {string} mensaje - Mensaje a mostrar
     * @param {string} tipo - Tipo de notificación (success, error, warning, info)
     */
    mostrarNotificacion: function(mensaje, tipo = 'info') {
        // Usar la función centralizada de notificaciones si está disponible
        if (window.mostrarNotificacion) {
            window.mostrarNotificacion(mensaje, tipo);
        } else {
            // Implementación de respaldo en caso de que la función centralizada no esté disponible
            console.warn('La función centralizada de notificaciones no está disponible');
            
            // Verificar si existe el contenedor de notificaciones
            let notificaciones = document.getElementById('notificaciones');
            if (!notificaciones) {
                // Crear el contenedor si no existe
                notificaciones = document.createElement('div');
                notificaciones.id = 'notificaciones';
                notificaciones.className = 'position-fixed top-0 end-0 p-3';
                notificaciones.style.zIndex = '1100';
                document.body.appendChild(notificaciones);
            }
            
            // Crear la notificación
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
            alertDiv.role = 'alert';
            alertDiv.innerHTML = `
                ${mensaje}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
            `;
            
            // Agregar la notificación al contenedor
            notificaciones.appendChild(alertDiv);
            
            // Eliminar la notificación después de 5 segundos
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 5000);
        }
    },
    
    /**
     * Abre el modal para subir un documento
     * @param {string} areaId - ID del área
     * @param {string} areaNombre - Nombre del área
     */
    abrirModalSubirDocumento: function(areaId, areaNombre) {
        console.log('=== ABRIR MODAL SUBIR DOCUMENTO ===');
        console.log('areaId recibido:', areaId, 'tipo:', typeof areaId);
        console.log('areaNombre recibido:', areaNombre);
        try {
            // Si no se proporcionó un areaId, intentar obtenerlo del área activa
            if (!areaId || areaId === 'undefined' || areaId === 'null' || areaId === '') {
                console.log('No se proporcionó areaId, intentando obtener del área activa...');
                const areaActiva = document.querySelector('.area-item.active');
                if (areaActiva) {
                    areaId = areaActiva.getAttribute('data-area-id');
                    areaNombre = areaNombre || areaActiva.getAttribute('data-area-nombre');
                    console.log('Área activa encontrada:', areaId, areaNombre);
                } else if (window.areaSeleccionada && window.areaSeleccionada.id) {
                    areaId = window.areaSeleccionada.id;
                    areaNombre = areaNombre || window.areaSeleccionada.nombre;
                    console.log('Área obtenida de areaSeleccionada:', areaId, areaNombre);
                } else if (typeof DocumentosApp !== 'undefined' && DocumentosApp.areaActual && DocumentosApp.areaActual.id) {
                    areaId = DocumentosApp.areaActual.id;
                    areaNombre = areaNombre || DocumentosApp.areaActual.nombre;
                    console.log('Área obtenida de DocumentosApp.areaActual:', areaId, areaNombre);
                } else {
                    console.error('Error: No se proporcionó un ID de área válido y no hay área activa');
                    throw new Error('No se pudo determinar el área. Por favor, selecciona un área primero y luego intenta subir un documento.');
                }
            }
            
            // Asegurarse de que el ID del área sea un número
            let areaIdNum;
            if (typeof areaId === 'object' && areaId !== null) {
                console.warn('Se recibió un objeto como areaId, extrayendo valor...', areaId);
                areaIdNum = parseInt(areaId.id || areaId.value || Object.values(areaId)[0], 10);
            } else if (typeof areaId === 'string') {
                // Convertir string a número
                areaIdNum = parseInt(areaId.trim(), 10);
                console.log('Convertiendo string areaId a número:', areaId, '->', areaIdNum);
            } else {
                areaIdNum = parseInt(areaId, 10);
            }

            if (isNaN(areaIdNum) || areaIdNum <= 0) {
                console.error('ID de área no válido:', areaId);
                throw new Error('No se pudo determinar el área. Por favor, cierra el modal y vuelve a abrirlo desde un área.');
            }

            // Actualizar el campo oculto del formulario con el ID del área
            const areaIdInput = document.getElementById('area_id');
            console.log('areaIdInput encontrado:', areaIdInput);
            if (!areaIdInput) {
                console.error('No se encontró el campo area_id en el formulario');
                throw new Error('No se encontró el campo area_id en el formulario');
            }

            // Establecer el valor numérico del área
            areaIdInput.value = areaIdNum;
            console.log('ID de área establecido en el formulario:', areaIdInput.value);
            console.log('Verificación inmediata - areaIdInput.value después de establecer:', document.getElementById('area_id').value);
            
            // También actualizar la variable global para futuras referencias
            if (typeof window !== 'undefined') {
                window.areaSeleccionada = { id: areaIdNum, nombre: areaNombre };
                console.log('window.areaSeleccionada actualizado:', window.areaSeleccionada);
            }
            
            // Actualizar el título del modal con el nombre del área
            const modalTitle = document.querySelector('#subirDocumentoModal .modal-title');
            if (modalTitle) {
                if (areaNombre) {
                    modalTitle.textContent = `Subir Documento - ${areaNombre}`;
                } else {
                    // Si no hay nombre, intentar obtenerlo del área
                    const areaElement = document.querySelector(`[data-area-id="${areaIdNum}"]`);
                    if (areaElement) {
                        const nombre = areaElement.getAttribute('data-area-nombre') || 'Área ' + areaIdNum;
                        modalTitle.textContent = `Subir Documento - ${nombre}`;
                    } else {
                        modalTitle.textContent = 'Subir Documento';
                    }
                }
            }
            
            // Verificar si Bootstrap está disponible
            if (typeof bootstrap !== 'undefined') {
                // Obtener el elemento del modal
                const modalElement = document.getElementById('subirDocumentoModal');
                if (!modalElement) {
                    console.error('No se encontró el elemento del modal');
                    return;
                }
                
                // Cerrar el modal si ya está abierto
                if (window.subirDocumentoModal) {
                    window.subirDocumentoModal.hide();
                    window.subirDocumentoModal.dispose();
                }
                
                // Crear una nueva instancia del modal
                window.subirDocumentoModal = new bootstrap.Modal(modalElement, {
                    backdrop: 'static',
                    keyboard: false
                });
                
                // Mostrar el modal
                window.subirDocumentoModal.show();
                
                // Forzar el foco en el campo de archivo
                setTimeout(() => {
                    const fileInput = document.getElementById('documento');
                    if (fileInput) fileInput.focus();
                }, 500);
            } else {
                console.error('Bootstrap no está disponible');
                throw new Error('No se pudo cargar la interfaz de usuario. Por favor, recarga la página.');
            }
        } catch (error) {
            console.error('Error al abrir el modal:', error);
            // Mostrar un mensaje de error al usuario
            this.mostrarNotificacion('Error al abrir el formulario de subida de documentos: ' + (error.message || 'Error desconocido'), 'danger');
        }
    },

    // Función para manejar la subida de documentos
    manejarSubidaDocumento: async function() {
        const form = document.getElementById('formSubirDocumento');
        const fileInput = document.getElementById('documento');
        
        if (!form || !fileInput) {
            console.error('No se encontró el formulario o el campo de archivo');
            this.mostrarNotificacion('Error: No se pudo acceder al formulario de subida', 'danger');
            return;
        }
        
        const uploadAlert = document.getElementById('uploadAlert');
        const uploadSpinner = document.getElementById('uploadSpinner');
        const submitBtn = form.querySelector('button[type="submit"]');
        const submitText = submitBtn?.querySelector('.submit-text');
        
        try {
            // Mostrar estado de carga
            if (submitBtn) {
                submitBtn.disabled = true;
                if (submitText) submitText.textContent = 'Subiendo...';
            }
            if (uploadSpinner) uploadSpinner.classList.remove('d-none');
            
            // Validar archivo
            if (fileInput.files.length === 0) {
                throw new Error('Por favor seleccione un archivo');
            }

            // Validar tamaño máximo del archivo (10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (fileInput.files[0].size > maxSize) {
                throw new Error('El archivo es demasiado grande. El tamaño máximo permitido es 10MB.');
            }

            // Obtener el nombre del área del título del modal
            const modalTitle = document.querySelector('#subirDocumentoModal .modal-title');
            let nombreArea = 'Área';
            
            if (modalTitle) {
                const titleText = modalTitle.textContent;
                const match = titleText.match(/Subir Documento - (.+)/);
                if (match && match[1]) {
                    nombreArea = match[1].trim();
                }
            }
            
            console.log('Iniciando subida de documento para área:', nombreArea);

            // Obtener el token CSRF
            const csrftoken = this.getCookie('csrftoken');
            if (!csrftoken) {
                throw new Error('No se pudo obtener el token CSRF');
            }

            // Preparar datos del formulario
            const formData = new FormData(form);
            
            // Asegurarse de que el nombre del área esté correctamente establecido
            formData.set('area_nombre', nombreArea);
            
            // Usar la URL sin etapa, obteniendo el ID del expediente de window.expedienteData
            const expedienteId = window.expedienteData?.id;
            if (!expedienteId) {
                throw new Error('No se pudo obtener el ID del expediente');
            }
            const url = `/expedientes/${expedienteId}/subir-documento/`;
            console.log('Enviando documento a:', url, 'para área:', nombreArea);
            
            // Mostrar los datos que se están enviando
            console.log('Datos del formulario:');
            for (let [key, value] of formData.entries()) {
                console.log(key, value);
            }
            
            // Enviar archivo
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                },
                body: formData
            });

            // Manejar la respuesta
            let data;
            try {
                data = await response.json();
                console.log('Respuesta del servidor:', data);
            } catch (e) {
                console.error('Error al parsear la respuesta JSON:', e);
                const text = await response.text();
                console.error('Respuesta del servidor (texto):', text);
                throw new Error('Error al procesar la respuesta del servidor');
            }

            if (response.ok && data.success) {
                // Cerrar el modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('subirDocumentoModal'));
                if (modal) {
                    modal.hide();
                }

                // No mostrar mensaje aquí, ya se muestra en documentos.js
                // Recargar la lista de documentos
                const areaElement = document.querySelector('.area-item.active');
                if (areaElement) {
                    const areaId = areaElement.dataset.areaId;
                    const areaNombre = areaElement.dataset.areaNombre || nombreArea;
                    if (areaId && areaNombre) {
                        this.cargarDocumentosArea(areaId, areaNombre);
                    }
                }
            } else {
                console.error('Error en la respuesta del servidor:', data);
                throw new Error(data.error || 'Error al subir el documento');
            }
        } catch (error) {
            console.error('Error al subir el documento:', error);
            this.mostrarNotificacion(
                error.message || 'Ocurrió un error al subir el documento. Por favor, inténtalo de nuevo.',
                'danger'
            );
        } finally {
            // Restaurar estado del botón
            if (submitBtn) {
                submitBtn.disabled = false;
                if (submitText) submitText.textContent = 'Subir Documento';
            }
            if (uploadSpinner) uploadSpinner.classList.add('d-none');
        }
    },
    
    // Función auxiliar para obtener cookies
    getCookie: function(name) {
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
};

// Hacer que las funciones estén disponibles globalmente
if (!window.abrirModalSubirDocumento) {
    window.abrirModalSubirDocumento = function(areaId, areaNombre) {
        return ExpedienteApp.abrirModalSubirDocumento(areaId, areaNombre);
    };
}

if (!window.cargarDocumentosArea) {
    window.cargarDocumentosArea = function(areaId, areaTitulo) {
        console.log('Llamada a cargarDocumentosArea global', { areaId, areaTitulo });
        
        // Verificar si ExpedienteApp está disponible
        if (typeof ExpedienteApp === 'undefined') {
            console.error('Error: ExpedienteApp no está definido');
            return;
        }
        
        // Verificar si el método cargarDocumentosArea existe
        if (typeof ExpedienteApp.cargarDocumentosArea === 'function') {
            try {
                ExpedienteApp.cargarDocumentosArea(areaId, areaTitulo);
            } catch (error) {
                console.error('Error al cargar documentos del área:', error);
                // Mostrar notificación de error al usuario
                if (ExpedienteApp.mostrarNotificacion) {
                    ExpedienteApp.mostrarNotificacion('Error al cargar los documentos del área', 'error');
                }
            }
        } else {
            console.error('Error: ExpedienteApp.cargarDocumentosArea no es una función');
        }
    };
}

if (!window.cambiarTema) {
    window.cambiarTema = function() {
        if (ExpedienteApp && typeof ExpedienteApp.toggleTema === 'function') {
            ExpedienteApp.toggleTema();
        }
    };
}

// Verificar si ya hay un manejador de DOMContentLoaded
const initApp = () => {
    console.log('Inicializando aplicación...');
    
    // Verificar si ya está inicializado
    if (window.appInitialized) {
        console.warn('La aplicación ya fue inicializada');
        return;
    }
    
    // Marcar como inicializado
    window.appInitialized = true;
    
    // Inicializar la aplicación
    if (typeof ExpedienteApp === 'object' && typeof ExpedienteApp.init === 'function') {
        try {
            ExpedienteApp.init();
        } catch (error) {
            console.error('Error al inicializar la aplicación:', error);
        }
    } else {
        console.error('No se pudo inicializar la aplicación: ExpedienteApp no está definido correctamente');
    }
};

// Usar DOMContentLoaded o ejecutar directamente si el DOM ya está listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // El DOM ya está listo
    setTimeout(initApp, 0);
}

// Manejar errores no capturados (solo registrar en consola, no mostrar al usuario)
if (!window.errorHandlerInitialized) {
    window.errorHandlerInitialized = true;
    
    window.addEventListener('error', function(event) {
        // Evitar manejar el mismo error múltiples veces
        if (event.defaultPrevented) {
            return;
        }
        
        // Solo registrar en consola, no mostrar mensaje al usuario
        console.error('Error no capturado:', event.error || event.message, event);
        
        // Prevenir el manejo por otros manejadores
        event.preventDefault();
        
        // No mostrar notificación al usuario - solo registrar en consola
        return false;
    });
    
    // Manejar promesas no capturadas
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Promesa no manejada:', event.reason);
        
        // Prevenir el manejo por otros manejadores
        event.preventDefault();
        
        // Mostrar notificación al usuario
        try {
            if (window.ExpedienteApp && typeof window.ExpedienteApp.mostrarNotificacion === 'function') {
                window.ExpedienteApp.mostrarNotificacion(
                    'Se produjo un error al procesar una operación. Por favor, inténtalo de nuevo.',
                    'error'
                );
            }
        } catch (e) {
            console.error('Error al mostrar notificación de error en promesa:', e);
        }
    });
}

// Hacer que la aplicación esté disponible globalmente
window.ExpedienteApp = ExpedienteApp;

// ============================================
// Funciones de acciones del expediente
// ============================================

// Función para guardar el expediente
async function guardarExpediente() {
    const btn = document.getElementById('btn-guardar-expediente');
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Obtener el token CSRF
        const csrftoken = ExpedienteApp.getCookie('csrftoken');
        
        // Enviar solicitud para guardar el expediente
        const response = await fetch(`/expedientes/${expedienteId}/guardar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Error al guardar el expediente');
        }
        
        // Mostrar mensaje de éxito
        ExpedienteApp.mostrarNotificacion('✅ Expediente guardado correctamente', 'success');
        
        // Redirigir a la lista de expedientes después de 1 segundo
        setTimeout(() => {
            window.location.href = '/expedientes/lista/';
        }, 1000);
        
    } catch (error) {
        console.error('Error al guardar el expediente:', error);
        ExpedienteApp.mostrarNotificacion(`❌ ${error.message || 'Error al guardar el expediente. Intente nuevamente.'}`, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Función para rechazar el expediente
async function rechazarExpediente() {
    const btn = document.getElementById('btn-rechazar-expediente');
    if (!btn) return;
    
    // Confirmar acción
    if (!confirm('¿Está seguro de que desea rechazar este expediente? Esta acción cambiará el estado del expediente a "rechazado".')) {
        return;
    }
    
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Rechazando...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Obtener el token CSRF
        const csrftoken = ExpedienteApp.getCookie('csrftoken');
        
        // Enviar solicitud para rechazar el expediente
        const formData = new FormData();
        formData.append('razon_rechazo', 'Expediente rechazado desde el botón de acción');
        
        const response = await fetch(`/expedientes/${expedienteId}/rechazar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok || !data.success) {
            throw new Error(data.message || data.error || 'Error al rechazar el expediente');
        }
        
        // Mostrar mensaje de éxito
        ExpedienteApp.mostrarNotificacion('✅ Expediente rechazado correctamente', 'success');
        
        // Recargar la página para reflejar los cambios
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error al rechazar el expediente:', error);
        ExpedienteApp.mostrarNotificacion(`❌ ${error.message || 'Error al rechazar el expediente. Intente nuevamente.'}`, 'danger');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Función para descargar el expediente en formato ZIP
function descargarZip() {
    const btn = document.getElementById('btn-descargar-zip');
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Preparando descarga...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Redirigir directamente a la URL de descarga (la vista acepta GET)
        window.location.href = `/expedientes/${expedienteId}/descargar-completo/`;
        
        // Restaurar el botón después de un momento
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }, 3000);
        
    } catch (error) {
        console.error('Error al preparar la descarga:', error);
        ExpedienteApp.mostrarNotificacion('❌ Error al preparar la descarga. Intente nuevamente.', 'danger');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Hacer que las funciones estén disponibles globalmente
window.guardarExpediente = guardarExpediente;
window.rechazarExpediente = rechazarExpediente;
window.descargarZip = descargarZip;
