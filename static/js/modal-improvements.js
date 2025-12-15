// ============================================
// MEJORAS PARA MODALES SIN BACKDROP
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Eliminar backdrop de todos los modales
    function removeModalBackdrop() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.style.display = 'none';
            backdrop.style.opacity = '0';
            backdrop.style.pointerEvents = 'none';
            backdrop.style.background = 'none';
        });
    }
    
    // Mejorar visibilidad de modales
    function improveModalVisibility() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            // Agregar backdrop sutil
            modal.style.background = 'rgba(0, 0, 0, 0.1)';
            modal.style.backdropFilter = 'blur(2px)';
            modal.style.webkitBackdropFilter = 'blur(2px)';
            
            // Mejorar el contenido del modal
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.style.boxShadow = '0 20px 60px rgba(0, 0, 0, 0.3)';
                modalContent.style.borderRadius = '20px';
                modalContent.style.border = '3px solid var(--border-primary)';
            }
        });
    }
    
    // Mejorar botones en modales
    function improveModalButtons() {
        const modalButtons = document.querySelectorAll('.modal .btn');
        modalButtons.forEach(button => {
            button.style.borderRadius = '12px';
            button.style.fontWeight = '500';
            button.style.padding = '0.75rem 1.5rem';
            button.style.transition = 'all 0.3s ease';
            
            // Efectos hover mejorados
            button.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                    this.style.transform = 'translateY(-2px)';
                }
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }
    
    // Mejorar formularios en modales
    function improveModalForms() {
        const modalInputs = document.querySelectorAll('.modal .form-control, .modal .form-select, .modal textarea');
        modalInputs.forEach(input => {
            input.style.borderRadius = '12px';
            input.style.padding = '0.75rem 1rem';
            input.style.fontSize = '1rem';
            input.style.transition = 'all 0.3s ease';
            
            // Efectos focus mejorados
            input.addEventListener('focus', function() {
                this.style.transform = 'translateY(-1px)';
                this.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            });
            
            input.addEventListener('blur', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            });
        });
    }
    
    // Mejorar alertas en modales
    function improveModalAlerts() {
        const modalAlerts = document.querySelectorAll('.modal .alert');
        modalAlerts.forEach(alert => {
            alert.style.borderRadius = '12px';
            alert.style.border = '2px solid';
            alert.style.padding = '1rem 1.5rem';
            alert.style.marginBottom = '1.5rem';
        });
    }
    
    // Mejorar labels en modales
    function improveModalLabels() {
        const modalLabels = document.querySelectorAll('.modal .form-label');
        modalLabels.forEach(label => {
            label.style.fontWeight = '500';
            label.style.marginBottom = '0.5rem';
            label.style.fontSize = '0.95rem';
        });
    }
    
    // Aplicar mejoras cuando se abre un modal
    document.addEventListener('show.bs.modal', function(event) {
        removeModalBackdrop();
        improveModalVisibility();
        improveModalButtons();
        improveModalForms();
        improveModalAlerts();
        improveModalLabels();
    });
    
    // Aplicar mejoras cuando se muestra un modal
    document.addEventListener('shown.bs.modal', function(event) {
        removeModalBackdrop();
    });
    
    // Aplicar mejoras iniciales
    removeModalBackdrop();
    improveModalVisibility();
    improveModalButtons();
    improveModalForms();
    improveModalAlerts();
    improveModalLabels();
    
    // Mejorar específicamente el modal de rechazar expediente
    const rechazarModal = document.getElementById('rechazarExpedienteModal');
    if (rechazarModal) {
        rechazarModal.addEventListener('show.bs.modal', function() {
            // Centrar el modal
            const modalDialog = this.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.classList.add('modal-dialog-centered');
            }
            
            // Mejorar el textarea del motivo
            const textarea = this.querySelector('#motivo_rechazo');
            if (textarea) {
                textarea.style.minHeight = '120px';
                textarea.style.resize = 'vertical';
            }
            
            // Mejorar la alerta de advertencia
            const alert = this.querySelector('.alert-warning');
            if (alert) {
                alert.style.borderLeft = '4px solid #f59e0b';
                alert.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
            }
        });
    }
    
    // Mejorar todos los modales existentes
    const allModals = document.querySelectorAll('.modal');
    allModals.forEach(modal => {
        // Agregar clase para mejor estilizado
        modal.classList.add('modal-improved');
        
        // Mejorar el diálogo
        const modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.classList.add('modal-dialog-centered');
        }
    });
    
    // Mejorar responsive de modales
    function improveModalResponsive() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalDialog = modal.querySelector('.modal-dialog');
            if (modalDialog && window.innerWidth <= 768) {
                modalDialog.style.margin = '1rem';
                modalDialog.style.maxWidth = 'calc(100% - 2rem)';
            }
        });
    }
    
    // Aplicar responsive en carga y resize
    improveModalResponsive();
    window.addEventListener('resize', improveModalResponsive);
    
    // Mejorar accesibilidad
    function improveModalAccessibility() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            // Asegurar que el modal tenga el foco correcto
            modal.addEventListener('shown.bs.modal', function() {
                const firstInput = this.querySelector('input, textarea, select, button:not([data-bs-dismiss="modal"])');
                if (firstInput) {
                    firstInput.focus();
                }
            });
            
            // Mejorar navegación con teclado
            modal.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const closeButton = this.querySelector('[data-bs-dismiss="modal"]');
                    if (closeButton) {
                        closeButton.click();
                    }
                }
            });
        });
    }
    
    improveModalAccessibility();
    
    // Mejorar animaciones de modales
    function improveModalAnimations() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalDialog = modal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.style.transition = 'transform 0.3s ease-out';
            }
        });
    }
    
    improveModalAnimations();
    
    console.log('✅ Mejoras de modales aplicadas correctamente');
});

// ============================================
// FUNCIONES ADICIONALES PARA MODALES
// ============================================

// Función para abrir modal con mejoras
function openModalWithImprovements(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Aplicar mejoras específicas
        setTimeout(() => {
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.style.transform = 'scale(1)';
                modalContent.style.opacity = '1';
            }
        }, 100);
    }
}

// Función para cerrar modal con animación
function closeModalWithAnimation(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.transform = 'scale(0.95)';
            modalContent.style.opacity = '0';
            
            setTimeout(() => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }, 200);
        }
    }
}
