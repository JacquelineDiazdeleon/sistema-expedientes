// Función para alternar entre temas
window.toggleTheme = function() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  
  // Guardar preferencia en localStorage
  localStorage.setItem('theme', newTheme);
  
  // Aplicar el nuevo tema
  html.setAttribute('data-theme', newTheme);
  
  // Actualizar el ícono
  updateThemeIcon(newTheme);
  
  // Actualizar el atributo para el lector de pantalla
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.setAttribute('aria-label', `Cambiar a tema ${currentTheme === 'dark' ? 'oscuro' : 'claro'}`);
    themeToggle.setAttribute('title', `Cambiar a tema ${currentTheme === 'dark' ? 'oscuro' : 'claro'}`);
  }
};

// Función para abrir el modal de detalles del expediente
function abrirModalExpediente(expedienteId) {
  // Mostrar estado de carga
  const modal = document.getElementById('expedienteModal');
  const modalBody = document.getElementById('modalBody');
  
  modalBody.innerHTML = `
    <div class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <p class="mt-2">Cargando información del expediente...</p>
    </div>
  `;
  
  // Mostrar el modal
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
  
  // Obtener los detalles del expediente
  fetch(`/expedientes/api/${expedienteId}/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Error al cargar el expediente');
      }
      return response.json();
    })
    .then(data => {
      // Actualizar el modal con los detalles del expediente
      modalBody.innerHTML = `
        <div class="expediente-detalle">
          <h4>${data.titulo || 'Sin título'}</h4>
          <p><strong>Número:</strong> ${data.numero_expediente || 'No disponible'}</p>
          <p><strong>Estado:</strong> ${data.estado_actual || 'No especificado'}</p>
          <p><strong>Fecha de creación:</strong> ${new Date(data.fecha_creacion).toLocaleDateString() || 'No disponible'}</p>
        </div>
      `;
    })
    .catch(error => {
      console.error('Error:', error);
      modalBody.innerHTML = `
        <div class="alert alert-danger">
          Error al cargar los detalles del expediente. Por favor, intente nuevamente.
          <p class="mt-2">${error.message}</p>
        </div>
      `;
    });
}

// Función para actualizar los íconos del tema
function updateThemeIcon(theme) {
  const sunIcon = document.querySelector('.sun-icon');
  const sunRays = document.querySelector('.sun-rays');
  const moonIcon = document.querySelector('.moon-icon');
  
  if (theme === 'light') {
    if (sunIcon) sunIcon.style.display = 'none';
    if (sunRays) sunRays.style.display = 'none';
    if (moonIcon) moonIcon.style.display = 'block';
  } else {
    if (sunIcon) sunIcon.style.display = 'block';
    if (sunRays) sunRays.style.display = 'block';
    if (moonIcon) moonIcon.style.display = 'none';
  }
}

// Inicializar el tema al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar tema
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
  
  // Configurar el botón de tema
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    themeToggle.setAttribute('aria-label', `Cambiar a tema ${currentTheme === 'dark' ? 'claro' : 'oscuro'}`);
    themeToggle.setAttribute('title', `Cambiar a tema ${currentTheme === 'dark' ? 'claro' : 'oscuro'}`);
  }
});
