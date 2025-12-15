// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme system
    initializeThemeSystem();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload handling
    initializeFileUploads();
    
    // Search functionality
    initializeSearch();
    
    // Auto-save for forms
    initializeAutoSave();
    
    // Progress tracking
    updateProgressBars();
    
    // Forzar texto negro en badges después de cargar
    setTimeout(forceBlackTextInBadges, 500);
    
    // Inicializar observer para cambios en el DOM
    observeAndFixBadges();
    
    console.log('🎨 Dashboard JS completamente cargado');
});

// File upload functionality
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('.file-upload-zone');
    
    fileInputs.forEach(zone => {
        // Drag and drop handlers
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        zone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });
        
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files, this);
            }
        });
    });
}

// Handle file upload
function handleFileUpload(files, zone) {
    const fileList = zone.querySelector('.file-list');
    
    Array.from(files).forEach(file => {
        // Validate file type and size
        if (!validateFile(file)) {
            return;
        }
        
        // Create file item
        const fileItem = createFileItem(file);
        fileList.appendChild(fileItem);
        
        // Simulate upload progress (replace with actual upload)
        simulateUploadProgress(fileItem);
    });
}

// Validate file
function validateFile(file) {
    const allowedTypes = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (!allowedTypes.includes(file.type)) {
        showAlert('Tipo de archivo no permitido: ' + file.name, 'warning');
        return false;
    }
    
    if (file.size > maxSize) {
        showAlert('Archivo muy grande: ' + file.name + ' (máximo 50MB)', 'warning');
        return false;
    }
    
    return true;
}

