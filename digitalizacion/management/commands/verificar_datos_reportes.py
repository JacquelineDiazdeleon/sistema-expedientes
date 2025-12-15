from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
from digitalizacion.models import Expediente, User, DocumentoExpediente


class Command(BaseCommand):
    help = 'Verifica los datos disponibles para reportes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICANDO DATOS PARA REPORTES...'))
        
        # Fecha actual
        now = timezone.now()
        today = now.date()
        fecha_inicio = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_fin = today.strftime('%Y-%m-%d')
        
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except:
            fecha_inicio_dt = today - timedelta(days=30)
            fecha_fin_dt = today
        
        self.stdout.write(f'📅 Período de análisis: {fecha_inicio} a {fecha_fin}')
        
        # Total de expedientes
        total_expedientes = Expediente.objects.count()
        self.stdout.write(f'📊 Total de expedientes en BD: {total_expedientes}')
        
        # Expedientes en el período
        expedientes_periodo = Expediente.objects.filter(
            fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).count()
        self.stdout.write(f'📊 Expedientes en período: {expedientes_periodo}')
        
        # Expedientes por tipo
        expedientes_por_tipo = Expediente.objects.filter(
            fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).values('tipo_expediente').annotate(
            total=Count('id')
        ).order_by('-total')
        
        self.stdout.write(f'📊 Expedientes por tipo: {list(expedientes_por_tipo)}')
        
        # Expedientes por estado
        expedientes_por_estado = Expediente.objects.filter(
            fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).values('estado_actual').annotate(
            total=Count('id')
        ).order_by('-total')
        
        self.stdout.write(f'📊 Expedientes por estado: {list(expedientes_por_estado)}')
        
        # Usuarios activos
        usuarios_activos = User.objects.filter(
            expedientes_creados__fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).annotate(
            total_expedientes=Count('expedientes_creados')
        ).filter(
            total_expedientes__gt=0
        ).order_by('-total_expedientes')[:10]
        
        self.stdout.write(f'📊 Usuarios activos: {list(usuarios_activos)}')
        
        # Expedientes por mes
        expedientes_por_mes = []
        for i in range(12):
            fecha = now - timedelta(days=30*i)
            mes = fecha.strftime('%Y-%m')
            total = Expediente.objects.filter(
                fecha_creacion__year=fecha.year,
                fecha_creacion__month=fecha.month
            ).count()
            expedientes_por_mes.append({'mes': mes, 'total': total})
        
        expedientes_por_mes.reverse()
        self.stdout.write(f'📊 Expedientes por mes: {expedientes_por_mes}')
        
        # Verificar si hay expedientes recientes
        expedientes_recientes = Expediente.objects.all().order_by('-fecha_creacion')[:5]
        self.stdout.write(f'📊 Expedientes más recientes:')
        for exp in expedientes_recientes:
            self.stdout.write(f'   - {exp.numero_expediente} ({exp.fecha_creacion}) - {exp.estado_actual}')
        
        # Verificar tipos de expediente disponibles
        tipos_disponibles = Expediente.objects.values_list('tipo_expediente', flat=True).distinct()
        self.stdout.write(f'📊 Tipos de expediente disponibles: {list(tipos_disponibles)}')
        
        # Verificar estados disponibles
        estados_disponibles = Expediente.objects.values_list('estado_actual', flat=True).distinct()
        self.stdout.write(f'📊 Estados disponibles: {list(estados_disponibles)}')
        
        self.stdout.write(self.style.SUCCESS('✅ Verificación completada'))
