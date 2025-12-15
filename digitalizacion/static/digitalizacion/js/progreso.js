/**
 * Módulo para manejar la barra de progreso del expediente
 */

const ProgresoApp = {
    // Configuración
    config: {
        intervaloActualizacion: 30000, // 30 segundos
        urlBase: '/expedientes',
    },
    
    // Estado
    estado: {
        intervalo: null,
        expedienteId: null,
        ultimaActualizacion: null
    },
    
    // Función auxiliar para obtener cookies
    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // ¿Esta cadena de cookie comienza con el nombre que queremos?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    
    // Inicialización
    init: function() {
        console.log('Inicializando módulo de progreso');
        this.obtenerElementos();
        this.establecerExpedienteId();
        
        if (this.estado.expedienteId) {
            this.iniciarSeguimiento();
        } else {
            console.warn('No se encontró el ID del expediente para el seguimiento de progreso');
        }
        
        this.agregarManejadoresEventos();
    },
    
    // Obtener referencias a los elementos del DOM
    obtenerElementos: function() {
        this.elementos = {
            barraProgreso: document.getElementById('barra-progreso'),
            porcentajeProgreso: document.getElementById('porcentaje-progreso'),
            textoProgreso: document.getElementById('texto-progreso'),
            fechaActualizacion: document.getElementById('fecha-actualizacion')
        };
    },
    
    // Establecer el ID del expediente
    establecerExpedienteId: function() {
        if (this.elementos.barraProgreso) {
            this.estado.expedienteId = this.elementos.barraProgreso.getAttribute('data-expediente-id');
        }
    },
    
    // Iniciar el seguimiento del progreso
    iniciarSeguimiento: function() {
        // Cargar datos iniciales
        this.actualizarProgreso();
        
        // Configurar actualización periódica
        this.estado.intervalo = setInterval(
            () => this.actualizarProgreso(), 
            this.config.intervaloActualizacion
        );
        
        console.log(`Seguimiento de progreso iniciado para el expediente ${this.estado.expedienteId}`);
    },
    
    // Detener el seguimiento del progreso
    detenerSeguimiento: function() {
        if (this.estado.intervalo) {
            clearInterval(this.estado.intervalo);
            this.estado.intervalo = null;
            console.log('Seguimiento de progreso detenido');
        }
    },
    
    // Actualizar el progreso desde el servidor
    actualizarProgreso: async function() {
        if (!this.estado.expedienteId) {
            console.warn('No se puede actualizar el progreso: ID de expediente no definido');
            return;
        }
        
        try {
            // Construir la URL usando la URL base de Django
            const url = `/expedientes/${this.estado.expedienteId}/obtener-progreso/`;
            console.log('Solicitando progreso desde:', url);
            
            const csrftoken = this.getCookie('csrftoken');
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrftoken || ''
                },
                credentials: 'same-origin'
            });
            
            console.log('Respuesta del servidor:', response);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Error HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Datos de progreso recibidos:', data);
            
            if (data && typeof data.porcentaje !== 'undefined') {
                this.actualizarInterfaz(data);
                this.estado.ultimaActualizacion = new Date();
                console.log('Progreso actualizado correctamente');
            } else {
                throw new Error('Formato de respuesta inválido');
            }
            
        } catch (error) {
            console.error('Error al actualizar el progreso:', error);
            // Mostrar un mensaje de error sutil en la interfaz
            if (this.elementos.textoProgreso) {
                this.elementos.textoProgreso.textContent = 'No se pudo actualizar el progreso';
                this.elementos.textoProgreso.classList.add('text-danger');
            }
        }
    },
    
    // Actualizar la interfaz con los datos del progreso
    actualizarInterfaz: function(data) {
        const { barraProgreso, porcentajeProgreso, textoProgreso, fechaActualizacion } = this.elementos;
        const { porcentaje, completadas, total, ultima_actualizacion } = data;
        
        // Actualizar barra de progreso
        if (barraProgreso) {
            barraProgreso.style.width = `${porcentaje}%`;
            barraProgreso.setAttribute('aria-valuenow', porcentaje);
            barraProgreso.classList.remove('bg-danger', 'bg-warning', 'bg-success');
            
            // Cambiar color según el porcentaje
            if (porcentaje < 30) {
                barraProgreso.classList.add('bg-danger');
            } else if (porcentaje < 80) {
                barraProgreso.classList.add('bg-warning');
            } else {
                barraProgreso.classList.add('bg-success');
            }
        }
        
        // Actualizar porcentaje
        if (porcentajeProgreso) {
            porcentajeProgreso.textContent = `${Math.round(porcentaje)}%`;
        }
        
        // Actualizar texto descriptivo
        if (textoProgreso) {
            textoProgreso.textContent = `${completadas} de ${total} tareas completadas`;
        }
        
        // Actualizar fecha de última actualización
        if (fechaActualizacion && ultima_actualizacion) {
            this.actualizarFechaUltimaActualizacion(ultima_actualizacion);
        }
        
        // Disparar evento personalizado
        document.dispatchEvent(new CustomEvent('progresoActualizado', { detail: data }));
    },
    
    // Actualizar la fecha de última actualización
    actualizarFechaUltimaActualizacion: function(fechaISO) {
        const { fechaActualizacion } = this.elementos;
        if (!fechaActualizacion) return;
        
        try {
            const fecha = new Date(fechaISO);
            const opciones = {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            
            const fechaFormateada = fecha.toLocaleDateString('es-MX', opciones);
            fechaActualizacion.textContent = `Última actualización: ${fechaFormateada}`;
            fechaActualizacion.setAttribute('datetime', fechaISO);
            fechaActualizacion.title = `Última actualización: ${fechaFormateada}`;
            
        } catch (error) {
            console.error('Error al formatear la fecha:', error);
        }
    },
    
    // Agregar manejadores de eventos
    agregarManejadoresEventos: function() {
        // Actualizar cuando se sube o elimina un documento
        document.addEventListener('documentoSubido', () => this.actualizarProgreso());
        document.addEventListener('documentoEliminado', () => this.actualizarProgreso());
        
        // Actualizar manualmente al hacer clic en el botón de actualizar
        const btnActualizar = document.querySelector('.btn-actualizar-progreso');
        if (btnActualizar) {
            btnActualizar.addEventListener('click', (e) => {
                e.preventDefault();
                this.actualizarProgreso();
            });
        }
    },
    
    // Limpiar recursos
    destruir: function() {
        this.detenerSeguimiento();
        
        // Eliminar manejadores de eventos
        document.removeEventListener('documentoSubido', this.actualizarProgreso);
        document.removeEventListener('documentoEliminado', this.actualizarProgreso);
    }
};

// Inicializar el módulo cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    ProgresoApp.init();
});

// Hacer que el módulo esté disponible globalmente
window.ProgresoApp = ProgresoApp;
