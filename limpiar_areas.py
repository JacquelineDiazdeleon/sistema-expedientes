import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db import transaction
from digitalizacion.models import (
    AreaTipoExpediente, 
    ValorAreaExpediente, 
    CampoAreaPersonalizado,
    ValorCampoPersonalizadoArea
)

def eliminar_todas_las_areas():
    """
    Elimina todos los registros relacionados con áreas de expedientes:
    - Valores de campos personalizados
    - Valores de áreas
    - Campos personalizados
    - Áreas de tipos de expediente
    """
    try:
        with transaction.atomic():
            # 1. Eliminar valores de campos personalizados
            print("Eliminando valores de campos personalizados...")
            num_valores_campos = ValorCampoPersonalizadoArea.objects.all().count()
            ValorCampoPersonalizadoArea.objects.all().delete()
            print(f"  - Se eliminaron {num_valores_campos} valores de campos personalizados")
            
            # 2. Eliminar valores de áreas
            print("\nEliminando valores de áreas...")
            num_valores_areas = ValorAreaExpediente.objects.all().count()
            ValorAreaExpediente.objects.all().delete()
            print(f"  - Se eliminaron {num_valores_areas} valores de áreas")
            
            # 3. Eliminar campos personalizados
            print("\nEliminando campos personalizados...")
            num_campos = CampoAreaPersonalizado.objects.all().count()
            CampoAreaPersonalizado.objects.all().delete()
            print(f"  - Se eliminaron {num_campos} campos personalizados")
            
            # 4. Eliminar áreas
            print("\nEliminando áreas...")
            num_areas = AreaTipoExpediente.objects.all().count()
            AreaTipoExpediente.objects.all().delete()
            print(f"  - Se eliminaron {num_areas} áreas")
            
            print("\n¡Proceso completado con éxito!")
            print("=" * 50)
            print(f"Resumen de eliminación:")
            print(f"- Valores de campos personalizados: {num_valores_campos}")
            print(f"- Valores de áreas: {num_valores_areas}")
            print(f"- Campos personalizados: {num_campos}")
            print(f"- Áreas: {num_areas}")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n¡Error durante la eliminación: {str(e)}")
        print("Se ha realizado un rollback de la transacción.")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("ELIMINACIÓN DE TODAS LAS ÁREAS DE EXPEDIENTES")
    print("=" * 50)
    print("\n¡ADVERTENCIA!")
    print("Esta acción eliminará TODAS las áreas de expedientes y sus datos relacionados.")
    print("Esta operación NO se puede deshacer.\n")
    
    confirmacion = input("¿Está seguro de que desea continuar? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        print("\nIniciando proceso de eliminación...\n")
        eliminar_todas_las_areas()
    else:
        print("\nOperación cancelada. No se realizaron cambios.")
        sys.exit(0)
