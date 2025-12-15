from django.core.management.base import BaseCommand
from django.db.models import Q
from digitalizacion.models import AreaTipoExpediente

class Command(BaseCommand):
    help = 'Check areas for licitacion type'

    def handle(self, *args, **options):
        # Check for areas with tipo_expediente='licitacion'
        areas = AreaTipoExpediente.objects.filter(tipo_expediente='licitacion')
        
        if not areas.exists():
            self.stdout.write(self.style.ERROR('No areas found for licitacion type'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Found {areas.count()} areas for licitacion type:'))
            for area in areas:
                self.stdout.write(f'ID: {area.id}, Title: {area.titulo}, Subtipo: {area.subtipo_expediente or "None"}, Active: {area.activa}')
        
        # Check for areas with subtipo_expediente starting with 'licitacion_'
        licitacion_subtypes = AreaTipoExpediente.objects.filter(
            models.Q(subtipo_expediente__startswith='licitacion_') | 
            models.Q(subtipo_expediente__isnull=True, tipo_expediente='licitacion')
        )
        
        self.stdout.write('\nAreas for licitacion subtypes:')
        for area in licitacion_subtypes:
            self.stdout.write(f'ID: {area.id}, Type: {area.tipo_expediente}, Subtipo: {area.subtipo_expediente or "None"}, Title: {area.titulo}')
