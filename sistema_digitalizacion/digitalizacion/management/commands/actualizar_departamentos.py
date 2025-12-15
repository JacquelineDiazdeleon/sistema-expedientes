from django.core.management.base import BaseCommand
from digitalizacion.models import Departamento


class Command(BaseCommand):
    help = 'Actualiza los departamentos de la Secretaría de Servicios Públicos'
    
    def handle(self, *args, **options):
        self.stdout.write('🏢 Actualizando departamentos...')
        
        # Lista de nuevos departamentos (nombre incluye el código)
        departamentos_data = [
            '90000 - SECRETARÍA DE SERVICIOS PÚBLICOS',
            '90001 - DEPTO. DE ATENCIÓN CIUDADANA',
            '90003 - COORDINACIÓN JURÍDICA',
            
            '90004 - DIRECCIÓN ADMINISTRATIVA',
            '90005 - DEPTO. DE TALLER DE MTTO.',
            '90006 - DEPTO. DE COMPRAS',
            '90007 - DEPTO. DE RECURSOS HUMANOS',
            '90008 - COORDINACIÓN GENERAL DE S.P.',
            '90009 - DEPTO. DE CONTROL PRESUPUESTAL',
            '90101 - DEPTO. DE OPTIMIZACIÓN DE RECURSOS',
            
            '90300 - DIRECCIÓN DE LIMPIA Y ASEO PÚBLICO',
            '90301 - DEPTO. DE ASEO PÚBLICO',
            '90302 - DEPTO. DE RECOLECCIÓN',
            '90303 - DEPTO. DE RESIDUOS SÓLIDOS',
            '90304 - DEPTO. DE INSPECCIÓN',
            
            '90400 - DIRECCIÓN DE ALUMBRADO PÚBLICO',
            '90401 - DEPTO. DE OPERACIÓN Y MTTO.',
            '90402 - DEPTO. DE PROYECTOS Y SUPERVISIÓN',
            '90403 - DEPTO. DE EDIFICIOS PÚBLICOS E ILUM. ORNAMENTAL',
            
            '90500 - DIRECCIÓN DE PANTEONES',
            '90501 - DEPTO. DE OPERACIÓN Y SERVICIOS',
            '90502 - DEPTO. DE MANTENIMIENTO',
            
            '90600 - DIRECCIÓN DE PARQUES Y JARDINES',
            '90601 - DEPTO. DE PARQUES Y JARDINES',
            '90602 - DEPTO. DE PRODUCCIÓN Y SANIDAD',
            '90603 - DEPTO. DE OPERACIÓN Y SERVICIOS',
            '90604 - DEPTO. DE PARQUES PÚBLICOS',
            
            '90700 - INSTITUTO DE LA CONVIV. Y DESARROLLO LÍNEA VERDE',
            '90701 - DEPTO. DE ADMINISTRACIÓN Y PLANEACIÓN',
            '90702 - DEPTO. DE PROGRAMAS SOCIALES',
            '90703 - DEPTO. DE MANTENIMIENTO',
            '90704 - DIRECCIÓN DEL INSTITUTO',
        ]
        
        # Eliminar departamentos existentes
        departamentos_eliminados = Departamento.objects.all().count()
        Departamento.objects.all().delete()
        self.stdout.write(f'🗑️ Eliminados {departamentos_eliminados} departamentos existentes')
        
        # Crear nuevos departamentos
        departamentos_creados = 0
        for nombre_completo in departamentos_data:
            departamento, created = Departamento.objects.get_or_create(
                nombre=nombre_completo,
                defaults={
                    'activo': True,
                    'descripcion': f'Departamento de la Secretaría de Servicios Públicos'
                }
            )
            
            if created:
                departamentos_creados += 1
                self.stdout.write(f'✅ Creado: {nombre_completo}')
            else:
                # Actualizar si ya existe
                departamento.activo = True
                departamento.save()
                self.stdout.write(f'🔄 Actualizado: {nombre_completo}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Proceso completado:'))
        self.stdout.write(self.style.SUCCESS(f'   • Eliminados: {departamentos_eliminados} departamentos'))
        self.stdout.write(self.style.SUCCESS(f'   • Creados: {departamentos_creados} departamentos'))
        self.stdout.write(self.style.SUCCESS(f'   • Total final: {Departamento.objects.count()} departamentos'))
        self.stdout.write('')
        self.stdout.write('📋 Departamentos de la Secretaría de Servicios Públicos actualizados correctamente')
