/**
 * Sistema avanzado de gestión de notificaciones
 * Maneja cola de notificaciones, evita duplicados y proporciona una API limpia
 */

class GestorNotificaciones {
    constructor() {
        this.cola = [];
        this.notificacionesActivas = new Set();
        this.notificacionVisible = false;
        this.tiempoVisible = 3000; // 3 segundos por defecto
        this.ultimoMensaje = '';
        this.ultimoTiempo = 0;
        this.tiempoMinimoEntreIguales = 1000; // 1 segundo entre mensajes iguales
        
        this.inicializarEstilos();
        this.inicializarContenedor();
    }

    inicializarEstilos() {
        if (document.getElementById('estilos-notificaciones-avanzadas')) return;
        
        const estilos = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            #notificaciones-avanzadas {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                max-width: 350px;
                width: 100%;
                pointer-events: none;
            }
            
            .notificacion-avanzada {
                position: relative;
                padding: 15px 20px;
                margin-bottom: 10px;
                border-radius: 8px;
                color: #fff;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                justify-content: space-between;
                animation: slideInRight 0.3s forwards;
                pointer-events: auto;
                transform: translateX(120%);
                opacity: 0;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .notificacion-avanzada.mostrando {
                transform: translateX(0);
                opacity: 1;
            }
            
            .notificacion-avanzada.ocultando {
                animation: slideOutRight 0.3s forwards;
            }
            
            .notificacion-contenido {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
            }
            
            .notificacion-icono {
                font-size: 20px;
                flex-shrink: 0;
            }
            
            .notificacion-mensaje {
                font-size: 14px;
                line-height: 1.4;
            }
            
            .notificacion-progreso {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(255, 255, 255, 0.5);
                width: 100%;
                transform-origin: left;
            }
            
            .notificacion-cerrar {
                background: none;
                border: none;
                color: inherit;
                font-size: 16px;
                cursor: pointer;
                margin-left: 10px;
                opacity: 0.7;
                transition: opacity 0.2s;
            }
            
            .notificacion-cerrar:hover {
                opacity: 1;
            }
            
            /* Estilos para diferentes tipos de notificación */
            .notificacion-avanzada.tipo-success {
                background: linear-gradient(135deg, #10B981, #059669);
            }
            
            .notificacion-avanzada.tipo-error {
                background: linear-gradient(135deg, #EF4444, #DC2626);
            }
            
            .notificacion-avanzada.tipo-warning {
                background: linear(135deg, #F59E0B, #D97706);
                color: #1F2937;
            }
            
            .notificacion-avanzada.tipo-info {
                background: linear-gradient(135deg, #3B82F6, #2563EB);
            }
        `;
        
        const style = document.createElement('style');
        style.id = 'estilos-notificaciones-avanzadas';
        style.textContent = estilos;
        document.head.appendChild(style);
    }
    
    inicializarContenedor() {
        if (document.getElementById('notificaciones-avanzadas')) return;
        
        const contenedor = document.createElement('div');
        contenedor.id = 'notificaciones-avanzadas';
        document.body.appendChild(contenedor);
    }
    
    mostrar(mensaje, tipo = 'info', tiempo = 3000) {
        // Prevenir mensajes duplicados rápidos
        const ahora = Date.now();
        if (mensaje === this.ultimoMensaje && 
            (ahora - this.ultimoTiempo) < this.tiempoMinimoEntreIguales) {
            return;
        }
        
        this.ultimoMensaje = mensaje;
        this.ultimoTiempo = ahora;
        
        // Crear ID único para esta notificación
        const id = 'notif-' + Math.random().toString(36).substr(2, 9);
        
        // Añadir a la cola
        this.cola.push({ id, mensaje, tipo, tiempo });
        
        // Procesar la cola
        this.procesarCola();
        
        return id;
    }
    
    procesarCola() {
        // Si ya hay una notificación mostrándose o no hay notificaciones en cola, salir
        if (this.notificacionVisible || this.cola.length === 0) return;
        
        this.notificacionVisible = true;
        const notificacion = this.cola.shift();
        
        // Crear elemento de notificación
        const notificacionElemento = this.crearNotificacion(notificacion);
        
        // Agregar al DOM
        const contenedor = document.getElementById('notificaciones-avanzadas');
        contenedor.appendChild(notificacionElemento);
        
        // Forzar reflow para que la animación funcione
        void notificacionElemento.offsetWidth;
        
        // Mostrar con animación
        notificacionElemento.classList.add('mostrando');
        
        // Configurar tiempo de cierre automático
        const tiempoCierre = notificacion.tiempo || this.tiempoVisible;
        let timeoutId;
        
        const cerrar = () => {
            // Si ya se está cerrando, salir
            if (notificacionElemento.classList.contains('ocultando')) return;
            
            // Limpiar el timeout si existe
            if (timeoutId) clearTimeout(timeoutId);
            
            // Iniciar animación de salida
            notificacionElemento.classList.remove('mostrando');
            notificacionElemento.classList.add('ocultando');
            
            // Eliminar después de la animación
            notificacionElemento.addEventListener('animationend', () => {
                notificacionElemento.remove();
                this.notificacionesActivas.delete(notificacion.id);
                this.notificacionVisible = false;
                
                // Procesar siguiente notificación
                setTimeout(() => this.procesarCola(), 100);
            }, { once: true });
        };
        
        // Configurar cierre automático
        timeoutId = setTimeout(cerrar, tiempoCierre);
        
        // Cerrar al hacer clic
        notificacionElemento.addEventListener('click', cerrar);
        
        // Agregar a notificaciones activas
        this.notificacionesActivas.add(notificacion.id);
    }
    
    crearNotificacion({ id, mensaje, tipo }) {
        const notificacion = document.createElement('div');
        notificacion.className = `notificacion-avanzada tipo-${tipo}`;
        notificacion.dataset.id = id;
        
        // Crear icono según el tipo
        let icono = 'ℹ️';
        switch (tipo) {
            case 'success':
                icono = '✓';
                break;
            case 'error':
                icono = '✕';
                break;
            case 'warning':
                icono = '⚠️';
                break;
            default:
                icono = 'ℹ️';
        }
        
        notificacion.innerHTML = `
            <div class="notificacion-contenido">
                <span class="notificacion-icono">${icono}</span>
                <span class="notificacion-mensaje">${mensaje}</span>
            </div>
            <button class="notificacion-cerrar" aria-label="Cerrar">&times;</button>
            <div class="notificacion-progreso"></div>
        `;
        
        // Animar la barra de progreso
        const progreso = notificacion.querySelector('.notificacion-progreso');
        if (progreso) {
            progreso.style.animation = `progreso ${this.tiempoVisible}ms linear forwards`;
        }
        
        return notificacion;
    }
    
    // Métodos de conveniencia
    success(mensaje, tiempo) {
        return this.mostrar(mensaje, 'success', tiempo);
    }
    
    error(mensaje, tiempo) {
        return this.mostrar(mensaje, 'error', tiempo);
    }
    
    warning(mensaje, tiempo) {
        return this.mostrar(mensaje, 'warning', tiempo);
    }
    
    info(mensaje, tiempo) {
        return this.mostrar(mensaje, 'info', tiempo);
    }
}

// Crear instancia global
window.notificaciones = new GestorNotificaciones();

// Función de compatibilidad para reemplazar la anterior
window.mostrarNotificacion = function(mensaje, tipo = 'info', tiempo = 3000) {
    return window.notificaciones.mostrar(mensaje, tipo, tiempo);
};

// Métodos de conveniencia globales
window.mostrarNotificacion.exito = function(mensaje, tiempo) {
    return window.notificaciones.success(mensaje, tiempo);
};

window.mostrarNotificacion.error = function(mensaje, tiempo) {
    return window.notificaciones.error(mensaje, tiempo);
};

window.mostrarNotificacion.advertencia = function(mensaje, tiempo) {
    return window.notificaciones.warning(mensaje, tiempo);
};

window.mostrarNotificacion.informacion = function(mensaje, tiempo) {
    return window.notificaciones.info(mensaje, tiempo);
};
