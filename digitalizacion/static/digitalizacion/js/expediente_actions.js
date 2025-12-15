// Función para guardar el expediente
async function guardarExpediente() {
    const btn = document.getElementById('btn-guardar-expediente');
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Obtener el token CSRF
        const csrftoken = getCookie('csrftoken');
        
        // Enviar solicitud para guardar el expediente
        const response = await fetch(`/expedientes/${expedienteId}/guardar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Error al guardar el expediente');
        }
        
        // Mostrar mensaje de éxito
        showAlert('✅ Expediente guardado correctamente', 'success');
        
        // Redirigir a la lista de expedientes después de 1 segundo
        setTimeout(() => {
            window.location.href = '/expedientes/';
        }, 1000);
        
    } catch (error) {
        console.error('Error al guardar el expediente:', error);
        showAlert(`❌ ${error.message || 'Error al guardar el expediente. Intente nuevamente.'}`, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Función para rechazar el expediente
async function rechazarExpediente() {
    const btn = document.getElementById('btn-rechazar-expediente');
    if (!btn) return;
    
    // Confirmar acción
    if (!confirm('¿Está seguro de que desea rechazar este expediente? Esta acción cambiará el estado del expediente a "rechazado".')) {
        return;
    }
    
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Rechazando...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Obtener el token CSRF
        const csrftoken = getCookie('csrftoken');
        
        // Enviar solicitud para rechazar el expediente
        const formData = new FormData();
        formData.append('razon_rechazo', 'Expediente rechazado desde el botón de acción');
        
        const response = await fetch(`/expedientes/${expedienteId}/rechazar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok || !data.success) {
            throw new Error(data.message || data.error || 'Error al rechazar el expediente');
        }
        
        // Mostrar mensaje de éxito
        showAlert('✅ Expediente rechazado correctamente', 'success');
        
        // Recargar la página para reflejar los cambios
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        console.error('Error al rechazar el expediente:', error);
        showAlert(`❌ ${error.message || 'Error al rechazar el expediente. Intente nuevamente.'}`, 'danger');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Función para descargar el expediente en formato ZIP
function descargarZip() {
    const btn = document.getElementById('btn-descargar-zip');
    const originalText = btn.innerHTML;
    
    try {
        // Mostrar indicador de carga
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Preparando descarga...';
        
        // Obtener el ID del expediente de la URL
        const urlParts = window.location.pathname.split('/');
        const expedienteId = urlParts[urlParts.indexOf('expedientes') + 1];
        
        // Redirigir directamente a la URL de descarga (la vista acepta GET)
        window.location.href = `/expedientes/${expedienteId}/descargar-completo/`;
        
        // Restaurar el botón después de un momento
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }, 3000);
        
    } catch (error) {
        console.error('Error al preparar la descarga:', error);
        showAlert('❌ Error al preparar la descarga. Intente nuevamente.', 'danger');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Función auxiliar para obtener el token CSRF de las cookies
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

// Función para mostrar notificaciones (compatibilidad con código existente)
function showAlert(message, type = 'info') {
    // Usar la función centralizada de notificaciones si está disponible
    if (window.mostrarNotificacion) {
        window.mostrarNotificacion(message, type);
    } else {
        // Implementación de respaldo en caso de que la función centralizada no esté disponible
        console.warn('La función centralizada de notificaciones no está disponible');
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.style.zIndex = '1100';
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Eliminar la alerta después de 5 segundos
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
}
