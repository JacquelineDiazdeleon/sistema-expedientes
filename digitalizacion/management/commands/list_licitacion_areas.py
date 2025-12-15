from django.core.management.base import BaseCommand
from digitalizacion.models import AreaTipoExpediente

class Command(BaseCommand):
    help = 'List all areas for licitacion type'

    def handle(self, *args, **options):
        areas = AreaTipoExpediente.objects.filter(tipo_expediente='licitacion')
        
        if not areas.exists():
            self.stdout.write(self.style.WARNING('No areas found for licitacion type'))
            return
            
        self.stdout.write('ID\tType\tSubtype\t\tActive\tTitle')
        self.stdout.write('-' * 80)
        
        for area in areas:
            self.stdout.write(
                f"{area.id}\t"
                f"{area.tipo_expediente}\t"
                f"{area.subtipo_expediente or 'None':<15}\t"
                f"{area.activa}\t"
                f"{area.titulo}"
            )
