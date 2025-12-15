import re

def update_upload_function():
    # Ruta al archivo
    file_path = 'templates/digitalizacion/expedientes/detalle_expediente.html'
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Definir el patrón para encontrar la función subirDocumento
    pattern = r'(// Función para subir un documento\n\s+async function subirDocumento\(event\) \{[\s\S]*?\n\s+\})'
    
    # Nueva implementación de la función
    new_function = """// Función para subir un documento
        async function subirDocumento(event) {
            event.preventDefault();
            
            const form = document.getElementById('formSubirDocumento');
            const uploadAlert = document.getElementById('uploadAlert');
            const uploadSpinner = document.getElementById('uploadSpinner');
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // Validar archivo
            const fileInput = document.getElementById('documento');
            if (fileInput.files.length === 0) {
                showAlert('Por favor seleccione un archivo', 'danger');
                return;
            }

            // Validar tamaño máximo del archivo (10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (fileInput.files[0].size > maxSize) {
                showAlert('El archivo es demasiado grande. El tamaño máximo permitido es 10MB.', 'danger');
                return;
            }

            // Validar nombre del documento
            const nombreDocumento = document.getElementById('nombreDocumento').value.trim();
            if (!nombreDocumento) {
                showAlert('Por favor ingrese un nombre para el documento', 'danger');
                return;
            }

            // Mostrar spinner y deshabilitar botón
            uploadSpinner.classList.remove('d-none');
            submitBtn.disabled = true;
            uploadAlert.classList.add('d-none');

            try {
                // Obtener token CSRF
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
                const csrftoken = getCookie('csrftoken');

                // Obtener la etapa del área actual
                const areaElement = document.querySelector(`[data-area-id="${areaActual}"]`);
                const etapa = areaElement ? areaElement.dataset.etapa : '';
                
                if (!etapa) {
                    throw new Error('No se pudo determinar la etapa del área');
                }
                
                // Construir la URL correcta con la etapa
                const url = `/expedientes/{{ expediente.id }}/etapa/${etapa}/subir-documento/`;
                console.log('URL de subida:', url);
                
                // Crear FormData con los datos del formulario
                const formData = new FormData(form);
                formData.append('area_id', areaActual);
                formData.append('etapa', etapa);
                
                // Mostrar datos del formulario para depuración
                console.log('Datos del formulario:');
                for (let [key, value] of formData.entries()) {
                    console.log(key, value);
                }
                
                // Realizar la petición
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    },
                    body: formData
                });

                // Manejar la respuesta
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Error en la respuesta del servidor:', errorText);
                    throw new Error(`Error al subir el documento: ${response.status} ${response.statusText}`);
                }

                const responseData = await response.json();
                console.log('Documento subido exitosamente:', responseData);
                showAlert('✅ Documento subido correctamente', 'success');
                
                // Cerrar el modal después de 1 segundo
                setTimeout(async () => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('subirDocumentoModal'));
                    if (modal) modal.hide();
                    
                    // Limpiar el formulario
                    form.reset();
                    
                    // Recargar los documentos del área
                    if (areaActual) {
                        console.log('Recargando documentos para el área:', areaActual);
                        
                        // Obtener el nombre del área para actualizar la vista
                        let areaNombre = '';
                        if (areaElement) {
                            areaNombre = areaElement.textContent.trim();
                        }
                        
                        // Esperar a que se cierre el modal
                        await new Promise(resolve => setTimeout(resolve, 500));
                        
                        // Actualizar la lista de documentos del área
                        await cargarDocumentosArea(areaActual, areaNombre);
                        
                        // Actualizar la barra de progreso
                        console.log('Actualizando barra de progreso...');
                        const progressData = await actualizarProgresoDocumentos();
                        console.log('Datos de progreso actualizados:', progressData);
                        
                        // Mostrar mensaje si se completó el 100%
                        if (progressData && progressData.porcentaje_completado >= 100) {
                            showAlert('¡Felicidades! Has completado todos los documentos requeridos para este expediente.', 'success');
                        }
                        
                        // Forzar una actualización visual de la barra de progreso
                        const progressBar = document.getElementById('globalProgressBar');
                        if (progressBar) {
                            progressBar.style.transition = 'width 0.6s ease';
                            // Forzar un reflow para asegurar la animación
                            void progressBar.offsetWidth;
                        }
                        
                        // Actualizar el contador de documentos en la pestaña del área
                        const tabLink = document.querySelector(`[data-bs-target="#area-${areaActual}"]`);
                        if (tabLink) {
                            const badge = tabLink.querySelector('.badge');
                            if (badge) {
                                const currentCount = parseInt(badge.textContent) || 0;
                                badge.textContent = currentCount + 1;
                            }
                        }
                    }
                }, 1000);
                
            } catch (error) {
                console.error('Error al subir el documento:', error);
                showAlert(`❌ ${error.message}`, 'danger');
                
                // Asegurarse de que el modal se cierre correctamente en caso de error
                const modalElement = document.getElementById('subirDocumentoModal');
                if (modalElement) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                        // Limpiar el backdrop manualmente si es necesario
                        const backdrop = document.querySelector('.modal-backdrop');
                        if (backdrop) {
                            backdrop.remove();
                        }
                        document.body.classList.remove('modal-open');
                        document.body.style.overflow = '';
                        document.body.style.paddingRight = '';
                    }
                }
            } finally {
                // Restaurar el estado del botón
                if (submitBtn) submitBtn.disabled = false;
                if (uploadSpinner) uploadSpinner.classList.add('d-none');
            }
        }"""
    
    # Reemplazar la función
    new_content = re.sub(pattern, new_function, content, flags=re.MULTILINE | re.DOTALL)
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("¡Función subirDocumento actualizada exitosamente!")

if __name__ == "__main__":
    update_upload_function()
