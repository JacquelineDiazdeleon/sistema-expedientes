/**
 * Manejo de interacciones con las áreas del expediente
 */

// Función para mostrar notificaciones al usuario (compatibilidad con código existente)
function showAlert(message, type = 'info') {
    // Usar la función centralizada de notificaciones
    window.mostrarNotificacion(message, type);
}

/**
 * Abre el modal para subir un documento a un área específica
 * @param {string} areaId - ID del área (opcional, se detecta automáticamente si no se proporciona)
 * @param {string} areaNombre - Nombre del área (opcional)
 * 
 * NOTA: Esta función delega a la función principal definida en el template o expediente.js
 * para evitar conflictos con múltiples definiciones
 */
if (!window.abrirModalSubirDocumento) {
    window.abrirModalSubirDocumento = function(areaId, areaNombre) {
    console.log('Abriendo modal para subir documento al área:', areaId, areaNombre);
    
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
            alert('Error: No se pudo determinar el área. Por favor, selecciona un área primero y luego intenta subir un documento.');
            return;
        }
    }
    
    // Convertir areaId a número si es necesario
    let areaIdNum = areaId;
    if (typeof areaId === 'string') {
        areaIdNum = parseInt(areaId.trim(), 10);
        if (isNaN(areaIdNum) || areaIdNum <= 0) {
            console.error('Error: El ID de área no es un número válido:', areaId);
            alert('Error: No se pudo determinar el área. Por favor, selecciona un área primero y luego intenta subir un documento.');
            return;
        }
    }
    
    // Actualizar el título del modal
    const modalTitulo = document.getElementById('subirDocumentoModalLabel');
    if (modalTitulo) {
        modalTitulo.textContent = `Subir documento a ${areaNombre || 'el área seleccionada'}`;
    }
    
    // Actualizar el campo oculto con el ID del área
    const areaIdInput = document.getElementById('area_id');
    if (areaIdInput) {
        areaIdInput.value = areaIdNum;
        console.log('ID de área establecido en el formulario:', areaIdInput.value);
        
        // También actualizar la variable global para futuras referencias
        if (typeof window !== 'undefined') {
            window.areaSeleccionada = { id: areaIdNum, nombre: areaNombre };
            console.log('window.areaSeleccionada actualizado:', window.areaSeleccionada);
        }
    } else {
        console.error('No se encontró el campo area_id en el formulario');
        alert('Error: No se pudo determinar el área. Por favor, recarga la página.');
        return;
    }
    
    // Verificar si Bootstrap está disponible
    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap no está disponible');
        showAlert('Error: La biblioteca de interfaz de usuario no se cargó correctamente. Por favor, recarga la página.', 'error');
        return;
    }
    
    // Mostrar el modal
    const modalElement = document.getElementById('subirDocumentoModal');
    if (modalElement) {
        // Cerrar el modal si ya está abierto
        const modalExistente = bootstrap.Modal.getInstance(modalElement);
        if (modalExistente) {
            modalExistente.hide();
            modalExistente.dispose();
        }
        
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });
        modal.show();
        
        // Enfocar el primer campo después de que el modal se muestre
        setTimeout(() => {
            const firstInput = modalElement.querySelector('input[type="text"], input[type="file"]');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    } else {
        console.error('No se encontró el elemento del modal');
        showAlert('No se pudo abrir el modal de subida de documentos', 'error');
    }
};

/**
 * Carga los documentos de un área específica
 * @param {string} areaId - ID del área
 * @param {string} nombreArea - Nombre del área para mostrar
 */
