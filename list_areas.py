import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import AreaTipoExpediente

def main():
    # Open a file to write the output
    with open('areas_output.txt', 'w', encoding='utf-8') as f:
        # Get all areas
        f.write("All areas in the database:\n")
        f.write("ID\tType\t\tSubtype\t\tActive\tTitle\n")
        f.write("-" * 80 + "\n")
        
        for area in AreaTipoExpediente.objects.all().order_by('tipo_expediente', 'subtipo_expediente', 'id'):
            f.write(f"{area.id}\t{area.tipo_expediente}\t{area.subtipo_expediente or 'None'}\t{area.activa}\t{area.titulo}\n")
        
        # Get areas for licitacion type
        f.write("\nAreas for tipo_expediente='licitacion':\n")
        f.write("ID\tType\t\tSubtype\t\tActive\tTitle\n")
        f.write("-" * 80 + "\n")
        
        licitacion_areas = AreaTipoExpediente.objects.filter(tipo_expediente='licitacion').order_by('subtipo_expediente', 'id')
        for area in licitacion_areas:
            f.write(f"{area.id}\t{area.tipo_expediente}\t{area.subtipo_expediente or 'None'}\t{area.activa}\t{area.titulo}\n")
        
        # Get areas for licitacion subtypes
        f.write("\nAreas for licitacion subtypes (recurso_propio and fondo_federal):\n")
        f.write("ID\tType\t\tSubtype\t\tActive\tTitle\n")
        f.write("-" * 80 + "\n")
        
        licitacion_subtypes = AreaTipoExpediente.objects.filter(
            tipo_expediente='licitacion',
            subtipo_expediente__in=['recurso_propio', 'fondo_federal', 'licitacion_recurso_propio', 'licitacion_fondo_federal']
        ).order_by('subtipo_expediente', 'id')
        
        for area in licitacion_subtypes:
            f.write(f"{area.id}\t{area.tipo_expediente}\t{area.subtipo_expediente}\t{area.activa}\t{area.titulo}\n")
        
        # Check if there are any areas for licitacion type
        if not licitacion_areas.exists():
            f.write("\nWARNING: No areas found for tipo_expediente='licitacion'")
        
        f.write("\nDone!")

if __name__ == "__main__":
    main()
