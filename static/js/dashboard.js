// ============================================
// DASHBOARD FILEVAULT - FUNCIONALIDAD PRINCIPAL
// ============================================

// Funcionalidad del sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const header = document.getElementById('header');
    const mainContent = document.getElementById('mainContent');
    const collapseBtn = document.getElementById('collapseBtn');
    
    if (collapseBtn) {
        collapseBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            header.classList.toggle('collapsed');
            mainContent.classList.toggle('collapsed');
            
            // Cambiar el icono
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.className = 'bi bi-chevron-right';
            } else {
                icon.className = 'bi bi-chevron-left';
            }
        });
    }
    
    // Búsqueda en tiempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            // Implementar búsqueda en tiempo real aquí
            console.log('Buscando:', query);
        });
    }
    
    // Cargar notificaciones solo si no están ocultas
    if (!document.querySelector('.notification-bell[style*="display: none"]')) {
        cargarNotificaciones();
    }
    
    // Cargar mensajes del chat
    cargarMensajesChat();
    
    // Cargar tema guardado
    cargarTemaGuardado();
    
    // Agregar event listener adicional para el botón de perfil
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        console.log('Botón de perfil encontrado, agregando event listener');
        profileBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Botón de perfil clickeado (event listener)');
            abrirPerfil();
        });
        console.log('Event listener agregado al botón de perfil');
    } else {
        // Solo mostrar error si estamos en el dashboard (página principal)
        if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
            console.error('ERROR: No se encontró el botón de perfil con ID profileBtn');
            console.log('Botones en la página:', document.querySelectorAll('button'));
        }
    }
});

// Funciones para abrir modales
function abrirChat() {
    console.log('Abriendo chat...');
    if (typeof bootstrap !== 'undefined') {
        const chatModal = new bootstrap.Modal(document.getElementById('chatModal'));
        chatModal.show();
    } else {
        // Solo mostrar error si estamos en el dashboard (página principal)
        if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
            console.error('Bootstrap no está disponible');
        }
    }
}

function abrirNotificaciones() {
    console.log('Abriendo notificaciones...');
    
    const notificationsModalElement = document.getElementById('notificationsModal');
    
    if (notificationsModalElement) {
        // Intentar con Bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            try {
                const modal = bootstrap.Modal.getOrCreateInstance(notificationsModalElement);
                modal.show();
                console.log('Modal de notificaciones abierto con Bootstrap 5');
                return;
            } catch (error) {
                console.log('Error con Bootstrap 5:', error);
            }
        }
        
        // Método fallback
        const triggerBtn = document.createElement('button');
        triggerBtn.setAttribute('data-bs-toggle', 'modal');
        triggerBtn.setAttribute('data-bs-target', '#notificationsModal');
        triggerBtn.style.display = 'none';
        document.body.appendChild(triggerBtn);
        triggerBtn.click();
        document.body.removeChild(triggerBtn);
        
        // Si jQuery está disponible
        if (typeof $ !== 'undefined') {
            try {
                $('#notificationsModal').modal('show');
                console.log('Modal de notificaciones abierto con jQuery');
            } catch (error) {
                console.log('Error con jQuery:', error);
            }
        }
    } else {
        // Solo mostrar error si estamos en el dashboard (página principal)
        if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
            console.error('Modal de notificaciones no encontrado');
        }
    }
}

function abrirPerfil() {
    console.log('Intentando abrir modal de perfil...');
    
    // Método alternativo usando data attributes de Bootstrap
    const profileModalElement = document.getElementById('profileModal');
    
    if (profileModalElement) {
        // Intentar con Bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            try {
                const modal = bootstrap.Modal.getOrCreateInstance(profileModalElement);
                modal.show();
                console.log('Modal abierto con Bootstrap 5');
                return;
            } catch (error) {
                console.log('Error con Bootstrap 5:', error);
            }
        }
        
        // Método fallback usando atributos data
        profileModalElement.setAttribute('data-bs-toggle', 'modal');
        profileModalElement.setAttribute('data-bs-target', '#profileModal');
        
        // Disparar evento click en un botón invisible
        const triggerBtn = document.createElement('button');
        triggerBtn.setAttribute('data-bs-toggle', 'modal');
        triggerBtn.setAttribute('data-bs-target', '#profileModal');
        triggerBtn.style.display = 'none';
        document.body.appendChild(triggerBtn);
        triggerBtn.click();
        document.body.removeChild(triggerBtn);
        
        console.log('Modal abierto con método fallback');
        
        // Si el método anterior no funciona, intentar con jQuery
        if (typeof $ !== 'undefined') {
            try {
                $('#profileModal').modal('show');
                console.log('Modal abierto con jQuery');
            } catch (error) {
                console.log('Error con jQuery:', error);
            }
        }
    } else {
        // Solo mostrar error si estamos en el dashboard (página principal)
        if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
            console.error('Modal element not found');
        }
    }
}

// Función de búsqueda
function buscar(event) {
    if (event.key === 'Enter') {
        const query = document.getElementById('searchInput').value.trim();
        if (query) {
            // Buscar en expedientes primero
            window.location.href = `/expedientes/lista/?q=${encodeURIComponent(query)}`;
        }
    }
}

// Función para buscar documentos
function buscarDocumentos(query) {
    window.location.href = `/documentos/?q=${encodeURIComponent(query)}`;
}

