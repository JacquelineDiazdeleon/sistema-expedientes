#!/usr/bin/env python
import os
import sys

def listar_todas_las_areas():
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    import django
    django.setup()
    
    from digitalizacion.models import AreaTipoExpediente
    
    # Obtener todas las áreas ordenadas por tipo y orden
    areas = AreaTipoExpediente.objects.all().order_by('tipo_expediente', 'subtipo_expediente', 'orden')
    
    if areas.exists():
        print("\nTODAS LAS ÁREAS DEL SISTEMA")
        print("=" * 100)
        print(f"{'ID':<5} | {'Tipo':<15} | {'Subtipo':<20} | {'Nombre':<30} | {'Orden':<5} | {'Oblig.'} | {'Activa'} | {'Default'}")
        print("-" * 100)
        
        for area in areas:
            print(f"{area.id:<5} | {area.get_tipo_expediente_display()[:14]:<15} | "
                  f"{str(area.subtipo_expediente or 'N/A')[:18]:<20} | "
                  f"{area.titulo[:27]:<30} | "
                  f"{area.orden:<5} | "
                  f"{'Sí' if area.obligatoria else 'No':<6} | "
                  f"{'Sí' if area.activa else 'No':<6} | "
                  f"{'Sí' if area.es_default else 'No'}")
        
        # Mostrar estadísticas
        total = areas.count()
        activas = areas.filter(activa=True).count()
        print("\n" + "=" * 100)
        print(f"Total de áreas: {total} (Activas: {activas}, Inactivas: {total - activas})")
        
    else:
        print("No se encontraron áreas en el sistema.")

def eliminar_areas_por_id(ids):
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    import django
    django.setup()
    
    from digitalizacion.models import AreaTipoExpediente
    
    try:
        # Convertir la cadena de IDs a una lista de enteros
        id_list = [int(id_str.strip()) for id_str in ids.split(',') if id_str.strip().isdigit()]
        
        # Obtener y eliminar las áreas
        areas = AreaTipoExpediente.objects.filter(id__in=id_list)
        count = areas.count()
        
        if count > 0:
            print(f"\nSe eliminarán las siguientes {count} áreas:")
            for area in areas:
                print(f"- ID: {area.id}, Tipo: {area.get_tipo_expediente_display()}, Subtipo: {area.subtipo_expediente or 'N/A'}, Título: {area.titulo}")
            
            confirm = input("\n¿Está seguro que desea continuar? (s/n): ")
            if confirm.lower() == 's':
                deleted = areas.delete()
                print(f"\nSe eliminaron {deleted[0]} áreas correctamente.")
            else:
                print("Operación cancelada.")
        else:
            print("No se encontraron áreas con los IDs proporcionados.")
            
    except Exception as e:
        print(f"Error al eliminar áreas: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--eliminar':
        if len(sys.argv) > 2:
            eliminar_areas_por_id(sys.argv[2])
        else:
            print("Error: Debe especificar los IDs de las áreas a eliminar separados por comas.")
            print("Ejemplo: python listar_areas.py --eliminar 1,2,3")
    else:
        listar_todas_las_areas()
        print("\nPara eliminar áreas, use: python listar_areas.py --eliminar id1,id2,id3")
