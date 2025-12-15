/**
 * Manejo de documentos para el módulo de expedientes
 */

const DocumentosApp = {
    // Variables de estado
    areaActual: null,
    
    // Inicialización
    init: function() {
        console.log('Inicializando módulo de documentos');
        // Inicializar this.areaActual
        this.areaActual = null;
        console.log('this.areaActual inicializado como:', this.areaActual);
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
        
        // Manejador de clic para botones de eliminar (delegado)
        // Usar arrow function para mantener el contexto de 'this'
        document.addEventListener('click', function(e) {
            // Buscar el botón más cercano (puede ser el botón mismo o un elemento dentro como el icono)
            const deleteBtn = e.target.closest('.btn-eliminar-documento');
            if (deleteBtn) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                const docId = deleteBtn.getAttribute('data-documento-id');
                const docNombre = deleteBtn.getAttribute('data-documento-nombre') || 'este documento';
                
                console.log('🔍 Click detectado en botón eliminar:', {
                    elementoClick: e.target,
                    elementoClickTag: e.target.tagName,
                    elementoClickClass: e.target.className,
                    boton: deleteBtn,
                    botonTag: deleteBtn.tagName,
                    docId: docId,
                    docNombre: docNombre
                });
                
                if (docId && docId !== '' && docId !== 'undefined' && docId !== 'null') {
                    console.log('✅ Click en botón eliminar confirmado, llamando a confirmarEliminarDocumento');
                    if (typeof DocumentosApp !== 'undefined' && typeof DocumentosApp.confirmarEliminarDocumento === 'function') {
                        DocumentosApp.confirmarEliminarDocumento(docId, docNombre);
                    } else {
                        console.error('❌ DocumentosApp.confirmarEliminarDocumento no está disponible');
                        alert('Error: No se pudo inicializar la función de eliminación. Por favor, recarga la página.');
                    }
                } else {
                    console.error('❌ Botón de eliminar no tiene data-documento-id válido');
                    console.log('Atributos del botón:', Array.from(deleteBtn.attributes).map(attr => `${attr.name}="${attr.value}"`));
                    alert('Error: No se pudo identificar el documento a eliminar. Por favor, recarga la página.');
                }
                
                return false;
            }
        }, true); // Usar capture phase para capturar antes que otros listeners

        // Manejar envío del formulario
        if (formularioSubida) {
            // Primero, eliminar cualquier manejador de eventos existente para evitar duplicados
            const newForm = formularioSubida.cloneNode(true);
            formularioSubida.parentNode.replaceChild(newForm, formularioSubida);
            this.elementos.formularioSubida = newForm;
            
            // Actualizar la referencia al input de archivo después de clonar
            const nuevoInputArchivo = newForm.querySelector('#documento');
            if (nuevoInputArchivo) {
                this.elementos.inputArchivo = nuevoInputArchivo;
                console.log('✅ Input de archivo actualizado después de clonar formulario');
            }
            
            // Agregar el nuevo manejador de eventos
            newForm.addEventListener('submit', (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevenir la propagación del evento
                
                // Verificar si ya hay una subida en progreso
                if (this.subiendo) {
                    console.log('Ya hay una subida en progreso');
                    return;
                }
                
                console.log('Iniciando subida de documento');
                this.subiendo = true;
                
                // Usar DocumentosApp directamente para evitar problemas con this
                DocumentosApp.subirDocumento()
                    .finally(() => {
                        this.subiendo = false;
                    });
            });
        }
        
        // Manejar selección de archivo - obtener el input actualizado
        const inputArchivoActual = document.getElementById('documento');
        if (inputArchivoActual) {
            // Actualizar la referencia en elementos
            this.elementos.inputArchivo = inputArchivoActual;
            
            inputArchivoActual.addEventListener('change', (e) => {
                console.log('📁 Archivo seleccionado:', e.target.files ? e.target.files[0]?.name : 'ninguno');
                if (e.target.files && e.target.files[0]) {
                    this.validarArchivo(e.target.files[0]);
                }
            });
        } else {
            console.warn('⚠️ No se encontró el input de archivo con ID "documento"');
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
    subirDocumento: async function() {
        console.log('=== INICIO DE SUBIR DOCUMENTO ===');
        console.log('this.areaActual completo:', this.areaActual);
        console.log('typeof this.areaActual:', typeof this.areaActual);
        if (this.areaActual) {
            console.log('this.areaActual.id:', this.areaActual.id, 'tipo:', typeof this.areaActual.id);
        }
        
        const { 
            formularioSubida, 
            spinner, 
            btnSubir,
            nombreDocumento,
            contenedorAlertas,
            observaciones
        } = this.elementos;
        
        // Obtener el input de archivo directamente del DOM para asegurar que esté actualizado
        let inputArchivo = document.getElementById('documento');
        
        // Si no se encuentra, intentar obtenerlo del formulario
        if (!inputArchivo && formularioSubida) {
            inputArchivo = formularioSubida.querySelector('input[type="file"]');
            console.log('Input obtenido del formulario:', inputArchivo);
        }
        
        // Si aún no se encuentra, intentar por name
        if (!inputArchivo) {
            inputArchivo = document.querySelector('input[name="documento"]');
            console.log('Input obtenido por name:', inputArchivo);
        }
        
        console.log('📁 Input de archivo encontrado:', inputArchivo);
        console.log('📁 Input files:', inputArchivo ? inputArchivo.files : 'input no encontrado');
        console.log('📁 Input files length:', inputArchivo && inputArchivo.files ? inputArchivo.files.length : 'N/A');
        console.log('📁 Input files[0]:', inputArchivo && inputArchivo.files ? inputArchivo.files[0] : 'N/A');
        
        if (!formularioSubida) {
            console.error('❌ No se encontró el formulario');
            this.mostrarAlerta('Error: No se encontró el formulario. Por favor, recarga la página.', 'error');
            return;
        }
        
        if (!inputArchivo) {
            console.error('❌ No se encontró el campo de archivo');
            this.mostrarAlerta('Error: No se encontró el campo de archivo. Por favor, recarga la página.', 'error');
            return;
        }
        
        // Validar que se haya seleccionado un archivo
        if (!inputArchivo.files || inputArchivo.files.length === 0 || !inputArchivo.files[0]) {
            console.error('❌ No hay archivo seleccionado');
            console.log('Input value:', inputArchivo.value);
            console.log('Input files:', inputArchivo.files);
            this.mostrarAlerta('Por favor, selecciona un archivo para subir.', 'error');
            // Enfocar el input de archivo
            setTimeout(() => {
                inputArchivo.focus();
                // No hacer click automático, solo mostrar el mensaje
            }, 100);
            return;
        }
        
        console.log('✅ Archivo validado correctamente:', inputArchivo.files[0].name);
        
        if (!nombreDocumento || !nombreDocumento.value.trim()) {
            this.mostrarAlerta('Por favor, ingresa un nombre para el documento.', 'error');
            return;
        }
        
        // Validar tamaño máximo del archivo (100MB)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (inputArchivo.files[0].size > maxSize) {
            this.mostrarAlerta('El archivo es demasiado grande. El tamaño máximo permitido es 100MB.', 'error');
            return;
        }
        
        // Obtener el ID del área directamente del formulario ANTES de crear el FormData
        // Esta es la forma más segura de obtener el areaId
        const areaIdInput = document.getElementById('area_id');
        let areaId = null;
        
        if (areaIdInput && areaIdInput.value) {
            areaId = parseInt(areaIdInput.value, 10);
            console.log('📋 areaId obtenido del formulario:', areaId, 'tipo:', typeof areaId);
        } else {
            // Intentar obtener del área activa como respaldo
            console.warn('⚠️ No se encontró area_id en el formulario, intentando obtener del área activa...');
            const areaActiva = document.querySelector('.area-item.active');
            if (areaActiva) {
                const areaIdStr = areaActiva.getAttribute('data-area-id');
                if (areaIdStr) {
                    areaId = parseInt(areaIdStr, 10);
                    // Establecer en el formulario para futuras referencias
                    if (areaIdInput) {
                        areaIdInput.value = areaId;
                        console.log('✅ area_id establecido desde área activa:', areaId);
                    }
                }
            }
            
            if (!areaId) {
                console.error('❌ No se encontró el campo area_id o está vacío');
                this.mostrarAlerta('No se pudo determinar el área. Por favor, seleccione un área e intente nuevamente.', 'error');
                return;
            }
        }
        
        // Validación final
        if (isNaN(areaId) || areaId === null || areaId === undefined || areaId <= 0) {
            console.error('❌ areaId no válido:', areaId);
            this.mostrarAlerta('No se pudo determinar el área. Por favor, seleccione un área e intente nuevamente.', 'error');
            return;
        }
        
        console.log('✅ areaId validado:', areaId, 'tipo:', typeof areaId);
        
        // Crear FormData y agregar campos manualmente
        const formData = new FormData();
        
        // Validar que el archivo exista y agregarlo
        const archivoSeleccionado = inputArchivo.files[0];
        if (!archivoSeleccionado) {
            console.error('❌ No se encontró archivo seleccionado');
            console.log('inputArchivo:', inputArchivo);
            console.log('inputArchivo.files:', inputArchivo.files);
            console.log('inputArchivo.files.length:', inputArchivo.files ? inputArchivo.files.length : 'undefined');
            this.mostrarAlerta('No se proporcionó ningún archivo. Por favor, selecciona un archivo.', 'error');
            // Enfocar y hacer clic en el input para ayudar al usuario
            setTimeout(() => {
                inputArchivo.focus();
                inputArchivo.click();
            }, 100);
            return;
        }
        
        console.log('✅ Archivo seleccionado:', archivoSeleccionado.name, 'Tamaño:', archivoSeleccionado.size, 'bytes');
        formData.append('documento', archivoSeleccionado);
        formData.append('nombre_documento', nombreDocumento.value.trim());
        formData.append('area_id', areaId.toString()); // ✅ AGREGAR EL area_id AL FORMDATA
        
        // Verificar que el area_id se agregó correctamente
        const areaIdVerificado = formData.get('area_id');
        if (!areaIdVerificado || areaIdVerificado !== areaId.toString()) {
            console.error('❌ ERROR: area_id no se agregó correctamente al FormData');
            console.log('areaId esperado:', areaId, 'areaId en FormData:', areaIdVerificado);
            this.mostrarAlerta('Error crítico: No se pudo incluir el área en el formulario. Por favor, recarga la página.', 'error');
            return;
        }
        
        console.log('✅ area_id verificado en FormData:', areaIdVerificado);
        
        if (observaciones && observaciones.value) {
            formData.append('descripcion', observaciones.value);
        }
        
        // Validar que el archivo se haya agregado correctamente
        if (!formData.has('documento')) {
            this.mostrarAlerta('Error al adjuntar el archivo. Por favor, intenta nuevamente.', 'error');
            return;
        }
        
        // Validar que el area_id se haya agregado correctamente
        if (!formData.has('area_id')) {
            console.error('Error: area_id no se agregó al FormData');
            this.mostrarAlerta('Error al preparar el formulario. Por favor, intenta nuevamente.', 'error');
            return;
        }
        
        console.log('FormData preparado con area_id:', formData.get('area_id'));
        
        // Mostrar spinner y deshabilitar botón
        if (spinner) spinner.classList.remove('d-none');
        if (btnSubir) btnSubir.disabled = true;
        
        // Obtener el token CSRF
        const csrftoken = this.getCookie('csrftoken');
        
        // Obtener el ID del expediente de la URL
        const expedienteId = window.location.pathname.split('/')[2];
        if (!expedienteId) {
            this.mostrarAlerta('No se pudo determinar el expediente actual.', 'error');
            if (spinner) spinner.classList.add('d-none');
            if (btnSubir) btnSubir.disabled = false;
            return;
        }
        
        // Construir la URL de la API
        const areaIdParaUrl = areaId.toString();
        console.log('Construyendo URL con areaId:', areaId, '-> areaIdParaUrl:', areaIdParaUrl);
        const url = `/expedientes/${expedienteId}/etapa/${areaIdParaUrl}/subir-documento/`;
        console.log('URL final:', url);
        
        // Configuración de la petición
        const options = {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                // No establecer Content-Type para permitir que el navegador lo establezca automáticamente
                // con el límite correcto para el archivo adjunto
            },
            credentials: 'same-origin', // Incluir cookies de autenticación
            body: formData
        };
        
        // Realizar la petición
        fetch(url, options)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Error al subir el documento');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Documento subido exitosamente:', data);
            
            // Limpiar cualquier mensaje de error existente
            if (this.elementos.contenedorAlertas) {
                this.elementos.contenedorAlertas.innerHTML = '';
            }
            
            // Limpiar el formulario
            if (formularioSubida) formularioSubida.reset();
            
            // Cerrar el modal si está abierto
            if (this.elementos.modalSubirDocumento) {
                this.elementos.modalSubirDocumento.hide();
            }
            
            // Recargar los documentos del área actual
            if (this.areaActual) {
                this.cargarDocumentosArea(this.areaActual);
            }
            
            // Disparar evento personalizado para notificar a otros componentes
            // Nota: Ya no es necesario que otros componentes muestren notificaciones
            document.dispatchEvent(new CustomEvent('documentoSubido', { 
                detail: { 
                    areaId: this.areaActual,
                    documento: data,
                    notificacionMostrada: true // Indicar que ya se mostró la notificación
                } 
            }));
        })
        .catch(error => {
            console.error('Error al subir el documento:', error);
            
            // Verificar si el error es 'database is locked' pero el archivo se subió correctamente
            if (error.message.includes('database is locked')) {
                console.log('Advertencia: La base de datos está bloqueada, pero el archivo se subió correctamente.');
                
                // Limpiar el formulario
                if (formularioSubida) formularioSubida.reset();
                
                // Cerrar el modal si está abierto
                if (this.elementos.modalSubirDocumento) {
                    this.elementos.modalSubirDocumento.hide();
                }
                
                // Recargar los documentos del área actual
                if (this.areaActual) {
                    this.cargarDocumentosArea(this.areaActual);
                }
                
                // Disparar evento personalizado para notificar a otros componentes
                document.dispatchEvent(new CustomEvent('documentoSubido', { 
                    detail: { 
                        areaId: this.areaActual,
                        notificacionMostrada: true // Indicar que ya se mostró la notificación
                    } 
                }));
                
                return; // Salir de la función sin mostrar mensaje de error
            }
            
            // Mensaje de error más descriptivo para otros errores
            let mensajeError = 'Ocurrió un error al subir el documento. ';
            
            if (error.message.includes('401') || error.message.includes('403')) {
                mensajeError += 'Por favor, inicia sesión nuevamente.';
                // Redirigir al login si no está autenticado
                window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
            } else if (error.message.includes('413')) {
                mensajeError = 'El archivo es demasiado grande. El tamaño máximo permitido es 100MB.';
            } else if (error.message.includes('404')) {
                mensajeError = 'No se pudo encontrar el recurso solicitado. Por favor, recarga la página.';
            } else if (error.message.includes('500')) {
                mensajeError = 'Error interno del servidor. Por favor, inténtalo de nuevo más tarde.';
            } else {
                mensajeError += error.message;
            }
            
            this.mostrarAlerta(mensajeError, 'error');
        })
        .finally(() => {
            // Ocultar spinner y habilitar botón
            if (spinner) spinner.classList.add('d-none');
            if (btnSubir) btnSubir.disabled = false;
            
            // Limpiar el input de archivo para permitir subir el mismo archivo nuevamente
            if (inputArchivo) inputArchivo.value = '';
        });
    },
    
    // Mostrar notificación en la esquina superior derecha
    mostrarAlerta: function(mensaje, tipo = 'info') {
        // Usar la función centralizada de notificaciones con fallback
        if (typeof window.mostrarNotificacion === 'function') {
            try {
                window.mostrarNotificacion(mensaje, tipo);
            } catch (error) {
                console.error('Error al mostrar notificación:', error);
                // Fallback a alert básico
                this.mostrarAlertaFallback(mensaje, tipo);
            }
        } else if (typeof ExpedienteApp !== 'undefined' && typeof ExpedienteApp.mostrarNotificacion === 'function') {
            // Intentar usar ExpedienteApp.mostrarNotificacion como fallback
            try {
                ExpedienteApp.mostrarNotificacion(mensaje, tipo);
            } catch (error) {
                console.error('Error al mostrar notificación con ExpedienteApp:', error);
                this.mostrarAlertaFallback(mensaje, tipo);
            }
        } else {
            // Fallback final: usar alert básico o SweetAlert si está disponible
            this.mostrarAlertaFallback(mensaje, tipo);
        }
    },
    
    // Fallback para mostrar alertas cuando no hay sistema de notificaciones
    mostrarAlertaFallback: function(mensaje, tipo = 'info') {
        if (typeof Swal !== 'undefined') {
            // Usar SweetAlert si está disponible
            const iconMap = {
                'success': 'success',
                'error': 'error',
                'warning': 'warning',
                'info': 'info',
                'danger': 'error'
            };
            Swal.fire({
                icon: iconMap[tipo] || 'info',
                title: tipo === 'error' || tipo === 'danger' ? 'Error' : tipo === 'success' ? 'Éxito' : 'Información',
                text: mensaje,
                timer: tipo === 'success' ? 2000 : 3000,
                showConfirmButton: tipo !== 'success'
            });
        } else {
            // Fallback final: usar alert básico
            alert(mensaje);
        }
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
        console.log('=== CARGAR DOCUMENTOS ÁREA ===');
        console.log('areaId recibido:', areaId, 'tipo:', typeof areaId);
        console.log('nombreArea recibido:', nombreArea);
        console.log('Array.isArray(areaId):', Array.isArray(areaId));
        
        // Guardar el areaId actual para usarlo después
        let areaIdSimple = areaId;
        if (typeof areaId === 'object' && areaId !== null) {
            console.warn('areaId es un objeto, extrayendo valor...', areaId);
            console.log('areaId.id:', areaId.id);
            console.log('areaId.value:', areaId.value);
            console.log('Object.values(areaId):', Object.values(areaId));
            areaIdSimple = areaId.id || areaId.value || Object.values(areaId)[0];
        }
        
        // Convertir a número si es string
        if (typeof areaIdSimple === 'string') {
            areaIdSimple = parseInt(areaIdSimple, 10);
        }
        
        console.log('areaIdSimple final:', areaIdSimple, 'tipo:', typeof areaIdSimple);
        
        this.areaActual = { id: areaIdSimple, nombre: nombreArea };
        console.log('areaActual establecido como:', this.areaActual);
        
        // Obtener el ID del expediente de la URL de diferentes maneras
        let expedienteId = null;
        
        // 1. Intentar obtener de la ruta /expedientes/123/detalle/
        const match = window.location.pathname.match(/\/expedientes\/(\d+)\//);
        if (match && match[1]) {
            expedienteId = match[1];
        } 
        // 2. Si no se encontró, intentar obtener el último número de la URL
        else {
            const urlParts = window.location.pathname.split('/').filter(Boolean);
            const lastPart = urlParts[urlParts.length - 1];
            if (lastPart && !isNaN(lastPart)) {
                expedienteId = lastPart;
            }
        }
        
        console.log('ID del expediente extraído:', expedienteId);
        
        if (!expedienteId || isNaN(expedienteId)) {
            const errorMsg = 'No se pudo identificar el expediente actual. URL: ' + window.location.pathname;
            console.error(errorMsg);
            this.mostrarError('No se pudo identificar el expediente actual. Por favor, recarga la página.');
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
            try {
                this.mostrarDocumentos(data.documentos || [], nombreArea);
            } catch (error) {
                console.error('Error al mostrar documentos:', error);
                this.mostrarError(`Error al mostrar los documentos: ${error.message}`);
            }
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
        
        // Obtener el areaId actual del objeto
        const areaIdActual = this.areaActual?.id || '';
        const nombreAreaActual = nombreArea || this.areaActual?.nombre || '';
        
        if (documentos.length === 0) {
            this.mostrarListaDocumentosVacia(nombreArea);
            return;
        }
        
        // Función auxiliar para obtener el icono según el tipo de archivo
        const getFileIcon = (tipo) => {
            const tipoLower = (tipo || '').toLowerCase();
            if (tipoLower.includes('pdf')) return 'bi-file-pdf-fill text-danger';
            if (tipoLower.includes('doc')) return 'bi-file-word-fill text-primary';
            if (tipoLower.includes('xls')) return 'bi-file-excel-fill text-success';
            if (tipoLower.includes('jpg') || tipoLower.includes('jpeg') || tipoLower.includes('png') || tipoLower.includes('gif')) return 'bi-file-image-fill text-info';
            return 'bi-file-earmark-fill text-secondary';
        };
        
        // Función auxiliar para obtener el tipo de archivo formateado
        const getTipoFormateado = (tipo, archivoNombre, archivoUrl) => {
            // Primero intentar obtener de la extensión del archivo (más confiable)
            let extension = '';
            
            // Intentar desde el nombre del archivo
            if (archivoNombre) {
                const parts = archivoNombre.split('.');
                if (parts.length > 1) {
                    extension = parts.pop().toLowerCase();
                }
            }
            
            // Si no hay extensión en el nombre, intentar desde la URL
            if (!extension && archivoUrl) {
                const urlParts = archivoUrl.split('.');
                if (urlParts.length > 1) {
                    extension = urlParts.pop().split('?')[0].toLowerCase(); // Remover query params
                }
            }
            
            // Mapeo de extensiones a tipos legibles
            const tipoMap = {
                'pdf': 'PDF',
                'doc': 'DOC',
                'docx': 'DOCX',
                'xls': 'XLS',
                'xlsx': 'XLSX',
                'ppt': 'PPT',
                'pptx': 'PPTX',
                'txt': 'TXT',
                'rtf': 'RTF',
                'jpg': 'JPG',
                'jpeg': 'JPG',
                'png': 'PNG',
                'gif': 'GIF',
                'bmp': 'BMP',
                'svg': 'SVG',
                'zip': 'ZIP',
                'rar': 'RAR'
            };
            
            if (extension && tipoMap[extension]) {
                return tipoMap[extension];
            }
            
            if (extension) {
                return extension.toUpperCase();
            }
            
            // Si hay tipo pero no extensión, intentar procesarlo
            if (tipo) {
                const tipoUpper = tipo.toUpperCase().trim();
                
                // Si ya está bien formateado, usarlo
                if (['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 'JPG', 'JPEG', 'PNG', 'GIF'].includes(tipoUpper)) {
                    return tipoUpper;
                }
                
                // Si dice "desconocido" o similar, ignorarlo
                if (tipoUpper.includes('DESCONOCIDO') || tipoUpper.includes('UNKNOWN') || tipoUpper === 'ARCHIVO') {
                    return 'ARCHIVO';
                }
                
                // Intentar extraer información del tipo MIME
                const tipoLower = tipo.toLowerCase();
                if (tipoLower.includes('pdf')) return 'PDF';
                if (tipoLower.includes('word') || tipoLower.includes('document')) {
                    return tipoLower.includes('openxml') ? 'DOCX' : 'DOC';
                }
                if (tipoLower.includes('excel') || tipoLower.includes('spreadsheet')) {
                    return tipoLower.includes('openxml') ? 'XLSX' : 'XLS';
                }
                if (tipoLower.includes('jpeg') || tipoLower.includes('jpg')) return 'JPG';
                if (tipoLower.includes('png')) return 'PNG';
                if (tipoLower.includes('gif')) return 'GIF';
                
                return tipoUpper;
            }
            
            return 'ARCHIVO';
        };
        
        // Función auxiliar para obtener el badge del tipo
        const getTypeBadge = (tipo, archivoNombre, archivoUrl) => {
            const tipoFormateado = getTipoFormateado(tipo, archivoNombre, archivoUrl);
            const tipoLower = tipoFormateado.toLowerCase();
            let badgeClass = 'bg-secondary';
            if (tipoLower === 'pdf') badgeClass = 'bg-danger';
            else if (tipoLower.includes('doc')) badgeClass = 'bg-primary';
            else if (tipoLower.includes('xls')) badgeClass = 'bg-success';
            else if (['jpg', 'jpeg', 'png', 'gif'].includes(tipoLower)) badgeClass = 'bg-info';
            return `<span class="badge ${badgeClass}">${tipoFormateado}</span>`;
        };
        
        // Crear la tabla de documentos con diseño mejorado
        let html = `
            <style>
                .documentos-table {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                    overflow: hidden;
                }
                .documentos-table .table {
                    margin-bottom: 0;
                }
                .documentos-table thead {
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-bottom: 2px solid #dee2e6;
                }
                .documentos-table thead th {
                    font-weight: 600;
                    color: #495057;
                    padding: 1rem;
                    border-bottom: 2px solid #dee2e6;
                    text-transform: uppercase;
                    font-size: 0.85rem;
                    letter-spacing: 0.5px;
                }
                .documentos-table tbody tr {
                    transition: all 0.2s ease;
                    border-bottom: 1px solid #f0f0f0;
                }
                .documentos-table tbody tr:hover {
                    background-color: #f8f9fa;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                .documentos-table tbody td {
                    padding: 1.25rem 1rem;
                    vertical-align: middle;
                    color: #212529;
                }
                .documento-nombre {
                    font-weight: 600;
                    color: #212529;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .documento-observaciones {
                    font-size: 0.85rem;
                    color: #6c757d;
                    font-style: italic;
                    margin-top: 0.25rem;
                }
                .documento-usuario {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: #495057;
                    font-size: 0.9rem;
                }
                .documento-usuario i {
                    color: #6c757d;
                }
                .documento-fecha {
                    color: #6c757d;
                    font-size: 0.9rem;
                }
                .btn-accion-documento {
                    background: white;
                    border: 1.5px solid #212529;
                    color: #212529;
                    padding: 0.5rem 0.75rem;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 36px;
                    height: 36px;
                    text-decoration: none;
                }
                .btn-accion-documento:hover {
                    background: #212529;
                    color: white;
                    border-color: #212529;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .btn-accion-documento i {
                    font-size: 1rem;
                }
                .btn-accion-eliminar:hover {
                    background: #dc3545;
                    border-color: #dc3545;
                    color: white;
                }
            </style>
            <div class="documentos-table">
                <div class="card-header d-flex justify-content-between align-items-center" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-bottom: 2px solid #dee2e6; padding: 1.25rem;">
                    <h5 class="mb-0" style="font-weight: 700; color: #212529;">
                        <i class="bi bi-folder2-open me-2"></i>Documentos de ${nombreArea}
                    </h5>
                    <button class="btn btn-sm btn-primary" onclick="abrirModalSubirDocumento('${areaIdActual}', '${nombreAreaActual.replace(/'/g, "\\'")}')" style="font-weight: 600;">
                        <i class="bi bi-plus-lg me-1"></i> Agregar Documento
                    </button>
                </div>
                <div class="table-responsive">
                    <table class="table mb-0">
                        <thead>
                            <tr>
                                <th style="width: 30%;">Nombre</th>
                                <th style="width: 8%;">Tipo</th>
                                <th style="width: 8%;">Tamaño</th>
                                <th style="width: 12%;">Fecha y Hora</th>
                                <th style="width: 12%;">Subido por</th>
                                <th style="width: 15%;">Observaciones</th>
                                <th style="width: 15%;" class="text-center">Acciones</th>
                            </tr>
                        </thead>
                        <tbody>`;
        
        documentos.forEach(doc => {
            // Logging para depuración
            console.log('📄 Procesando documento:', {
                id: doc.id,
                documento_id: doc.documento_id,
                nombre: doc.nombre || doc.nombre_archivo,
                todos_los_campos: Object.keys(doc)
            });
            
            // Asegurar que tenemos un ID válido
            const documentoId = doc.id || doc.documento_id || doc.pk;
            if (!documentoId) {
                console.error('❌ Documento sin ID válido:', doc);
            }
            
            // Formatear fecha y hora
            let fechaFormateada = 'No disponible';
            if (doc.fecha_subida_completa) {
                fechaFormateada = doc.fecha_subida_completa;
            } else if (doc.fecha_subida) {
                try {
                    const fecha = new Date(doc.fecha_subida);
                    if (!isNaN(fecha.getTime())) {
                        fechaFormateada = fecha.toLocaleString('es-ES', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    }
                } catch (e) {
                    fechaFormateada = doc.fecha_subida;
                }
            }
            
            // Obtener tipo de archivo formateado
            const tipoArchivo = getTipoFormateado(doc.tipo || doc.tipo_archivo, doc.nombre_archivo || doc.nombre, doc.archivo_url);
            
            // Obtener tamaño formateado
            const tamanoFormateado = doc.tamano_formateado || this.formatearTamanio(doc.tamano_archivo || 0);
            
            // Obtener usuario
            const usuario = doc.subido_por || 'Usuario desconocido';
            
            // Obtener observaciones y escapar caracteres especiales de forma segura
            let observaciones = '';
            try {
                observaciones = (doc.observaciones || doc.descripcion || '').toString();
            } catch (e) {
                observaciones = '';
            }
            const observacionesEscapadas = observaciones.replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            
            let nombreEscapado = 'Sin nombre';
            try {
                nombreEscapado = (doc.nombre || doc.nombre_archivo || 'Sin nombre').toString().replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            } catch (e) {
                nombreEscapado = 'Sin nombre';
            }
            
            let usuarioEscapado = 'Usuario desconocido';
            try {
                usuarioEscapado = usuario.toString().replace(/"/g, '&quot;').replace(/'/g, '&#39;');
            } catch (e) {
                usuarioEscapado = 'Usuario desconocido';
            }
            
            // Truncar observaciones para mostrar
            const observacionesTruncadas = observaciones.length > 30 ? observacionesEscapadas.substring(0, 30) + '...' : observacionesEscapadas;
            
            html += `
                <tr>
                    <td>
                        <div class="documento-nombre">
                            <i class="bi ${getFileIcon(tipoArchivo)}"></i>
                            <div>
                                <div>${nombreEscapado}</div>
                                ${observaciones ? `<div class="documento-observaciones">${observacionesEscapadas}</div>` : ''}
                            </div>
                        </div>
                    </td>
                    <td>${getTypeBadge(doc.tipo || doc.tipo_archivo, doc.nombre_archivo || doc.nombre, doc.archivo_url)}</td>
                    <td><span class="text-muted">${tamanoFormateado}</span></td>
                    <td>
                        <div class="documento-fecha">
                            <i class="bi bi-calendar3 me-1"></i>${fechaFormateada}
                        </div>
                    </td>
                    <td>
                        <div class="documento-usuario">
                            <i class="bi bi-person-circle"></i>
                            <span>${usuarioEscapado}</span>
                        </div>
                    </td>
                    <td>
                        ${observaciones ? `<span class="text-muted small" title="${observacionesEscapadas}">${observacionesTruncadas}</span>` : '<span class="text-muted small">Sin observaciones</span>'}
                    </td>
                    <td class="text-center">
                        <div class="d-flex justify-content-center gap-2">
                            <a href="${doc.archivo_url || '#'}" 
                               class="btn-accion-documento" 
                               target="_blank" 
                               title="Ver documento">
                                <i class="bi bi-eye"></i>
                            </a>
                            <a href="${doc.archivo_url || '#'}" 
                               class="btn-accion-documento" 
                               download 
                               title="Descargar documento">
                                <i class="bi bi-download"></i>
                            </a>
                            <button type="button" 
                                    class="btn-accion-documento btn-accion-eliminar btn-eliminar-documento" 
                                    data-documento-id="${documentoId || ''}" 
                                    data-documento-nombre="${nombreEscapado}" 
                                    title="Eliminar documento"
                                    aria-label="Eliminar documento ${nombreEscapado}"
                                    onclick="event.preventDefault(); event.stopPropagation(); if(typeof DocumentosApp !== 'undefined' && typeof DocumentosApp.confirmarEliminarDocumento === 'function') { const btn = event.currentTarget; const docId = btn.getAttribute('data-documento-id'); const docNombre = btn.getAttribute('data-documento-nombre'); console.log('🖱️ Click directo en botón (onclick):', docId, docNombre); DocumentosApp.confirmarEliminarDocumento(docId, docNombre); } else { console.error('DocumentosApp no disponible'); alert('Error: No se pudo inicializar la función de eliminación'); } return false;">
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
        
        try {
            contenedor.innerHTML = html;
            console.log('✅ HTML insertado en contenedor, inicializando listeners...');
            
            // Inicializar event listeners para botones de eliminar después de insertar HTML
            if (typeof this.initEliminarDocumentos === 'function') {
                console.log('🔧 Llamando a initEliminarDocumentos...');
                this.initEliminarDocumentos();
            } else {
                console.warn('⚠️ initEliminarDocumentos no está disponible');
            }
            
            // Verificar que los botones se crearon correctamente
            const botonesEliminar = document.querySelectorAll('.btn-eliminar-documento');
            console.log(`📊 Botones de eliminar encontrados después de insertar HTML: ${botonesEliminar.length}`);
            botonesEliminar.forEach((btn, idx) => {
                const docId = btn.getAttribute('data-documento-id');
                console.log(`  Botón ${idx + 1}: data-documento-id="${docId}"`);
            });
        } catch (error) {
            console.error('❌ Error al insertar HTML en el contenedor:', error);
            console.error('Error details:', error.message, error.stack);
            this.mostrarError('Error al mostrar los documentos. Por favor, recarga la página.');
        }
    },
    
    // Mostrar lista vacía de documentos
    mostrarListaDocumentosVacia: function(nombreArea) {
        const contenedor = document.getElementById('contenido-documentos');
        if (!contenedor) return;
        
        // Obtener el areaId actual del objeto
        const areaIdActual = this.areaActual?.id || '';
        const nombreAreaActual = nombreArea || this.areaActual?.nombre || '';
        
        contenedor.innerHTML = `
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="bi bi-folder2-open display-4 text-muted"></i>
                </div>
                <h4>No hay documentos en ${nombreAreaActual}</h4>
                <p class="text-muted mb-4">Aún no se han cargado documentos para esta área.</p>
                <button class="btn btn-azul-oscuro" onclick="abrirModalSubirDocumento('${areaIdActual}', '${nombreAreaActual.replace(/'/g, "\\'")}')">
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
    
    // Inicializar event listeners para botones de eliminar
    initEliminarDocumentos: function() {
        console.log('🔧 Inicializando event listeners para botones de eliminar...');
        const botonesEliminar = document.querySelectorAll('.btn-eliminar-documento');
        console.log(`📊 Se encontraron ${botonesEliminar.length} botones de eliminar`);
        
        if (botonesEliminar.length === 0) {
            console.warn('⚠️ No se encontraron botones de eliminar. Verifica que los documentos se estén mostrando correctamente.');
            return;
        }
        
        botonesEliminar.forEach((btn, index) => {
            // Verificar que el botón tenga los atributos necesarios
            const documentoId = btn.getAttribute('data-documento-id');
            const documentoNombre = btn.getAttribute('data-documento-nombre') || 'este documento';
            
            if (!documentoId) {
                console.error(`❌ Botón ${index + 1} no tiene data-documento-id:`, btn);
                return;
            }
            
            console.log(`✅ Botón ${index + 1} configurado:`, documentoId, documentoNombre);
            
            // Remover listeners previos si existen
            const nuevoBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(nuevoBtn, btn);
            
            // Agregar listener directo al botón
            nuevoBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log(`🖱️ Click directo en botón eliminar ${index + 1}:`, documentoId, documentoNombre);
                DocumentosApp.confirmarEliminarDocumento(documentoId, documentoNombre);
            }, true); // Usar capture phase
        });
        
        console.log('✅ Event listeners para botones de eliminar inicializados correctamente');
    },
    
    // Confirmar eliminación de documento
    confirmarEliminarDocumento: function(documentoId, nombreDocumento) {
        console.log('🔔 confirmarEliminarDocumento llamada con:', documentoId, nombreDocumento);
        
        // Validar que documentoId sea válido
        if (!documentoId || documentoId === 'undefined' || documentoId === 'null' || documentoId === '' || documentoId === '0') {
            console.error('❌ ID de documento no válido:', documentoId);
            this.mostrarAlerta('Error: No se pudo identificar el documento a eliminar', 'error');
            return;
        }
        
        const nombreMostrar = nombreDocumento || 'este documento';
        const mensaje = `¿Estás seguro de que deseas eliminar "${nombreMostrar}"?\n\nEsta acción no se puede deshacer.`;
        
        if (confirm(mensaje)) {
            console.log('✅ Usuario confirmó eliminación, llamando a eliminarDocumento');
            this.eliminarDocumento(documentoId);
        } else {
            console.log('❌ Usuario canceló la eliminación');
        }
    },
    
    // Eliminar documento
    eliminarDocumento: function(documentoId) {
        console.log('🗑️ eliminarDocumento llamada con ID:', documentoId, 'tipo:', typeof documentoId);
        
        // Validar documentoId
        if (!documentoId || documentoId === 'undefined' || documentoId === 'null' || documentoId === '' || documentoId === '0') {
            console.error('❌ ID de documento no válido en eliminarDocumento:', documentoId);
            this.mostrarAlerta('Error: ID de documento no válido', 'error');
            return;
        }
        
        // 1. Encontrar el elemento del documento (puede ser una fila de tabla o un elemento con data-documento-id)
        let documentoElement = document.querySelector(`tr[data-documento-id="${documentoId}"]`);
        if (!documentoElement) {
            documentoElement = document.querySelector(`.documento-item[data-documento-id="${documentoId}"]`);
        }
        if (!documentoElement) {
            // Buscar por el botón que tiene el data-documento-id y subir al tr padre
            const btnEliminar = document.querySelector(`.btn-eliminar-documento[data-documento-id="${documentoId}"]`);
            if (btnEliminar) {
                documentoElement = btnEliminar.closest('tr');
                console.log('📋 Elemento encontrado a través del botón:', documentoElement);
            }
        }
        if (!documentoElement) {
            console.error('❌ No se encontró el elemento del documento con ID:', documentoId);
            console.log('🔍 Buscando todos los elementos con data-documento-id...');
            const todosLosElementos = document.querySelectorAll('[data-documento-id]');
            console.log(`📊 Elementos encontrados: ${todosLosElementos.length}`);
            todosLosElementos.forEach((el, idx) => {
                console.log(`  ${idx + 1}. ID: ${el.getAttribute('data-documento-id')}, Clase: ${el.className}, Tag: ${el.tagName}`);
            });
            this.mostrarAlerta('No se pudo encontrar el documento a eliminar en la página', 'error');
            return;
        }
        
        console.log('✅ Elemento del documento encontrado:', documentoElement);

        // 2. Obtener referencias necesarias
        const areaActual = this.areaActual;
        const contenedorPadre = documentoElement.parentNode;
        
        // 3. Eliminar el elemento del DOM
        documentoElement.style.opacity = '0.5';
        documentoElement.style.pointerEvents = 'none';
        
        // 4. Mostrar mensaje de carga
        this.mostrarAlerta('Eliminando documento...', 'info');
        
        // 5. Obtener el ID del expediente de la URL de forma más robusta
        const pathParts = window.location.pathname.split('/').filter(p => p);
        let expedienteId = null;
        const expedienteIndex = pathParts.indexOf('expedientes');
        
        if (expedienteIndex !== -1 && pathParts[expedienteIndex + 1]) {
            expedienteId = pathParts[expedienteIndex + 1];
        }
        
        // También intentar obtener del campo oculto si existe
        if (!expedienteId || isNaN(expedienteId)) {
            const expedienteIdInput = document.getElementById('expediente_id');
            if (expedienteIdInput && expedienteIdInput.value) {
                expedienteId = expedienteIdInput.value;
            }
        }
        
        if (!expedienteId || isNaN(expedienteId)) {
            console.error('No se pudo determinar el ID del expediente');
            console.log('URL actual:', window.location.pathname);
            console.log('pathParts:', pathParts);
            this.mostrarAlerta('Error: No se pudo determinar el expediente actual', 'error');
            // Restaurar el elemento
            documentoElement.style.opacity = '1';
            documentoElement.style.pointerEvents = 'auto';
            return;
        }
        
        // 6. Enviar la petición al servidor con la URL correcta
        const url = `/expedientes/${expedienteId}/documentos/eliminar/${documentoId}/`;
        console.log('🗑️ Eliminando documento:', documentoId, 'del expediente:', expedienteId);
        console.log('URL de eliminación:', url);
        const csrfToken = this.getCookie('csrftoken');
        
        if (!csrfToken) {
            console.error('No se pudo obtener el token CSRF');
            this.mostrarAlerta('Error: No se pudo obtener el token de seguridad', 'error');
            documentoElement.style.opacity = '1';
            documentoElement.style.pointerEvents = 'auto';
            return;
        }
        
        // Usar setTimeout para permitir que la UI se actualice
        setTimeout(() => {
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                console.log('📡 Respuesta del servidor recibida:', response.status, response.statusText);
                if (!response.ok) {
                    // Intentar obtener el mensaje de error del servidor
                    return response.json().then(err => {
                        console.error('❌ Error del servidor:', err);
                        throw new Error(err.error || err.message || `Error ${response.status}: ${response.statusText}`);
                    }).catch(() => {
                        // Si no se puede parsear como JSON, lanzar error genérico
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('📦 Datos recibidos del servidor:', data);
                if (data.success) {
                    console.log('✅ Documento eliminado exitosamente en el servidor');
                    // Eliminar el elemento del DOM solo después de confirmación del servidor
                    if (documentoElement && documentoElement.parentNode) {
                        documentoElement.remove();
                        console.log('🗑️ Elemento eliminado del DOM');
                    }
                    this.mostrarAlerta('Documento eliminado correctamente', 'success');
                    
                    // Disparar evento personalizado para notificar a otros componentes
                    document.dispatchEvent(new CustomEvent('documentoEliminado', { 
                        detail: { 
                            documentoId: documentoId,
                            areaId: this.areaActual?.id,
                            notificacionMostrada: true
                        } 
                    }));
                    
                    // Recargar los documentos del área actual
                    if (this.areaActual && this.areaActual.id) {
                        console.log('🔄 Recargando documentos del área:', this.areaActual);
                        setTimeout(() => {
                            this.cargarDocumentosArea(this.areaActual.id, this.areaActual.nombre);
                        }, 500);
                    } else {
                        // Verificar si quedan documentos en el área
                        const contenedorDocumentos = document.querySelector('#contenido-documentos tbody');
                        if (contenedorDocumentos && contenedorDocumentos.children.length === 0 && areaActual) {
                            this.mostrarListaDocumentosVacia(areaActual.nombre || 'esta área');
                        }
                    }
                } else {
                    console.error('❌ El servidor respondió con success=false:', data);
                    throw new Error(data.error || data.message || 'Error al eliminar el documento');
                }
            })
            .catch(error => {
                console.error('❌ Error al eliminar el documento:', error);
                console.error('Stack trace:', error.stack);
                // Restaurar el elemento
                if (documentoElement) {
                    documentoElement.style.opacity = '1';
                    documentoElement.style.pointerEvents = 'auto';
                }
                this.mostrarAlerta(error.message || 'Error al eliminar el documento. Por favor, intenta nuevamente.', 'error');
            });
        }, 100); // Pequeño retraso para permitir que la UI se actualice
    }
};

// Inicializar el módulo cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    DocumentosApp.init();
});