// Función para marcar todas las notificaciones como leídas
function marcarTodasLeidas() {
    fetch('/marcar-notificaciones-leidas/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Ocultar el badge de notificaciones
            const badge = document.getElementById('notificationBadge');
            if (badge) {
                badge.style.display = 'none';
            }
            
            // Recargar la página para actualizar las notificaciones
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error al marcar notificaciones como leídas:', error);
    });
}

// Función para obtener el token CSRF
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

// Función para enviar mensaje
function enviarMensaje() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (message) {
        // Aquí implementarías el envío del mensaje
        console.log('Mensaje enviado:', message);
        messageInput.value = '';
        
        // Agregar mensaje a la interfaz
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = 'mb-2 p-2 bg-light rounded';
        messageElement.innerHTML = `
            <strong>${new Date().toLocaleTimeString()}:</strong> ${message}
        `;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Función para cargar notificaciones
function cargarNotificaciones() {
    const notificationsList = document.getElementById('notificationsList');
    const notificationBadge = document.getElementById('notificationBadge');
    
    if (!notificationsList || !notificationBadge) return;
    
    // Ejemplo de notificaciones
    const notificaciones = [
        { titulo: 'Nuevo expediente', descripcion: 'Se ha creado un nuevo expediente', tiempo: 'Hace 5 minutos' },
        { titulo: 'Documento subido', descripcion: 'Se ha subido un nuevo documento', tiempo: 'Hace 10 minutos' }
    ];
    
    if (notificaciones.length > 0) {
        notificationBadge.style.display = 'block';
        notificationBadge.textContent = notificaciones.length;
        
        notificationsList.innerHTML = notificaciones.map(notif => `
            <div class="d-flex align-items-start gap-3 p-2 border-bottom">
                <i class="bi bi-bell text-primary"></i>
                <div>
                    <h6 class="mb-1">${notif.titulo}</h6>
                    <p class="mb-1 text-muted">${notif.descripcion}</p>
                    <small class="text-muted">${notif.tiempo}</small>
                </div>
            </div>
        `).join('');
    }
}

// Función para cargar mensajes del chat
function cargarMensajesChat() {
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatMessages) return;
    
    // Ejemplo de mensajes
    const mensajes = [
        { usuario: 'Sistema', mensaje: 'Bienvenido al chat del sistema', tiempo: 'Hace 1 hora' },
        { usuario: 'Admin', mensaje: '¿Necesitas ayuda con algo?', tiempo: 'Hace 30 minutos' }
    ];
    
    chatMessages.innerHTML = mensajes.map(msg => `
        <div class="mb-2 p-2 bg-light rounded">
            <strong>${msg.usuario}</strong> <small class="text-muted">${msg.tiempo}</small><br>
            ${msg.mensaje}
        </div>
    `).join('');
}

// Función para cambiar tema
function cambiarTema() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Actualizar icono del botón
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        if (newTheme === 'dark') {
            themeToggle.className = 'bi bi-sun';
        } else {
            themeToggle.className = 'bi bi-moon';
        }
    }
}

// Función para cargar tema guardado
function cargarTemaGuardado() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    const themeToggle = document.querySelector('.theme-toggle i');
    if (themeToggle) {
        if (savedTheme === 'dark') {
            themeToggle.className = 'bi bi-sun';
        } else {
            themeToggle.className = 'bi bi-moon';
        }
    }
}

// Función para actualizar métricas en tiempo real
function actualizarMetricas() {
    // Aquí implementarías la actualización de métricas desde el backend
    console.log('Actualizando métricas...');
}

// Función para manejar búsqueda avanzada
function buscarAvanzado(query) {
    if (query.length < 3) return;
    
    // Implementar búsqueda avanzada
    fetch(`/buscar/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Resultados de búsqueda:', data);
            // Aquí procesarías los resultados
        })
        .catch(error => {
            console.error('Error en búsqueda:', error);
        });
}

// Función para exportar datos
function exportarDatos(formato) {
    // Implementar exportación según el formato (PDF, Excel, etc.)
    console.log(`Exportando datos en formato: ${formato}`);
}

// Función para generar reportes
function generarReporte(tipo) {
    // Implementar generación de reportes
    console.log(`Generando reporte de tipo: ${tipo}`);
}

// Event listeners adicionales
document.addEventListener('keydown', function(e) {
    // Atajo de teclado para búsqueda (Ctrl+K)
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Atajo para colapsar sidebar (Ctrl+B)
    if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        const collapseBtn = document.getElementById('collapseBtn');
        if (collapseBtn) {
            collapseBtn.click();
        }
    }
});

// Función para mostrar notificaciones toast
function mostrarNotificacion(mensaje, tipo = 'info') {
    // Crear elemento de notificación
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${mensaje}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
    
    // Agregar al contenedor de toasts
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Mostrar el toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remover después de que se oculte
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Función para actualizar contadores en tiempo real
function actualizarContadores() {
    // Actualizar contador de notificaciones
    const notificationBadge = document.getElementById('notificationBadge');
    if (notificationBadge) {
        // Aquí implementarías la lógica para obtener notificaciones no leídas
        const notificacionesNoLeidas = 0; // Obtener del backend
        if (notificacionesNoLeidas > 0) {
            notificationBadge.style.display = 'block';
            notificationBadge.textContent = notificacionesNoLeidas;
        } else {
            notificationBadge.style.display = 'none';
        }
    }
}

// Inicializar funcionalidades adicionales
document.addEventListener('DOMContentLoaded', function() {
    // Actualizar contadores cada 30 segundos
    setInterval(actualizarContadores, 30000);
    
    // Actualizar métricas cada minuto
    setInterval(actualizarMetricas, 60000);
    
    // Configurar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

