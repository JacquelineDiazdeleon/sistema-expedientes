// Manejar el envío del formulario de número SIMA
document.addEventListener('DOMContentLoaded', function() {
    const formSima = document.getElementById('form-editar-sima');
    if (formSima) {
        formSima.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = formSima.getAttribute('data-url') || '';
            
            // Crear un objeto con los datos del formulario
            const data = {
                'numero_sima': document.getElementById('numero_sima').value.trim()
            };
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Actualizar el número SIMA mostrado
                    const displayElements = document.querySelectorAll('#numero-sima, [id^="numero-sima-"]');
                    displayElements.forEach(element => {
                        if (data.numero_sima) {
                            element.innerHTML = data.numero_sima;
                            element.classList.remove('text-muted', 'fst-italic');
                        } else {
                            element.innerHTML = '<span class="text-muted fst-italic">Sin asignar</span>';
                        }
                    });
                    
                    // Cerrar el modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editarSimaModal'));
                    if (modal) modal.hide();
                    
                    // Mostrar notificación de éxito
                    showToast('Éxito', 'Número SIMA actualizado correctamente', 'success');
                } else {
                    // Mostrar mensaje de error si lo hay
                    const errorMsg = data.error || 'Error al actualizar el número SIMA';
                    showToast('Error', errorMsg, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error', 'Error al procesar la solicitud', 'error');
            });
        });
    }
});

// Función para obtener el token CSRF de las cookies
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

// Función para mostrar notificaciones toast
function showToast(title, message, type = 'info') {
    try {
        // Validar parámetros
        if (!title || !message) {
            console.error('Título y mensaje son requeridos para mostrar el toast');
            return;
        }
        
        // Verificar si Bootstrap Toast está disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            // Crear el elemento del toast
            const toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                // Crear el contenedor si no existe
                const container = document.createElement('div');
                container.id = 'toast-container';
                container.style.position = 'fixed';
                container.style.top = '20px';
                container.style.right = '20px';
                container.style.zIndex = '1100';
                document.body.appendChild(container);
            }
            
            // Crear el toast
            const toastId = 'toast-' + Date.now();
            const toastElement = document.createElement('div');
            toastElement.id = toastId;
            toastElement.className = 'toast';
            toastElement.setAttribute('role', 'alert');
            toastElement.setAttribute('aria-live', 'assertive');
            toastElement.setAttribute('aria-atomic', 'true');
            
            // Determinar icono y color de borde según el tipo
            let iconClass = 'bi-info-circle';
            let borderColor = '#0d6efd';
            let iconColor = '#0d6efd';
            
            if (type === 'success') {
                iconClass = 'bi-check-circle-fill';
                borderColor = '#198754';
                iconColor = '#198754';
            } else if (type === 'error' || type === 'danger') {
                iconClass = 'bi-x-circle-fill';
                borderColor = '#dc3545';
                iconColor = '#dc3545';
            } else if (type === 'warning') {
                iconClass = 'bi-exclamation-triangle-fill';
                borderColor = '#ffc107';
                iconColor = '#ffc107';
            } else if (type === 'info') {
                iconClass = 'bi-info-circle-fill';
                borderColor = '#0dcaf0';
                iconColor = '#0dcaf0';
            }
            
            // Plantilla del toast moderna en blanco
            toastElement.style.cssText = `
                background: white;
                border: 1px solid ${borderColor};
                border-left: 4px solid ${borderColor};
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                min-width: 300px;
                max-width: 400px;
            `;
            
            toastElement.innerHTML = `
                <div class="d-flex align-items-center p-3">
                    <div class="flex-shrink-0 me-3">
                        <i class="bi ${iconClass}" style="font-size: 1.5rem; color: ${iconColor};"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-semibold mb-1" style="color: #212529; font-size: 0.95rem;">${title}</div>
                        <div class="text-muted" style="font-size: 0.875rem; line-height: 1.4;">${message}</div>
                    </div>
                    <button type="button" class="btn-close ms-2" data-bs-dismiss="toast" aria-label="Cerrar" style="opacity: 0.5;"></button>
                </div>
            `;
            
            // Agregar el toast al contenedor
            document.getElementById('toast-container').appendChild(toastElement);
            
            // Inicializar y mostrar el toast
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 5000
            });
            
            // Eliminar el toast del DOM cuando se cierre
            toastElement.addEventListener('hidden.bs.toast', function () {
                toastElement.remove();
            });
            
            toast.show();
        } else {
            // Usar alert como respaldo si no hay soporte para Toast
            alert(`${title}: ${message}`);
        }
        
    } catch (error) {
        console.error('Error al mostrar el mensaje:', error);
        // Último recurso: usar console.error
        console.error(`${title}: ${message}`);
    }
}
