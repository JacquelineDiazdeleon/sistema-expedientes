// sidebar.js - Funcionalidad para el menú lateral
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.areas-sidebar');
    const toggleButton = document.getElementById('sidebarToggle');
    const closeButton = document.getElementById('closeSidebar');

    // Función para alternar el sidebar
    function toggleSidebar() {
        if (sidebar) {
            sidebar.classList.toggle('show');
            document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
        }
    }

    // Función para cerrar el sidebar
    function closeSidebar() {
        if (sidebar) {
            sidebar.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // Manejadores de eventos
    if (toggleButton) {
        toggleButton.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', function(e) {
            e.stopPropagation();
            closeSidebar();
        });
    }

    // Cerrar el menú al hacer clic fuera de él
    document.addEventListener('click', function(event) {
        if (sidebar && !sidebar.contains(event.target) && 
            toggleButton && !toggleButton.contains(event.target) &&
            sidebar.classList.contains('show')) {
            closeSidebar();
        }
    });

    // Cerrar el menú al hacer clic en un enlace en móviles
    if (window.innerWidth <= 992) {
        const links = document.querySelectorAll('.area-item a');
        links.forEach(link => {
            link.addEventListener('click', closeSidebar);
        });
    }

    // Hacer la función accesible globalmente
    window.toggleSidebar = toggleSidebar;
    window.closeSidebar = closeSidebar;
});
