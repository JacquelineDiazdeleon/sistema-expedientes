/**
 * Sistema de Digitalización - JavaScript Moderno
 * Funcionalidades avanzadas para el dashboard
 */

class ModernDashboard {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.setupThemeToggle();
        this.setupSidebar();
        this.setupNotifications();
        this.setupSearch();
        this.setupCounters();
        this.setupResponsive();
    }

    setupEventListeners() {
        // Event listeners para elementos interactivos
        document.addEventListener('DOMContentLoaded', () => {
            this.setupDropdowns();
            this.setupTooltips();
            this.setupModals();
        });
    }

    initializeAnimations() {
        // Animaciones de entrada escalonadas
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    entry.target.style.animationDelay = `${index * 0.1}s`;
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observar elementos animables
        const animatedElements = document.querySelectorAll('.stat-card, .action-card, .expediente-card, .info-card');
        animatedElements.forEach(el => observer.observe(el));
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        // Cargar tema guardado
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.applyTheme(savedTheme);

        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.applyTheme(newTheme);
        });
    }

    applyTheme(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            themeToggle.querySelector('i').className = 'bi bi-sun';
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            themeToggle.querySelector('i').className = 'bi bi-moon';
        }
    }

    setupSidebar() {
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');

        if (!sidebarToggle || !sidebar || !mainContent) return;

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('collapsed');
            
            const icon = sidebarToggle.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.className = 'bi bi-chevron-right';
            } else {
                icon.className = 'bi bi-chevron-left';
            }

            // Guardar estado del sidebar
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });

        // Restaurar estado del sidebar
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('collapsed');
            sidebarToggle.querySelector('i').className = 'bi bi-chevron-right';
        }
    }

    setupNotifications() {
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationPanel = document.getElementById('notificationPanel');
        const closeNotifications = document.getElementById('closeNotifications');

        if (!notificationBtn || !notificationPanel) return;

        // Toggle del panel de notificaciones
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationPanel.classList.toggle('show');
        });

        // Cerrar notificaciones
        if (closeNotifications) {
            closeNotifications.addEventListener('click', () => {
                notificationPanel.classList.remove('show');
            });
        }

        // Cerrar al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!notificationBtn.contains(e.target) && !notificationPanel.contains(e.target)) {
                notificationPanel.classList.remove('show');
            }
        });

        // Simular carga de notificaciones
        this.loadNotifications();
    }

    async loadNotifications() {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;

        try {
            // Simular API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Actualizar contador de notificaciones
            const notificationBadge = document.getElementById('notificationBadge');
            if (notificationBadge) {
                notificationBadge.textContent = '3';
                notificationBadge.style.display = 'block';
            }

            // Mostrar notificaciones de ejemplo
            notificationList.innerHTML = `
                <div class="notification-item unread">
                    <div class="notification-content">
                        <div class="notification-icon">
                            <i class="bi bi-file-earmark-check"></i>
                        </div>
                        <div class="notification-text">
                            <div class="notification-title">Expediente Completado</div>
                            <div class="notification-message">El expediente EXP-2025-0001 ha sido verificado exitosamente.</div>
                            <div class="notification-time">Hace 5 minutos</div>
                        </div>
                    </div>
                </div>
                <div class="notification-item">
                    <div class="notification-content">
                        <div class="notification-icon">
                            <i class="bi bi-person-plus"></i>
                        </div>
                        <div class="notification-text">
                            <div class="notification-title">Nuevo Usuario</div>
                            <div class="notification-message">Se ha registrado un nuevo usuario en el sistema.</div>
                            <div class="notification-time">Hace 1 hora</div>
                        </div>
                    </div>
                </div>
                <div class="notification-item">
                    <div class="notification-content">
                        <div class="notification-icon">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <div class="notification-text">
                            <div class="notification-title">Documento Pendiente</div>
                            <div class="notification-message">El expediente EXP-2025-0002 requiere atención.</div>
                            <div class="notification-time">Hace 2 horas</div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error cargando notificaciones:', error);
        }
    }

    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.toLowerCase();
            
            searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });

        // Búsqueda con Enter
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch(e.target.value.toLowerCase());
            }
        });
    }

    performSearch(query) {
        const expedientesCards = document.querySelectorAll('.expediente-card');
        
        expedientesCards.forEach(card => {
            const titulo = card.dataset.titulo || '';
            const fuente = card.dataset.fuente || '';
            const usuario = card.dataset.usuario || '';
            
            const matches = titulo.includes(query) || 
                           fuente.includes(query) || 
                           usuario.includes(query);
            
            if (matches) {
                card.style.display = 'block';
                card.style.animation = 'fadeIn 0.3s ease-in';
            } else {
                card.style.display = 'none';
            }
        });

        // Mostrar mensaje si no hay resultados
        this.showSearchResults(query, expedientesCards);
    }

    showSearchResults(query, cards) {
        const expedientesSection = document.querySelector('.expedientes-section');
        if (!expedientesSection) return;

        let existingMessage = expedientesSection.querySelector('.search-no-results');
        if (existingMessage) {
            existingMessage.remove();
        }

        const visibleCards = Array.from(cards).filter(card => 
            card.style.display !== 'none'
        );

        if (query && visibleCards.length === 0) {
            const noResultsMessage = document.createElement('div');
            noResultsMessage.className = 'search-no-results text-center py-4';
            noResultsMessage.innerHTML = `
                <i class="bi bi-search" style="font-size: 3rem; color: var(--secondary-400);"></i>
                <h4 class="mt-3" style="color: var(--secondary-600);">No se encontraron resultados</h4>
                <p style="color: var(--secondary-500);">Intenta con otros términos de búsqueda</p>
            `;
            expedientesSection.appendChild(noResultsMessage);
        }
    }

    setupCounters() {
        const statNumbers = document.querySelectorAll('.stat-number');
        
        statNumbers.forEach(stat => {
            const finalValue = parseInt(stat.textContent);
            if (!isNaN(finalValue)) {
                this.animateCounter(stat, 0, finalValue, 2000);
            }
        });
    }

    animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const difference = end - start;
        
        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Función de easing para animación suave
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            
            const current = Math.floor(start + (difference * easeOutQuart));
            element.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };
        
        requestAnimationFrame(updateCounter);
    }

    setupDropdowns() {
        const userProfile = document.getElementById('userProfile');
        const userDropdown = document.getElementById('userDropdown');

        if (userProfile && userDropdown) {
            userProfile.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdown.classList.toggle('show');
            });

            // Cerrar al hacer clic fuera
            document.addEventListener('click', (e) => {
                if (!userProfile.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('show');
                }
            });
        }
    }

    setupTooltips() {
        // Tooltips personalizados para elementos importantes
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
        
        setTimeout(() => tooltip.classList.add('show'), 100);
    }

    hideTooltip() {
        const tooltip = document.querySelector('.custom-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    setupModals() {
        // Configuración de modales Bootstrap si están disponibles
        if (typeof bootstrap !== 'undefined') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                new bootstrap.Modal(modal);
            });
        }
    }

    setupResponsive() {
        const handleResize = () => {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('mainContent');
            
            if (window.innerWidth <= 1024) {
                sidebar?.classList.add('collapsed');
                mainContent?.classList.add('collapsed');
            }
        };

        window.addEventListener('resize', handleResize);
        handleResize(); // Ejecutar al cargar
    }

    // Métodos de utilidad
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="bi bi-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Método para actualizar estadísticas en tiempo real
    updateStats(newStats) {
        Object.keys(newStats).forEach(key => {
            const statElement = document.querySelector(`[data-stat="${key}"]`);
            if (statElement) {
                const currentValue = parseInt(statElement.textContent);
                const newValue = newStats[key];
                
                if (currentValue !== newValue) {
                    this.animateCounter(statElement, currentValue, newValue, 1000);
                }
            }
        });
    }
}

// Inicializar el dashboard cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ModernDashboard();
});

// Exportar para uso global si es necesario
window.ModernDashboard = ModernDashboard;

// Estilos CSS adicionales para funcionalidades JavaScript
const additionalStyles = `
    .custom-tooltip {
        position: fixed;
        background: var(--secondary-900);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.875rem;
        z-index: 10000;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.2s ease;
        pointer-events: none;
        box-shadow: var(--shadow-lg);
    }

    .custom-tooltip.show {
        opacity: 1;
        transform: translateY(0);
    }

    .custom-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent;
        border-top-color: var(--secondary-900);
    }

    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-radius: var(--radius-lg);
        padding: 16px 20px;
        box-shadow: var(--shadow-xl);
        border: 1px solid var(--secondary-200);
        z-index: 10000;
        transform: translateX(400px);
        transition: transform 0.3s ease;
    }

    .toast.show {
        transform: translateX(0);
    }

    .toast-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .toast-success {
        border-left: 4px solid var(--success-500);
    }

    .toast-error {
        border-left: 4px solid var(--danger-500);
    }

    .toast-warning {
        border-left: 4px solid var(--warning-500);
    }

    .toast-info {
        border-left: 4px solid var(--info-500);
    }

    .search-no-results {
        background: var(--secondary-50);
        border-radius: var(--radius-lg);
        margin: var(--space-lg) 0;
    }

    .notification-item {
        padding: 16px 20px;
        border-bottom: 1px solid var(--secondary-200);
        transition: background-color 0.2s ease;
        cursor: pointer;
    }

    .notification-item:hover {
        background: var(--secondary-50);
    }

    .notification-item.unread {
        background: rgba(14, 165, 233, 0.05);
        border-left: 3px solid var(--primary-500);
    }

    .notification-item:last-child {
        border-bottom: none;
    }

    .fade-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
`;

// Inyectar estilos adicionales
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);
