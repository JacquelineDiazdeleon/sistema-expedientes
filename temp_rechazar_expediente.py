            # Guardar el estado anterior para el historial
            estado_anterior = expediente.estado
            
            # Actualizar el estado del expediente
            expediente.estado = 'rechazado'
            expediente.estado_actual = 'rechazado'
            
            # Guardar los cambios
            expediente.save(update_fields=['estado', 'estado_actual'])
