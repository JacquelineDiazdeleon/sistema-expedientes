from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from digitalizacion.models import Expediente


class Command(BaseCommand):
    help = 'Diagnostica el problema con los reportes de expedientes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Iniciando diagnóstico de reportes...'))
        
        # 1. Verificar si hay expedientes en la base de datos
        total_expedientes = Expediente.objects.count()
        self.stdout.write(f'📊 Total de expedientes en la BD: {total_expedientes}')
        
        if total_expedientes == 0:
            self.stdout.write(self.style.WARNING('⚠️  No hay expedientes en la base de datos'))
            return
        
        # 2. Verificar expedientes recientes
        expedientes_recientes = Expediente.objects.order_by('-fecha_creacion')[:5]
        self.stdout.write(f'\n📅 Últimos 5 expedientes:')
        for exp in expedientes_recientes:
            self.stdout.write(f'   - {exp.numero_expediente} ({exp.fecha_creacion}) - {exp.estado_actual}')
        
        # 3. Probar la consulta de filtros
        self.stdout.write(f'\n🔍 Probando consulta de filtros...')
        
        # Fechas de prueba
        fecha_inicio = datetime.now().date() - timedelta(days=30)
        fecha_fin = datetime.now().date()
        
        self.stdout.write(f'   Fecha inicio: {fecha_inicio}')
        self.stdout.write(f'   Fecha fin: {fecha_fin}')
        
        # Convertir fechas a datetime para la consulta
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        try:
            # Probar la consulta
            expedientes_filtrados = Expediente.objects.filter(
                fecha_creacion__range=[fecha_inicio_dt, fecha_fin_dt]
            ).select_related('departamento', 'creado_por')
            
            count = expedientes_filtrados.count()
            self.stdout.write(f'   ✅ Consulta exitosa: {count} expedientes encontrados')
            
            # Verificar si hay problemas con las relaciones
            for exp in expedientes_filtrados[:3]:
                try:
                    dept = exp.departamento.nombre if exp.departamento else 'Sin departamento'
                    user = exp.creado_por.get_full_name() if exp.creado_por else 'Usuario no especificado'
                    self.stdout.write(f'      - {exp.numero_expediente}: Depto={dept}, User={user}')
                except Exception as e:
                    self.stdout.write(f'      - ❌ Error en expediente {exp.id}: {e}')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error en la consulta: {e}'))
        
        # 4. Probar consulta simple sin filtros de fecha
        self.stdout.write(f'\n🔍 Probando consulta simple...')
        try:
            expedientes_simples = Expediente.objects.all()[:5]
            self.stdout.write(f'   ✅ Consulta simple exitosa: {expedientes_simples.count()} expedientes')
            
            for exp in expedientes_simples:
                try:
                    dept = exp.departamento.nombre if exp.departamento else 'Sin departamento'
                    user = exp.creado_por.get_full_name() if exp.creado_por else 'Usuario no especificado'
                    self.stdout.write(f'      - {exp.numero_expediente}: Depto={dept}, User={user}')
                except Exception as e:
                    self.stdout.write(f'      - ❌ Error en expediente {exp.id}: {e}')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error en consulta simple: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Diagnóstico completado'))
