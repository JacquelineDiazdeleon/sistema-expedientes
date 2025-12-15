#!/usr/bin/env python
import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import AreaTipoExpediente

def main():
    print("Áreas de adjudicación directa en la base de datos:")
    print("-" * 80)
    
    # Obtener todas las áreas de adjudicación directa
    areas = AreaTipoExpediente.objects.filter(tipo_expediente='adjudicacion_directa')
    
    if not areas.exists():
        print("No se encontraron áreas de adjudicación directa en la base de datos.")
        return
    
    # Mostrar información detallada de cada área
    for area in areas:
        print(f"ID: {area.id}")
        print(f"  Nombre: {area.nombre}")
        print(f"  Título: {area.titulo}")
        print(f"  Tipo: {area.tipo_expediente}")
        print(f"  Subtipo: {area.subtipo_expediente}")
        print(f"  Activa: {area.activa}")
        print(f"  Orden: {area.orden}")
        print("-" * 80)
    
    print(f"\nTotal de áreas de adjudicación directa: {areas.count()}")

if __name__ == "__main__":
    main()
