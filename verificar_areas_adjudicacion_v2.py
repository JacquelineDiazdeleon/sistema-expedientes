#!/usr/bin/env python
import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import AreaTipoExpediente

def main():
    # Crear un archivo de salida
    with open('areas_adjudicacion_directa.txt', 'w', encoding='utf-8') as f:
        f.write("Áreas de adjudicación directa en la base de datos:\n")
        f.write("-" * 80 + "\n\n")
        
        # Obtener todas las áreas de adjudicación directa
        areas = AreaTipoExpediente.objects.filter(tipo_expediente='adjudicacion_directa')
        
        if not areas.exists():
            f.write("No se encontraron áreas de adjudicación directa en la base de datos.\n")
            return
        
        # Mostrar información detallada de cada área
        for area in areas:
            f.write(f"ID: {area.id}\n")
            f.write(f"  Nombre: {area.nombre}\n")
            f.write(f"  Título: {area.titulo}\n")
            f.write(f"  Tipo: {area.tipo_expediente}\n")
            f.write(f"  Subtipo: {area.subtipo_expediente}\n")
            f.write(f"  Activa: {area.activa}\n")
            f.write(f"  Orden: {area.orden}\n")
            f.write("-" * 80 + "\n\n")
        
        f.write(f"\nTotal de áreas de adjudicación directa: {areas.count()}\n")
    
    print("La información se ha guardado en 'areas_adjudicacion_directa.txt'")

if __name__ == "__main__":
    main()
