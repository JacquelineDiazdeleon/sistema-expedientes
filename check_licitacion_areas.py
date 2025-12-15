import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import AreaTipoExpediente

print("Areas for tipo_expediente='licitacion':")
areas = AreaTipoExpediente.objects.filter(tipo_expediente='licitacion')
for area in areas:
    print(f"ID: {area.id}, Title: {area.titulo}, Subtipo: {area.subtipo_expediente or 'None'}, Active: {area.activa}")

print("\nAreas for licitacion subtypes:")
licitacion_subtypes = AreaTipoExpediente.objects.filter(
    tipo_expediente='licitacion',
    subtipo_expediente__isnull=False
)
for area in licitacion_subtypes:
    print(f"ID: {area.id}, Title: {area.titulo}, Subtipo: {area.subtipo_expediente}, Active: {area.activa}")
