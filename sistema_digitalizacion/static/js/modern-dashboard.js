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
        document.addEventListener('DOMContentLoaded', () => {
            this.setupDropdowns();
            this.setupTooltips();
            this.setupModals();
        });
    }

    initializeAnimations() {
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

        const animatedElements = document.querySelectorAll('.stat-card, .action-card, .expediente-card, .info-card');
        animatedElements.forEach(el => observer.observe(el));
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

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
            const icon = themeToggle.querySelector('i');
            if (icon) icon.className = 'bi bi-sun';
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            const icon = themeToggle.querySelector('i');
            if (icon) icon.className = 'bi bi-moon';
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

            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });

        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('collapsed');
            const icon = sidebarToggle.querySelector('i');
            if (icon) icon.className = 'bi bi-chevron-right';
        }
    }

    setupNotifications() {
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationPanel = document.getElementById('notificationPanel');
        const closeNotifications = document.getElementById('closeNotifications');

        if (!notificationBtn || !notificationPanel) return;

        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationPanel.classList.toggle('show');
        });

        if (closeNotifications) {
            closeNotifications.addEventListener('click', () => {
                notificationPanel.classList.remove('show');
            });
        }

        document.addEventListener('click', (e) => {
            if (!notificationBtn.contains(e.target) && !notificationPanel.contains(e.target)) {
                notificationPanel.classList.remove('show');
            }
        });
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
            } else {
                card.style.display = 'none';
            }
        });
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

            document.addEventListener('click', (e) => {
                if (!userProfile.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('show');
                }
            });
        }
    }

    setupTooltips() {
        // Tooltips placeholder
    }

    setupModals() {
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
        handleResize();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ModernDashboard();
});

window.ModernDashboard = ModernDashboard;

