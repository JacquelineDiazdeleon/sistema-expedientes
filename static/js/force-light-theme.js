// Forzar tema claro al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Establecer el tema claro en localStorage
    localStorage.setItem('theme', 'light');
    
    // Asegurar que el atributo data-theme esté configurado
    document.documentElement.setAttribute('data-theme', 'light');
    
    // Eliminar cualquier clase de tema oscuro del body
    document.body.classList.remove('dark-theme');
    
    // Forzar recálculo de estilos
    document.body.style.display = 'none';
    document.body.offsetHeight; // Trigger reflow
    document.body.style.display = '';
    
    console.log('Tema claro forzado');
});
