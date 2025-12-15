// Sistema de Temas Claro/Oscuro para Sistema de Digitalización

class ThemeSystem {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.themeIcon = null;
        this.init();
    }

    init() {
        // Aplicar tema al cargar
        this.setTheme(this.currentTheme);
        
        // Buscar botón de tema si existe
        this.findThemeToggle();
        
        // Agregar listener para cambios de tema
        this.addThemeListener();
        
        console.log('Theme system initialized with theme:', this.currentTheme);
    }

    findThemeToggle() {
        // Buscar botón de tema por diferentes selectores
        this.themeIcon = document.getElementById('theme-icon') || 
                        document.querySelector('.theme-toggle i') ||
                        document.querySelector('.theme-toggle');
    }

    addThemeListener() {
        // Si hay un botón de tema, agregar listener
        if (this.themeIcon) {
            const themeToggle = this.themeIcon.closest('.theme-toggle') || this.themeIcon;
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    setTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
            this.updateThemeIcon('dark');
            localStorage.setItem('theme', 'dark');
            this.currentTheme = 'dark';
        } else {
            root.setAttribute('data-theme', 'light');
            this.updateThemeIcon('light');
            localStorage.setItem('theme', 'light');
            this.currentTheme = 'light';
        }

        // Disparar evento personalizado para notificar cambio de tema
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: theme } 
        }));
    }

    updateThemeIcon(theme) {
        if (this.themeIcon) {
            if (theme === 'dark') {
                this.themeIcon.className = 'bi bi-moon-fill';
                this.themeIcon.title = 'Cambiar a tema claro';
            } else {
                this.themeIcon.className = 'bi bi-sun-fill';
                this.themeIcon.title = 'Cambiar a tema oscuro';
            }
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    // Método para cambiar tema programáticamente
    changeTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.setTheme(theme);
        }
    }
}

// Función global para cambiar tema (para compatibilidad)
function toggleTheme() {
    if (window.themeSystem) {
        window.themeSystem.toggleTheme();
    }
}

function setTheme(theme) {
    if (window.themeSystem) {
        window.themeSystem.setTheme(theme);
    }
}

// Función para obtener tema actual
function getCurrentTheme() {
    if (window.themeSystem) {
        return window.themeSystem.getCurrentTheme();
    }
    return 'light';
}

// Inicializar sistema de temas cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Crear instancia global del sistema de temas
    window.themeSystem = new ThemeSystem();
    
    // Agregar listener para cambios de tema en otras páginas
    window.addEventListener('storage', function(e) {
        if (e.key === 'theme' && window.themeSystem) {
            window.themeSystem.setTheme(e.newValue);
        }
    });
});

// Función para aplicar tema a elementos específicos
function applyThemeToElement(element, theme) {
    if (!element) return;
    
    if (theme === 'dark') {
        element.classList.add('dark-theme');
        element.classList.remove('light-theme');
    } else {
        element.classList.add('light-theme');
        element.classList.remove('dark-theme');
    }
}

// Función para crear botón de tema personalizado
function createThemeToggle(container, options = {}) {
    const defaults = {
        size: '28px',
        showText: false,
        className: 'theme-toggle'
    };
    
    const config = { ...defaults, ...options };
    
    const toggleBtn = document.createElement('button');
    toggleBtn.className = config.className;
    toggleBtn.style.width = config.size;
    toggleBtn.style.height = config.size;
    toggleBtn.title = 'Cambiar tema';
    toggleBtn.onclick = toggleTheme;
    
    const icon = document.createElement('i');
    icon.id = 'theme-icon';
    icon.className = 'bi bi-sun-fill';
    
    toggleBtn.appendChild(icon);
    
    if (config.showText) {
        const text = document.createElement('span');
        text.textContent = 'Tema';
        text.style.marginLeft = '0.5rem';
        toggleBtn.appendChild(text);
        toggleBtn.style.width = 'auto';
        toggleBtn.style.padding = '0.375rem 0.75rem';
    }
    
    if (container) {
        container.appendChild(toggleBtn);
    }
    
    return toggleBtn;
}

// Función para detectar preferencia del sistema
function detectSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

// Función para sincronizar con preferencia del sistema
function syncWithSystemTheme() {
    const systemTheme = detectSystemTheme();
    const savedTheme = localStorage.getItem('theme');
    
    // Si no hay tema guardado, usar el del sistema
    if (!savedTheme) {
        if (window.themeSystem) {
            window.themeSystem.setTheme(systemTheme);
        }
    }
    
    // Escuchar cambios en la preferencia del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        const newSystemTheme = e.matches ? 'dark' : 'light';
        
        // Solo cambiar si no hay tema personalizado guardado
        if (!localStorage.getItem('theme')) {
            if (window.themeSystem) {
                window.themeSystem.setTheme(newSystemTheme);
            }
        }
    });
}

// Función para aplicar tema a elementos específicos por selector
function applyThemeToSelector(selector, theme) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        applyThemeToElement(element, theme);
    });
}

// Función para crear un indicador de tema
function createThemeIndicator(container) {
    const indicator = document.createElement('div');
    indicator.className = 'theme-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 0.75rem;
        color: var(--text-primary);
        z-index: 9999;
        box-shadow: var(--shadow);
    `;
    
    const updateIndicator = () => {
        const theme = getCurrentTheme();
        indicator.textContent = `Tema: ${theme === 'dark' ? 'Oscuro' : 'Claro'}`;
        indicator.style.background = getComputedStyle(document.documentElement)
            .getPropertyValue('--bg-card');
        indicator.style.color = getComputedStyle(document.documentElement)
            .getPropertyValue('--text-primary');
        indicator.style.borderColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--border');
    };
    
    updateIndicator();
    
    // Actualizar cuando cambie el tema
    window.addEventListener('themeChanged', updateIndicator);
    
    if (container) {
        container.appendChild(indicator);
    }
    
    return indicator;
}

// Exportar funciones para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ThemeSystem,
        toggleTheme,
        setTheme,
        getCurrentTheme,
        createThemeToggle,
        detectSystemTheme,
        syncWithSystemTheme,
        applyThemeToElement,
        applyThemeToSelector,
        createThemeIndicator
    };
}
