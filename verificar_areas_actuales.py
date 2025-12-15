import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db.models import Count
from digitalizacion.models import AreaTipoExpediente

def verificar_areas_por_tipo():
    print("=== ÁREAS POR TIPO DE EXPEDIENTE ===\n")
    
    # Obtener todos los tipos de expediente únicos
    tipos_expediente = AreaTipoExpediente.objects.values_list('tipo_expediente', flat=True).distinct()
    
    for tipo in tipos_expediente:
        print(f"\n--- {tipo.upper()} ---")
        
        # Obtener subtipos para este tipo
        subtipos = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo
        ).exclude(
            subtipo_expediente__isnull=True
        ).exclude(
            subtipo_expediente=''
        ).values_list('subtipo_expediente', flat=True).distinct()
        
        if subtipos:
            for subtipo in subtipos:
                print(f"\n  Subtipo: {subtipo}")
                areas = AreaTipoExpediente.objects.filter(
                    tipo_expediente=tipo,
                    subtipo_expediente=subtipo
                ).order_by('nombre')
                
                for area in areas:
                    print(f"  - {area.nombre} (ID: {area.id}, Activa: {area.activa})")
        
        # Mostrar áreas sin subtipo
        areas_sin_subtipo = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo,
            subtipo_expediente__isnull=True
        ) | AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo,
            subtipo_expediente=''
        )
        
        if areas_sin_subtipo.exists():
            print("\n  Sin subtipo:")
            for area in areas_sin_subtipo.order_by('nombre'):
                print(f"  - {area.nombre} (ID: {area.id}, Activa: {area.activa})")

def encontrar_duplicados():
    print("\n=== ÁREAS DUPLICADAS ===\n")
    
    # Encontrar áreas con el mismo nombre y tipo
    duplicados = AreaTipoExpediente.objects.values(
        'nombre', 'tipo_expediente'
    ).annotate(
        total=Count('id')
    ).filter(total__gt=1)
    
    if duplicados.exists():
        for dup in duplicados:
            areas = AreaTipoExpediente.objects.filter(
                nombre=dup['nombre'],
                tipo_expediente=dup['tipo_expediente']
            ).order_by('id')
            
            print(f"\nÁrea duplicada: {dup['tipo_expediente']} - {dup['nombre']}")
            for area in areas:
                print(f"  ID: {area.id}, Subtipo: {area.subtipo_expediente}, Activa: {area.activa}")
    else:
        print("No se encontraron áreas duplicadas.")

if __name__ == "__main__":
    verificar_areas_por_tipo()
    encontrar_duplicados()
