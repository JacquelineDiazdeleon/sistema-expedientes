/**
 * Manejo de documentos para el módulo de expedientes
 */

const DocumentosApp = {
    // Variables de estado
    areaActual: null,
    
    // Inicialización
    init: function() {
        console.log('Inicializando módulo de documentos');
        this.obtenerElementos();
        this.initEventListeners();
    },
    
    // Obtener referencias a elementos del DOM
    obtenerElementos: function() {
        this.elementos = {
            modalSubirDocumento: document.getElementById('subirDocumentoModal') ? 
                new bootstrap.Modal(document.getElementById('subirDocumentoModal')) : null,
            formularioSubida: document.getElementById('form-subir-documento'),
            inputArchivo: document.getElementById('documento'),
            btnSubir: document.getElementById('btn-subir-documento'),
            spinner: document.getElementById('uploadSpinner'),
            nombreDocumento: document.getElementById('nombreDocumento'),
            observaciones: document.getElementById('observaciones'),
            contenedorAlertas: document.getElementById('contenedor-alertas')
        };
    },
    
    // Inicializar manejadores de eventos
    initEventListeners: function() {
        const { 
            formularioSubida, 
            inputArchivo
        } = this.elementos;

        // Manejar envío del formulario
        if (formularioSubida) {
            formularioSubida.addEventListener('submit', (e) => {
                e.preventDefault();
                this.subirDocumento();
            });
        }
        
        // Manejar selección de archivo
        if (inputArchivo) {
            inputArchivo.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    this.validarArchivo(e.target.files[0]);
                }
            });
        }
    },
    
    // Validar archivo antes de subir
    validarArchivo: function(archivo) {
        const tiposPermitidos = ['application/pdf', 'application/msword', 
                               'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                               'application/vnd.ms-excel',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                               'image/jpeg', 'image/png'];
        const tamanoMaximo = 10 * 1024 * 1024; // 10MB
        
        if (!tiposPermitidos.includes(archivo.type)) {
            this.mostrarAlerta('Tipo de archivo no permitido. Por favor, sube un archivo PDF, Word, Excel o imagen.', 'error');
            this.elementos.inputArchivo.value = '';
            return false;
        }
        
        if (archivo.size > tamanoMaximo) {
            this.mostrarAlerta('El archivo es demasiado grande. El tamaño máximo permitido es de 10MB.', 'error');
            this.elementos.inputArchivo.value = '';
            return false;
        }
        
        return true;
    },
    
    // Subir documento al servidor
    subirDocumento: function() {
        const { 
            formularioSubida, 
            spinner, 
            btnSubir,
            nombreDocumento,
            inputArchivo
        } = this.elementos;
        
        if (!formularioSubida || !inputArchivo.files[0]) {
            this.mostrarAlerta('Por favor, selecciona un archivo para subir.', 'error');
            return;
        }
        
        if (!nombreDocumento || !nombreDocumento.value.trim()) {
            this.mostrarAlerta('Por favor, ingresa un nombre para el documento.', 'error');
            return;
        }
        
        // Mostrar spinner y deshabilitar botón
        spinner.classList.remove('d-none');
        btnSubir.disabled = true;
        
        // Crear FormData
        const formData = new FormData(formularioSubida);
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.length - 1];
        
        if (!expedienteId || isNaN(expedienteId)) {
            this.mostrarAlerta('No se pudo identificar el expediente actual.', 'error');
            spinner.classList.add('d-none');
            btnSubir.disabled = false;
            return;
        }
        
        // Agregar el ID del área actual si está disponible
        if (this.areaActual && this.areaActual.id) {
            formData.append('area_id', this.areaActual.id);
        }
        
        // Realizar la petición
        fetch(`/expedientes/${expedienteId}/documentos/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Error al subir el documento');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.mostrarAlerta('Documento subido correctamente', 'success');
                // Cerrar el modal
                if (this.elementos.modalSubirDocumento) {
                    this.elementos.modalSubirDocumento.hide();
                }
                // Recargar los documentos del área actual
                if (this.areaActual) {
                    this.cargarDocumentosArea(this.areaActual.id, this.areaActual.nombre);
                }
                // Limpiar el formulario
                formularioSubida.reset();
            } else {
                throw new Error(data.error || 'Error al subir el documento');
            }
        })
        .catch(error => {
            console.error('Error al subir el documento:', error);
            this.mostrarAlerta(error.message || 'Error al subir el documento. Por favor, inténtalo de nuevo.', 'error');
        })
        .finally(() => {
            spinner.classList.add('d-none');
            btnSubir.disabled = false;
        });
    },
    
    // Mostrar alerta
    mostrarAlerta: function(mensaje, tipo = 'info') {
        const { contenedorAlertas } = this.elementos;
        if (!contenedorAlertas) return;
        
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
        alerta.role = 'alert';
        alerta.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;
        
        contenedorAlertas.appendChild(alerta);
        
        // Eliminar la alerta después de 5 segundos
        setTimeout(() => {
            alerta.classList.remove('show');
            setTimeout(() => {
                contenedorAlertas.removeChild(alerta);
            }, 150);
        }, 5000);
    },
    
    // Obtener el valor de una cookie por su nombre
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
    },
    
    // Cargar documentos de un área
    cargarDocumentosArea: function(areaId, nombreArea) {
        console.log('Cargando documentos para el área:', areaId, nombreArea);
        this.areaActual = { id: areaId, nombre: nombreArea };
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.length - 1];
        
        if (!expedienteId || isNaN(expedienteId)) {
            console.error('No se pudo obtener el ID del expediente de la URL');
            this.mostrarError('No se pudo identificar el expediente actual');
            return;
        }
        
        // Mostrar indicador de carga
        const contenedor = document.getElementById('contenido-documentos');
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <span class="ms-3">Cargando documentos para ${nombreArea}...</span>
                </div>`;
        }
        
        // Realizar la petición al servidor
        fetch(`/expedientes/${expedienteId}/area/${areaId}/documentos/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `Error en la petición: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Documentos recibidos:', data);
            if (data.success === false) {
                throw new Error(data.error || 'Error al cargar los documentos');
            }
            this.mostrarDocumentos(data.documentos || [], nombreArea);
        })
        .catch(error => {
            console.error('Error al cargar documentos:', error);
            this.mostrarError(`No se pudieron cargar los documentos: ${error.message}`);
        });
    },
    
    // Mostrar documentos en la interfaz
    mostrarDocumentos: function(documentos, nombreArea) {
        const contenedor = document.getElementById('contenido-documentos');
        if (!contenedor) return;
        
        if (documentos.length === 0) {
            this.mostrarListaDocumentosVacia(nombreArea);
            return;
        }
        
        // Crear la tabla de documentos
        let html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">Documentos de ${nombreArea}</h5>
                    <button class="btn btn-sm btn-azul-oscuro" data-bs-toggle="modal" data-bs-target="#subirDocumentoModal">
                        <i class="bi bi-plus-lg me-1"></i> Agregar Documento
                    </button>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Tipo</th>
                                <th>Tamaño</th>
                                <th>Fecha de Subida</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>`;
        
        documentos.forEach(doc => {
            const fecha = new Date(doc.fecha_subida);
            const fechaFormateada = fecha.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const tamanoFormateado = this.formatearTamanio(doc.tamano_archivo || 0);
            
            html += `
                <tr>
                    <td>${doc.nombre || 'Sin nombre'}</td>
                    <td>${doc.tipo_documento || 'Desconocido'}</td>
                    <td>${tamanoFormateado}</td>
                    <td>${fechaFormateada}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <a href="${doc.archivo_url}" class="btn btn-outline-primary" target="_blank" title="Ver">
                                <i class="bi bi-eye"></i>
                            </a>
                            <a href="${doc.archivo_url}" class="btn btn-outline-secondary" download title="Descargar">
                                <i class="bi bi-download"></i>
                            </a>
                            <button class="btn btn-outline-danger" onclick="DocumentosApp.confirmarEliminarDocumento('${doc.id}', '${doc.nombre || 'este documento'}')" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>`;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>`;
            
        contenedor.innerHTML = html;
    },
    
    // Mostrar lista vacía de documentos
    mostrarListaDocumentosVacia: function(nombreArea) {
        const contenedor = document.getElementById('contenido-documentos');
        if (!contenedor) return;
        
        contenedor.innerHTML = `
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="bi bi-folder2-open display-4 text-muted"></i>
                </div>
                <h4>No hay documentos en ${nombreArea}</h4>
                <p class="text-muted mb-4">Aún no se han cargado documentos para esta área.</p>
                <button class="btn btn-azul-oscuro" data-bs-toggle="modal" data-bs-target="#subirDocumentoModal">
                    <i class="bi bi-upload me-2"></i>Subir Primer Documento
                </button>
            </div>`;
    },
    
    // Formatear tamaño de archivo
    formatearTamanio: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Mostrar error
    mostrarError: function(mensaje) {
        const contenedor = document.getElementById('contenido-documentos');
        if (!contenedor) return;
        
        contenedor.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <div>${mensaje}</div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-secondary" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-1"></i> Recargar
                    </button>
                </div>
            </div>`;
    },
    
    // Confirmar eliminación de documento
    confirmarEliminarDocumento: function(documentoId, nombreDocumento) {
        if (confirm(`¿Estás seguro de que deseas eliminar "${nombreDocumento}"? Esta acción no se puede deshacer.`)) {
            this.eliminarDocumento(documentoId);
        }
    },
    
    // Eliminar documento
    eliminarDocumento: function(documentoId) {
        fetch(`/documentos/${documentoId}/eliminar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Error al eliminar el documento');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.mostrarAlerta('Documento eliminado correctamente', 'success');
                // Recargar los documentos del área actual
                if (this.areaActual) {
                    this.cargarDocumentosArea(this.areaActual.id, this.areaActual.nombre);
                }
            } else {
                throw new Error(data.error || 'Error al eliminar el documento');
            }
        })
        .catch(error => {
            console.error('Error al eliminar el documento:', error);
            this.mostrarAlerta(error.message || 'Error al eliminar el documento. Por favor, inténtalo de nuevo.', 'error');
        });
    }
};

// Inicializar el módulo cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    DocumentosApp.init();
});
