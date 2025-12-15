    def get_progreso(self):
        """
        Calcula el progreso del expediente basado en las áreas que tienen al menos un documento.
        Retorna un diccionario con:
        - porcentaje: el porcentaje de áreas completadas (0-100)
        - completadas: número de áreas con al menos un documento
        - total: número total de áreas configuradas
        - texto: texto formateado (ej: '3/5 áreas completadas')
        """
        # Si está completado o rechazado, retornar el porcentaje correspondiente
        if self.estado_actual == 'completado':
            return {
                'porcentaje': 100,
                'completadas': 0,
                'total': 0,
                'texto': 'Expediente completo'
            }
        elif self.estado_actual == 'rechazado':
            return {
                'porcentaje': 0,
                'completadas': 0,
                'total': 0,
                'texto': 'Rechazado'
            }
        
        # Obtener todas las áreas configuradas para este tipo de expediente
        from django.db.models import Count
        
        # Construir el filtro base para las áreas configuradas
        filtro_areas = {
            'tipo_expediente': self.tipo_expediente,
            'activa': True
        }
        
        # Si el expediente tiene un subtipo, filtrar por él también
        if self.subtipo_expediente:
            filtro_areas['subtipo_expediente'] = self.subtipo_expediente
        
        # Obtener las áreas configuradas para este tipo (y subtipo si aplica) de expediente
        areas_configuradas = AreaTipoExpediente.objects.filter(**filtro_areas)
        
        # Depuración (opcional, puede ser eliminado después de verificar)
        print("Filtrando áreas con: {}".format(filtro_areas))
        print("Áreas encontradas: {}".format(areas_configuradas.count()))
        
        # Si no hay áreas configuradas, usar el método anterior basado en etapas
        if not areas_configuradas.exists():
            # Orden correcto de las etapas según el esquema del sistema
            orden_etapas = [
                'inicio',
                'solicitud_area',
                'cotizacion',
                'requisicion_sima',
                'suficiencia_presupuestal',
                'aprobacion_director',
                'aprobacion_secretario',
                'notificacion_compras',
                'valoracion_tipo',
                'adjudicacion',
                'formalizacion',
                'contrato',
                'recepcion_bien',
                'recepcion_facturacion',
                'generacion_evidencia',
                'envio_compras',
                'pago',
            ]
            
            # Contar etapas completadas
            etapas_completadas = self.etapas.filter(completada=True).count()
            etapas_totales = len(orden_etapas)
            
            # Calcular progreso basado en etapas completadas
            if etapas_totales > 0:
                porcentaje = int((etapas_completadas / etapas_totales) * 100)
                # Si se completó el 100%, actualizar el estado del expediente
                if porcentaje >= 100 and self.estado_actual != 'completado':
                    self.actualizar_estado_a_completado()
                
                return {
                    'porcentaje': min(porcentaje, 100),
                    'completadas': etapas_completadas,
                    'total': etapas_totales,
                    'texto': 'Expediente completo' if porcentaje >= 100 else '{}/{} etapas completadas'.format(etapas_completadas, etapas_totales)
                }
            
            return {
                'porcentaje': 0,
                'completadas': 0,
                'total': 0,
                'texto': 'Sin progreso'
            }
        
        # Obtener todos los documentos del expediente agrupados por etapa
        documentos_por_etapa = self.documentos.values('etapa').annotate(total=Count('id'))
        
        # Crear un conjunto con los nombres de las etapas que tienen documentos
        etapas_con_documentos = {doc['etapa'] for doc in documentos_por_etapa}
        
        # Contar áreas totales y áreas con documentos
        total_areas = areas_configuradas.count()
        areas_con_documentos = 0
        
        for area in areas_configuradas:
            # Verificar si hay al menos un documento en esta área
            if area.nombre in etapas_con_documentos:
                areas_con_documentos += 1
        
        # Si no hay áreas, retornar 0
        if total_areas == 0:
            return {
                'porcentaje': 0,
                'completadas': 0,
                'total': 0,
                'texto': 'Sin áreas configuradas'
            }
            
        # Calcular el porcentaje de áreas completadas
        porcentaje = int((areas_con_documentos / total_areas) * 100)
        
        # Si se completó el 100%, actualizar el estado del expediente
        if porcentaje >= 100 and self.estado_actual != 'completado':
            self.actualizar_estado_a_completado()
        
        return {
            'porcentaje': min(porcentaje, 100),
            'completadas': areas_con_documentos,
            'total': total_areas,
            'texto': '{}/{} áreas completadas'.format(areas_con_documentos, total_areas) if porcentaje < 100 else 'Expediente completo'
        }
