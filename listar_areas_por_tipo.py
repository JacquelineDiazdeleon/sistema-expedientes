#!/usr/bin/env python
import os
import sys

def listar_areas_por_tipo():
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    import django
    django.setup()
    
    from digitalizacion.models import AreaTipoExpediente, Expediente
    
    # Obtener todos los tipos de expediente únicos
    tipos_expediente = AreaTipoExpediente.objects.values_list('tipo_expediente', flat=True).distinct()
    
    for tipo in tipos_expediente:
        # Obtener el nombre del tipo
        tipo_nombre = dict(Expediente.TIPO_CHOICES).get(tipo, tipo)
        print(f"\n\n{'='*100}")
        print(f"TIPO DE EXPEDIENTE: {tipo_nombre.upper()} ({tipo})")
        print(f"{'='*100}")
        
        # Obtener subtipos para este tipo
        subtipos = AreaTipoExpediente.objects.filter(
            tipo_expediente=tipo
        ).exclude(subtipo_expediente__isnull=True).exclude(
            subtipo_expediente__exact=''
        ).values_list('subtipo_expediente', flat=True).distinct()
        
        if subtipos:
            for subtipo in subtipos:
                print(f"\n  Subtipo: {subtipo}")
                print(f"  {'-'*50}")
                areas = AreaTipoExpediente.objects.filter(
                    tipo_expediente=tipo,
                    subtipo_expediente=subtipo
                ).order_by('orden')
                
                for area in areas:
                    print(f"  {area.id:>4}. [{area.orden:>2}] {area.titulo}")
        else:
            # Si no hay subtipos, mostrar áreas directamente
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo,
                subtipo_expediente__isnull=True
            ).order_by('orden')
            
            if areas.exists():
                for area in areas:
                    print(f"  {area.id:>4}. [{area.orden:>2}] {area.titulo}")
            else:
                # Si no hay áreas sin subtipo, mostrar todas las áreas
                areas = AreaTipoExpediente.objects.filter(
                    tipo_expediente=tipo
                ).order_by('orden')
                
                for area in areas:
                    print(f"  {area.id:>4}. [{area.orden:>2}] {area.titulo}")
    
    # Mostrar estadísticas
    total = AreaTipoExpediente.objects.count()
    activas = AreaTipoExpediente.objects.filter(activa=True).count()
    print("\n" + "="*100)
    print(f"ESTADÍSTICAS:")
    print(f"Total de áreas: {total}")
    print(f"Áreas activas: {activas}")
    print(f"Áreas inactivas: {total - activas}")
    print("="*100)

if __name__ == "__main__":
    listar_areas_por_tipo()
