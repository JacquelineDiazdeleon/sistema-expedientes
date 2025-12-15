from django.core.management.base import BaseCommand
from django.db import transaction
from digitalizacion.models import Expediente, AreaTipoExpediente, ValorAreaExpediente
from django.db.models import Q

class Command(BaseCommand):
    help = 'Sincroniza las áreas de todos los expedientes con las áreas definidas en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando sincronización de áreas de expedientes...'))
        
        # Obtener todos los expedientes
        expedientes = Expediente.objects.all()
        total = expedientes.count()
        
        self.stdout.write(f'Procesando {total} expedientes...')
        
        for i, expediente in enumerate(expedientes, 1):
            self.stdout.write(f'\n--- Procesando expediente {i}/{total}: ID {expediente.id} ---')
            self.sincronizar_areas_expediente(expediente)
        
        self.stdout.write(self.style.SUCCESS('\n¡Sincronización completada con éxito!'))
    
    def sincronizar_areas_expediente(self, expediente):
        """Sincroniza las áreas de un expediente con las áreas definidas"""
        tipo_expediente = expediente.tipo_expediente
        subtipo_expediente = getattr(expediente, 'subtipo_expediente', None)
        
        self.stdout.write(f'Tipo: {tipo_expediente}, Subtipo: {subtipo_expediente}')
        
        # 1. Obtener las áreas que deberían estar en este expediente
        areas_esperadas = self.obtener_areas_esperadas(tipo_expediente, subtipo_expediente)
        
        # 2. Obtener los valores actuales de áreas
        valores_actuales = {v.area_id: v for v in ValorAreaExpediente.objects.filter(expediente=expediente)}
        
        # 3. Eliminar valores de áreas que ya no deberían estar
        areas_esperadas_ids = {area.id for area in areas_esperadas}
        for area_id, valor in list(valores_actuales.items()):
            if area_id not in areas_esperadas_ids:
                self.stdout.write(self.style.WARNING(f'  - Eliminando valor de área obsoleta (ID: {area_id})'))
                valor.delete()
                del valores_actuales[area_id]
        
        # 4. Crear valores para áreas nuevas
        for area in areas_esperadas:
            if area.id not in valores_actuales:
                self.stdout.write(f'  + Creando valor para área: {area.titulo} (ID: {area.id})')
                try:
                    nuevo_valor = ValorAreaExpediente.objects.create(
                        expediente=expediente,
                        area=area,
                        completada=False
                    )
                    valores_actuales[area.id] = nuevo_valor
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error al crear valor: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'  Procesado: {len(areas_esperadas)} áreas sincronizadas'))
    
    def obtener_areas_esperadas(self, tipo_expediente, subtipo_expediente):
        """Obtiene las áreas que deberían estar en un expediente según su tipo y subtipo"""
        # Obtener todas las áreas activas para el tipo de expediente
        areas_query = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo_expediente,
            activa=True
        )
        
        # Filtrar por subtipo si existe
        if subtipo_expediente:
            # Caso especial para licitaciones con prefijo (licitacion_recurso_propio -> recurso_propio)
            if tipo_expediente == 'licitacion' and '_' in subtipo_expediente:
                subtipo_sin_prefijo = subtipo_expediente.split('_', 1)[1]
                
                # Buscar áreas con el subtipo sin prefijo
                areas_especificas = areas_query.filter(
                    subtipo_expediente=subtipo_sin_prefijo
                )
            else:
                # Para otros casos, buscar con el subtipo exacto
                areas_especificas = areas_query.filter(
                    subtipo_expediente=subtipo_expediente
                )
            
            # Obtener áreas genéricas (sin subtipo)
            areas_genericas = areas_query.filter(
                Q(subtipo_expediente__isnull=True) | 
                Q(subtipo_expediente='')
            )
            
            # Combinar áreas específicas y genéricas
            areas = list(areas_especificas) + list(areas_genericas)
        else:
            # Si no hay subtipo, solo obtener áreas genéricas
            areas = list(areas_query.filter(
                Q(subtipo_expediente__isnull=True) | 
                Q(subtipo_expediente='')
            ))
        
        # Eliminar duplicados por ID
        areas = list({area.id: area for area in areas}.values())
        
        # Ordenar por orden y título
        return sorted(areas, key=lambda x: (x.orden, x.titulo))