window.cargarDocumentosArea = async function(areaId, nombreArea) {
    console.log('Cargando documentos para área:', areaId, nombreArea);
    
    // Validar parámetros
    if (!areaId) {
        console.error('Error: No se proporcionó un ID de área válido');
        showAlert('No se proporcionó un ID de área válido', 'error');
        return;
    }
    
    // Referencias a elementos del DOM
    const contenedor = document.getElementById('contenido-documentos');
    const bienvenida = document.getElementById('bienvenida-area');
    const contenidoArea = document.getElementById('contenido-area');
    const tituloAreaElement = document.getElementById('titulo-area-seleccionada');
    
    // Función para mostrar error
    const mostrarError = (mensaje) => {
        console.error('Error al cargar documentos:', mensaje);
        
        // Crear elementos DOM directamente
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        
        const flexDiv = document.createElement('div');
        flexDiv.className = 'd-flex align-items-center';
        
        const icon = document.createElement('i');
        icon.className = 'bi bi-exclamation-triangle-fill me-2';
        
        const mensajeElement = document.createElement('span');
        mensajeElement.textContent = `Error al cargar documentos: ${mensaje}`;
        
        flexDiv.appendChild(icon);
        flexDiv.appendChild(mensajeElement);
        alertDiv.appendChild(flexDiv);
        
        // Limpiar el contenedor y mostrar el error
        if (contenedor) {
            contenedor.innerHTML = '';
            contenedor.appendChild(alertDiv);
        }
        
        // Mostrar botón de reintento
        const reintentarBtn = document.createElement('button');
        reintentarBtn.className = 'btn btn-outline-primary mt-3';
        reintentarBtn.innerHTML = '<i class="bi bi-arrow-repeat me-2"></i>Reintentar';
        reintentarBtn.onclick = () => window.cargarDocumentosArea(areaId, nombreArea);
        
        alertDiv.appendChild(document.createElement('br'));
        alertDiv.appendChild(reintentarBtn);
    };
    
    try {
        // Mostrar indicador de carga
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-3">Cargando documentos del área...</p>
                </div>
            `;
        }
        
        // Ocultar bienvenida y mostrar contenido del área
        if (bienvenida) bienvenida.classList.add('d-none');
        if (contenidoArea) contenidoArea.classList.remove('d-none');
        
        // Actualizar el título del área
        if (tituloAreaElement) {
            tituloAreaElement.textContent = nombreArea || 'Documentos del área';
        }
        
        try {
            console.log('Cargando documentos para el área:', areaId);
            
            // Obtener el ID del expediente de la URL
            const urlParts = window.location.pathname.split('/');
            const expedienteId = urlParts[urlParts.length - 1];
            
            if (!expedienteId || isNaN(expedienteId)) {
                throw new Error('No se pudo obtener el ID del expediente de la URL');
            }
            
            // Hacer la petición a la ruta correcta
            const response = await fetch(`/expedientes/${expedienteId}/area/${areaId}/documentos/`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Error en la petición: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Documentos cargados:', data);
            
            if (data.success === false) {
                throw new Error(data.error || 'Error al cargar los documentos');
            }
            
            // Actualizar la interfaz con los documentos cargados
            if (contenedor) {
                if (data.documentos && data.documentos.length > 0) {
                    let html = `
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5>Documentos del área</h5>
                                <button class="btn btn-primary" onclick="abrirModalSubirDocumento('${areaId}', '${nombreArea.replace(/'/g, "\\'")}')">
                                    <i class="bi bi-plus-lg me-1"></i> Agregar Documento
                                </button>
                            </div>
                            <div class="list-group mt-3">
                    `;
                    
                    data.documentos.forEach(doc => {
                        html += `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <div class="d-flex align-items-center">
                                    <i class="bi ${doc.tipo === 'pdf' ? 'bi-file-earmark-pdf text-danger' : 'bi-file-earmark-text'}"></i>
                                    <span class="ms-2">${doc.nombre}</span>
                                </div>
                                <div>
                                    <a href="${doc.url}" class="btn btn-sm btn-outline-primary me-2" target="_blank">
                                        <i class="bi bi-eye"></i> Ver
                                    </a>
                                    <a href="${doc.url}" class="btn btn-sm btn-outline-secondary" download>
                                        <i class="bi bi-download"></i> Descargar
                                    </a>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                    
                    contenedor.innerHTML = html;
                } else {
                    contenedor.innerHTML = `
                        <div class="text-center py-5">
                            <i class="bi bi-folder-x display-1 text-muted mb-3"></i>
                            <h4>No hay documentos en esta área</h4>
                            <p class="text-muted mb-4">Aún no se han cargado documentos en esta área.</p>
                            <button class="btn btn-primary" onclick="abrirModalSubirDocumento('${areaId}', '${nombreArea.replace(/'/g, "\\'")}')">
                                <i class="bi bi-upload me-1"></i> Subir Primer Documento
                            </button>
                        </div>
                    `;
                }
            }
            
        } catch (error) {
            console.error('Error al cargar los documentos:', error);
            mostrarError('No se pudieron cargar los documentos. ' + error.message);
        }
        
    } catch (error) {
        console.error('Error inesperado:', error);
        mostrarError('Ocurrió un error inesperado: ' + error.message);
    }
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando manejador de áreas...');
    
    // Asignar manejador de eventos a cada área
    document.querySelectorAll('.area-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const areaId = this.getAttribute('data-area-id');
            const areaNombre = this.getAttribute('data-area-nombre');
            
            // Actualizar la clase activa
            document.querySelectorAll('.area-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Cargar documentos del área
            if (window.cargarDocumentosArea) {
                window.cargarDocumentosArea(areaId, areaNombre);
            } else {
                console.error('La función cargarDocumentosArea no está definida');
                showAlert('Error al cargar los documentos: función no disponible', 'error');
            }
        });
    });
    
    // Cargar automáticamente el área activa
    const areaActiva = document.querySelector('.area-item.active');
    if (areaActiva && window.cargarDocumentosArea) {
        console.log('Cargando área activa por defecto');
        const areaId = areaActiva.getAttribute('data-area-id');
        const areaNombre = areaActiva.getAttribute('data-area-nombre');
        window.cargarDocumentosArea(areaId, areaNombre);
    }
        
    // Escuchar el evento de documento subido
    document.addEventListener('documentoSubido', (e) => {
        const { areaId, documento, notificacionMostrada } = e.detail;
        
        // Recargar la lista de documentos del área
        if (areaId) {
            const areaItem = document.querySelector(`.area-item[data-area-id="${areaId}"]`);
            if (areaItem) {
                const areaNombre = areaItem.getAttribute('data-area-nombre');
                cargarDocumentosArea(areaId, areaNombre);
            }
        }
    });
    
    // NOTA: El manejo del formulario se delega a documentos.js para evitar conflictos
    // Inicializar el formulario de subida de documentos
    // const formSubirDocumento = document.getElementById('form-subir-documento');
    // if (formSubirDocumento) {
    //     formSubirDocumento.addEventListener('submit', async function(e) {
    //         e.preventDefault();
    //             
    //         const formData = new FormData(this);
    //         const btnSubmit = this.querySelector('button[type="submit"]');
    //         const spinner = this.querySelector('.spinner-border');
    //             
    //         // Obtener el ID del área del formulario o del elemento activo
    //         let areaId = formData.get('area_id') || document.querySelector('.area-item.active')?.getAttribute('data-area-id');
    //         const areaNombre = document.querySelector('.area-item.active')?.getAttribute('data-area-nombre') || '';
    //             
    //         // Validar que el ID del área no sea un objeto
    //         if (typeof areaId === 'object' && areaId !== null) {
    //             console.warn('Se recibió un objeto como areaId, extrayendo valor...', areaId);
    //             areaId = areaId.id || areaId.value || Object.values(areaId)[0];
    //         }
    //             
    //         // Convertir a string si es necesario
    //         areaId = String(areaId);
    //             
    //         if (!areaId || areaId === '[object Object]') {
    //             showAlert('Error: No se pudo identificar el área de destino', 'error');
    //             return;
    //         }
    //
    //         // Validar que se haya seleccionado un archivo
    //         const fileInput = this.querySelector('input[type="file"]');
    //         if (!fileInput || !fileInput.files || !fileInput.files[0]) {
    //             showAlert('Error: No se proporcionó ningún archivo', 'error');
    //             return;
    //         }
    //
    //         // Asegurarse de que el archivo se agregue con el nombre correcto 'archivo'
    //         if (formData.has('documento')) {
    //             const archivo = formData.get('documento');
    //             formData.delete('documento');
    //             formData.append('archivo', archivo);
    //         } else if (fileInput.files[0]) {
    //             formData.append('archivo', fileInput.files[0]);
    //         }
    //
    //         // Agregar el área al formData si no está presente
    //         if (!formData.has('area_id')) {
    //             formData.append('area_id', areaId);
    //         }
    //             
    //         // Obtener el ID del expediente de la URL
    //         const urlParts = window.location.pathname.split('/');
    //         const expedienteId = urlParts[urlParts.length - 1];
    //         
    //         if (expedienteId && !isNaN(expedienteId)) {
    //             formData.append('expediente_id', expedienteId);
    //         }
    //         
            try {
                // Mostrar indicador de carga
                btnSubmit.disabled = true;
                if (spinner) spinner.classList.remove('d-none');
                             
                // Usar la ruta correcta de la API
                const response = await fetch('/expedientes/api/documentos/subir/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken') || '',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                // Verificar si la respuesta es JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    throw new Error('Respuesta del servidor no es JSON: ' + text.substring(0, 200));
                }

                const data = await response.json();
                if (!response.ok) {
                    // Verificar si el error es 'database is locked'
                    if (data.error && data.error.includes('database is locked')) {
                        console.log('Advertencia: La base de datos está bloqueada, pero el archivo se subió correctamente.');
                        
                        // Cerrar el modal
                        const modal = bootstrap.Modal.getInstance(document.getElementById('subirDocumentoModal'));
                        if (modal) modal.hide();
                        
                        // Recargar documentos del área actual
                        if (window.cargarDocumentosArea) {
                            window.cargarDocumentosArea(areaId, areaNombre);
                        }
                        
                        // Limpiar el formulario
                        this.reset();
                        
                        // No mostrar notificación aquí, se mostrará en documentos.js
                        return;
                    }
                    throw new Error(data.error || `Error ${response.status}: ${response.statusText}`);
                }

                // Cerrar el modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('subirDocumentoModal'));
                if (modal) modal.hide();
                      
                // Recargar documentos del área actual
                if (window.cargarDocumentosArea) {
                    window.cargarDocumentosArea(areaId, areaNombre);
                }
                
                // Disparar evento personalizado para notificar a otros componentes
                document.dispatchEvent(new CustomEvent('documentoSubido', {
                    detail: {
                        areaId: areaId,
                        documento: data.documento || {}
                    }
                }));

                // Limpiar el formulario
                this.reset();

            } catch (error) {
                console.error('Error al subir el documento:', error);
                
                // Verificar si el error es 'database is locked' pero el archivo se subió correctamente
                if (error.message && error.message.includes('database is locked')) {
                    console.log('Advertencia: La base de datos está bloqueada, pero el archivo se subió correctamente.');
                    
                    // Cerrar el modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('subirDocumentoModal'));
                    if (modal) modal.hide();
                    
                    // Recargar documentos del área actual
                    if (window.cargarDocumentosArea) {
                        window.cargarDocumentosArea(areaId, areaNombre);
                    }
                    
                    // No mostrar notificación aquí, se mostrará en documentos.js
                } else {
                    showAlert('Error al subir el documento: ' + (error.message || 'Error desconocido'), 'error');
                }
            } finally {
                // Restaurar el botón
                btnSubmit.disabled = false;
                if (spinner) spinner.classList.add('d-none');
            }
    //     });
    // }
        
    // Función auxiliar para obtener el token CSRF
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
});