// Create file item element
function createFileItem(file) {
    const div = document.createElement('div');
    div.className = 'file-item d-flex justify-content-between align-items-center p-3 mb-2 bg-zinc-800 border border-zinc-700 rounded';
    
    div.innerHTML = `
        <div>
            <div class="fw-medium text-zinc-100">${file.name}</div>
            <small class="text-zinc-400">${formatFileSize(file.size)} • ${new Date().toLocaleString()}</small>
            <div class="progress mt-2" style="height: 4px;">
                <div class="progress-bar bg-emerald-600" role="progressbar" style="width: 0%"></div>
            </div>
        </div>
        <div class="d-flex gap-2">
            <button type="button" class="btn btn-sm btn-outline-light" onclick="downloadFile(this)">
                <i class="bi bi-download"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(this)">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    return div;
}

// Simulate upload progress
function simulateUploadProgress(fileItem) {
    const progressBar = fileItem.querySelector('.progress-bar');
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            showAlert('Archivo subido exitosamente', 'success');
        }
        progressBar.style.width = progress + '%';
    }, 200);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Remove file
function removeFile(button) {
    const fileItem = button.closest('.file-item');
    fileItem.remove();
    showAlert('Archivo eliminado', 'info');
}

// Download file
function downloadFile(button) {
    const fileItem = button.closest('.file-item');
    const fileName = fileItem.querySelector('.fw-medium').textContent;
    showAlert('Descargando: ' + fileName, 'info');
    // Implement actual download logic here
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('[data-search-target]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const target = document.querySelector(this.dataset.searchTarget);
            const items = target.querySelectorAll('[data-searchable]');
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                const matches = text.includes(query);
                item.style.display = matches ? 'block' : 'none';
            });
        });
    });
}

// Auto-save functionality
function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                autoSaveForm(form);
            });
        });
    });
}

// Auto-save form
function autoSaveForm(form) {
    const formData = new FormData(form);
    
    // Add auto-save indicator
    showAutoSaveIndicator();
    
    // Simulate auto-save (replace with actual implementation)
    setTimeout(() => {
        hideAutoSaveIndicator();
        console.log('Form auto-saved');
    }, 1000);
}

// Show auto-save indicator
function showAutoSaveIndicator() {
    let indicator = document.getElementById('auto-save-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'auto-save-indicator';
        indicator.className = 'position-fixed top-0 end-0 m-3 p-2 bg-zinc-800 border border-zinc-700 rounded text-zinc-300';
        indicator.innerHTML = '<i class="bi bi-cloud-arrow-up me-2"></i>Guardando...';
        indicator.style.zIndex = '9999';
        document.body.appendChild(indicator);
    }
    
    indicator.style.display = 'block';
}

// Hide auto-save indicator
function hideAutoSaveIndicator() {
    const indicator = document.getElementById('auto-save-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// Update progress bars
function updateProgressBars() {
    const progressBars = document.querySelectorAll('[data-progress]');
    
    progressBars.forEach(bar => {
        const progress = parseInt(bar.dataset.progress);
        const progressBar = bar.querySelector('.progress-bar');
        
        if (progressBar) {
            // Animate progress bar
            setTimeout(() => {
                progressBar.style.width = progress + '%';
            }, 100);
        }
    });
}

// Show alert
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${getAlertIcon(type)}
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Create alert container
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Get alert icon
function getAlertIcon(type) {
    const icons = {
        success: '<i class="bi bi-check-circle me-2"></i>',
        danger: '<i class="bi bi-exclamation-triangle me-2"></i>',
        warning: '<i class="bi bi-exclamation-circle me-2"></i>',
        info: '<i class="bi bi-info-circle me-2"></i>'
    };
    
    return icons[type] || icons.info;
}

// Stage management
function toggleStage(stageId) {
    const stage = document.getElementById(stageId);
    const isExpanded = stage.classList.contains('show');
    
    if (isExpanded) {
        stage.classList.remove('show');
    } else {
        stage.classList.add('show');
    }
}

// Mark stage as complete
function markStageComplete(stageId) {
    const stage = document.getElementById(stageId);
    const badge = stage.querySelector('.stage-badge');
    
    if (confirm('¿Marcar esta etapa como completada?')) {
        stage.classList.add('stage-completed');
        badge.textContent = 'Completado';
        badge.className = 'badge bg-success';
        
        showAlert('Etapa marcada como completada', 'success');
        
        // Update overall progress
        updateOverallProgress();
    }
}

// Update overall progress
function updateOverallProgress() {
    const stages = document.querySelectorAll('.stage-item');
    const completedStages = document.querySelectorAll('.stage-completed');
    
    const progress = Math.round((completedStages.length / stages.length) * 100);
    
    const progressBar = document.querySelector('.overall-progress .progress-bar');
    const progressText = document.querySelector('.overall-progress-text');
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
    
    if (progressText) {
        progressText.textContent = progress + '%';
    }
}

// ===== SISTEMA DE TEMAS MODERNO =====
function initializeThemeSystem() {
    console.log('🎨 Inicializando sistema de temas...');
    
    // Get saved theme from localStorage or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light';
    console.log('💾 Tema guardado:', savedTheme);
    
    // Set initial theme immediately
    setTheme(savedTheme, false);
    
    // Add event listener to theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        console.log('🎛️ Botón toggle encontrado, agregando eventos...');
        
        // Agregar efectos visuales al botón
        themeToggle.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        
        themeToggle.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
        
        // Evento principal de cambio de tema
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Click en toggle detectado');
            
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            console.log(`🔄 Cambiando de ${currentTheme} a ${newTheme}`);
            
            // Agregar animación de click
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            setTheme(newTheme, true);
        });
        
        // Soporte para tecla Enter y Espacio
        themeToggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    } else {
        console.error('❌ Botón toggle no encontrado! ID: themeToggle');
    }
}

function setTheme(theme, showNotification = false) {
    console.log(`🎨 Aplicando tema: ${theme}`);
    
    // Set theme attribute on document
    document.documentElement.setAttribute('data-theme', theme);
    
    // Save theme to localStorage
    localStorage.setItem('theme', theme);
    
    // Update toggle button state
    updateThemeToggleButton(theme);
    
    // Add transition class temporarily
    document.body.classList.add('theme-transitioning');
    setTimeout(() => {
        document.body.classList.remove('theme-transitioning');
    }, 300);
    
    // Show notification only if requested
    if (showNotification) {
        const themeNames = {
            'light': '☀️ Tema Claro',
            'dark': '🌙 Tema Oscuro'
        };
        
        showAlert(`${themeNames[theme]} activado`, 'info');
    }
    
    // Forzar corrección de badges después del cambio de tema
    setTimeout(forceBlackTextInBadges, 100);
    
    console.log(`✅ Tema ${theme} aplicado correctamente`);
}

function updateThemeToggleButton(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        // Update ARIA attributes for accessibility
        const newLabel = theme === 'light' ? 'Cambiar a tema oscuro' : 'Cambiar a tema claro';
        themeToggle.setAttribute('aria-label', newLabel);
        themeToggle.setAttribute('title', newLabel);
        
        // Update visual state
        themeToggle.classList.remove('theme-light', 'theme-dark');
        themeToggle.classList.add(`theme-${theme}`);
        
        console.log(`🎛️ Botón actualizado para tema: ${theme}`);
    }
}

function getSystemTheme() {
    // Check if user prefers dark mode
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

// Listen for system theme changes
if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Usar el método moderno addEventListener si está disponible
    if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', function(e) {
            // Only auto-switch if user hasn't manually set a theme
            if (!localStorage.getItem('theme')) {
                console.log('🔄 Sistema cambió tema, actualizando...');
                setTheme(e.matches ? 'dark' : 'light', true);
            }
        });
    } else {
        // Fallback para navegadores más antiguos
        mediaQuery.addListener(function(e) {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light', true);
            }
        });
    }
}

// Auto-detect system theme if no preference is saved
function initializeSystemTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (!savedTheme) {
        const systemTheme = getSystemTheme();
        console.log(`🔍 Detectando tema del sistema: ${systemTheme}`);
        setTheme(systemTheme, false);
    }
}

// Función para forzar texto negro en badges (tema claro)
function forceBlackTextInBadges() {
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    
    if (!isDarkTheme) {
        // Buscar todos los badges y forzar texto negro
        const badges = document.querySelectorAll('.badge, [class*="bg-blue"], [class*="bg-orange"], [class*="bg-yellow"], [class*="bg-emerald"]');
        
        badges.forEach(badge => {
            badge.style.setProperty('color', '#000000', 'important');
            badge.style.setProperty('background-color', 'rgba(59, 130, 246, 0.15)', 'important');
            badge.style.setProperty('border', '1px solid #3b82f6', 'important');
            
            // También forzar elementos internos
            const innerElements = badge.querySelectorAll('*');
            innerElements.forEach(el => {
                el.style.setProperty('color', '#000000', 'important');
            });
        });
        
        console.log('🔧 Forzado texto negro en', badges.length, 'badges');
    }
}

// Función para observar cambios en el DOM y aplicar correcciones
function observeAndFixBadges() {
    // Crear un observer para detectar cambios en el DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Si se agregaron nuevos nodos, revisar badges
                setTimeout(forceBlackTextInBadges, 10);
            }
        });
    });
    
    // Observar cambios en todo el documento
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('👁️ Observer de badges inicializado');
}

// ===== SISTEMA DE NOTIFICACIONES GLOBALES =====
let notificationInterval = null;
let lastNotificationCount = 0;

function initializeGlobalNotifications() {
    console.log('🔔 Inicializando notificaciones globales...');
    
    // Cargar notificaciones iniciales
    loadNotifications();
    
    // Configurar actualización automática cada 30 segundos
    if (notificationInterval) {
        clearInterval(notificationInterval);
    }
    notificationInterval = setInterval(loadNotifications, 30000);
    
    // Cargar notificaciones cuando el usuario vuelve a la página
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('🔔 Usuario volvió a la página, cargando notificaciones...');
            loadNotifications();
        }
    });
    
    console.log('✅ Sistema de notificaciones globales iniciado');
}

function loadNotifications() {
    // Solo cargar si el usuario está autenticado
    const notificationDropdown = document.getElementById('dropdownNotificaciones');
    if (!notificationDropdown) {
        console.log('🔔 Usuario no autenticado, saltando carga de notificaciones');
        return;
    }
    
    // Agregar timestamp para evitar caché
    const timestamp = new Date().getTime();
    
    fetch(`/expedientes/api/notificaciones/?t=${timestamp}`, {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`🔔 Notificaciones cargadas: ${data.notificaciones.length} items, ${data.total_no_leidas} no leídas`);
            
            // Detectar nuevas notificaciones para mostrar alerta
            if (data.total_no_leidas > lastNotificationCount && lastNotificationCount > 0) {
                console.log('🔔 ¡Nuevas notificaciones detectadas!');
                showNotificationAlert(data.total_no_leidas - lastNotificationCount);
            }
            
            lastNotificationCount = data.total_no_leidas;
            updateNotificationUI(data.notificaciones, data.total_no_leidas);
        })
        .catch(error => {
            console.error('❌ Error cargando notificaciones:', error);
            
            // Mostrar error en la UI si es necesario
            const lista = document.getElementById('lista-notificaciones');
            if (lista) {
                lista.innerHTML = `
                    <li class="px-3 py-2 text-center">
                        <div class="text-danger">
                            <i class="bi bi-exclamation-triangle mb-2"></i>
                            <div>Error al cargar notificaciones</div>
                            <small>Reintentando en 30 segundos...</small>
                        </div>
                    </li>
                `;
            }
        });
}

function showNotificationAlert(newCount) {
    // Mostrar una alerta sutil de nuevas notificaciones
    const alert = document.createElement('div');
    alert.className = 'position-fixed top-0 end-0 p-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        <div class="toast show bg-info text-white" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-bell-fill me-2"></i>
                    ${newCount > 1 ? `${newCount} nuevas notificaciones` : 'Nueva notificación'}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 4000);
}

function updateNotificationUI(notificaciones, totalNoLeidas) {
    const contador = document.getElementById('contador-notificaciones');
    const lista = document.getElementById('lista-notificaciones');
    
    if (!contador || !lista) {
        console.log('🔔 Elementos de notificación no encontrados, usuario probablemente no autenticado');
        return;
    }
    
    console.log(`🔔 Actualizando UI: ${notificaciones.length} notificaciones, ${totalNoLeidas} no leídas`);
    
    // Actualizar contador
    if (totalNoLeidas > 0) {
        contador.textContent = totalNoLeidas > 99 ? '99+' : totalNoLeidas;
        contador.style.display = 'block';
        contador.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
        
        // Agregar animación sutil cuando hay nuevas notificaciones
        contador.style.animation = 'pulse 2s infinite';
    } else {
        contador.style.display = 'none';
        contador.style.animation = 'none';
    }
    
    // Limpiar lista actual
    lista.innerHTML = '';
    
    if (notificaciones.length === 0) {
        lista.innerHTML = `
            <li class="px-3 py-2 text-center">
                <div class="text-muted">
                    <i class="bi bi-bell-slash fs-4 mb-2"></i>
                    <div>No hay notificaciones nuevas</div>
                </div>
            </li>
        `;
        return;
    }
    
    // Agregar notificaciones
    notificaciones.forEach(notif => {
        const li = document.createElement('li');
        li.innerHTML = `
            <a class="dropdown-item ${!notif.leida ? 'fw-bold bg-info bg-opacity-10 border-start border-info border-3' : ''}" 
               href="#" 
               onclick="markNotificationAsRead(${notif.id}, '${notif.enlace || '#'}')"
               style="border-radius: 0.375rem; margin: 0.25rem;">
                <div class="d-flex align-items-start p-2">
                    <div class="flex-shrink-0 me-3">
                        ${getNotificationIcon(notif.tipo)}
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-medium text-dark">${notif.titulo}</div>
                        <div class="text-muted small mt-1">${notif.mensaje}</div>
                        <div class="d-flex justify-content-between align-items-center mt-2">
                            <small class="text-info">
                                <i class="bi bi-folder me-1"></i>${notif.expediente}
                            </small>
                            <small class="text-muted">
                                ${formatNotificationDate(notif.fecha_creacion)}
                            </small>
                        </div>
                    </div>
                    ${!notif.leida ? '<div class="flex-shrink-0 ms-2"><span class="badge bg-info rounded-pill">●</span></div>' : ''}
                </div>
            </a>
        `;
        lista.appendChild(li);
    });
    
    // Agregar separador si hay más notificaciones
    if (totalNoLeidas > notificaciones.length) {
        const separator = document.createElement('li');
        separator.innerHTML = `
            <div class="dropdown-divider"></div>
            <div class="text-center p-2">
                <small class="text-muted">
                    Mostrando ${notificaciones.length} de ${totalNoLeidas} notificaciones
                </small>
            </div>
        `;
        lista.appendChild(separator);
    }
}

function getNotificationIcon(tipo) {
    const icons = {
        'mencion': '<i class="bi bi-at text-primary"></i>',
        'comentario': '<i class="bi bi-chat-dots text-success"></i>',
        'etapa': '<i class="bi bi-arrow-right-circle text-warning"></i>',
        'documento': '<i class="bi bi-file-earmark text-info"></i>',
        'asignacion': '<i class="bi bi-person-check text-purple"></i>'
    };
    return icons[tipo] || '<i class="bi bi-bell text-muted"></i>';
}

function formatNotificationDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Ahora';
    if (diffInMinutes < 60) return `${diffInMinutes}m`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
    return `${Math.floor(diffInMinutes / 1440)}d`;
}

function markNotificationAsRead(notificationId, enlace) {
    fetch(`/expedientes/notificaciones/${notificationId}/leer/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok && enlace && enlace !== '#') {
            window.location.href = enlace;
        } else {
            // Recargar notificaciones para actualizar el estado
            loadNotifications();
        }
    })
    .catch(error => {
        console.error('Error marcando notificación como leída:', error);
    });
}

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Hacer funciones globalmente accesibles
window.markNotificationAsRead = markNotificationAsRead;
window.loadNotifications = loadNotifications;

// Inicializar notificaciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar después de un pequeño delay para asegurar que el DOM esté completamente cargado
    setTimeout(initializeGlobalNotifications, 500);
});

// Export functions for global access
window.DashboardJS = {
    showAlert,
    toggleStage,
    markStageComplete,
    removeFile,
    downloadFile,
    setTheme,
    initializeThemeSystem,
    forceBlackTextInBadges,
    observeAndFixBadges,
    loadNotifications,
    markNotificationAsRead
};

