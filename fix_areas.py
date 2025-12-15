import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db import transaction
from django.db.models import Count, Min
from digitalizacion.models import AreaTipoExpediente

def limpiar_areas_duplicadas():
    print("Iniciando limpieza de áreas duplicadas...")
    
    # Encontrar duplicados
    duplicates = AreaTipoExpediente.objects.values(
        'nombre', 'tipo_expediente'
    ).annotate(
        min_id=Min('id'),
        count_models=Count('id')
    ).filter(count_models__gt=1)
    
    print(f"Encontrados {len(duplicates)} grupos de áreas duplicadas")
    
    with transaction.atomic():
        for dup in duplicates:
            print(f"Procesando: {dup['tipo_expediente']} - {dup['nombre']}")
            
            # Mantener el más antiguo (menor ID)
            AreaTipoExpediente.objects.filter(
                nombre=dup['nombre'],
                tipo_expediente=dup['tipo_expediente']
            ).exclude(
                id=dup['min_id']
            ).delete()
            
            print(f"  -> Eliminados duplicados, se mantuvo ID {dup['min_id']}")
    
    print("Limpieza completada!")

if __name__ == "__main__":
    limpiar_areas_duplicadas()
