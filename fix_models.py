import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db import models
from django.db.migrations.state import ModelState
from django.db.migrations.operations import AlterField
from django.db.migrations.migration import Migration
from django.db.migrations.state import ProjectState
from django.db.migrations import executor
from django.apps import apps

def alter_model_field(model_name, field_name, **field_kwargs):
    """
    Función para modificar un campo de un modelo existente
    """
    # Obtener el modelo
    model = apps.get_model('digitalizacion', model_name)
    
    # Obtener el campo existente
    old_field = model._meta.get_field(field_name)
    
    # Crear un nuevo campo con las nuevas opciones
    new_field = type(old_field)(**{
        **{f.attname: getattr(old_field, f.attname) for f in old_field.__class__._meta.fields},
        **field_kwargs,
        'name': field_name,
        'model': model,
    })
    
    # Crear una migración temporal
    migration = Migration('temp', 'digitalizacion')
    migration.operations = [
        AlterField(
            model_name=model_name.lower(),
            name=field_name,
            field=new_field,
        ),
    ]
    
    # Aplicar la migración
    executor = executor.MigrationExecutor(connection)
    project_state = ProjectState.from_apps(apps)
    
    # Aplicar la migración
    with connection.schema_editor() as schema_editor:
        migration.apply(project_state, schema_editor)
    
    print(f"Campo {field_name} del modelo {model_name} actualizado correctamente.")

if __name__ == "__main__":
    from django.db import connection
    
    # Modificar el campo usuario en HistorialExpediente
    alter_model_field(
        model_name='HistorialExpediente',
        field_name='usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    print("¡Proceso completado! Por favor, crea y aplica las migraciones manualmente con:")
    print("python manage.py makemigrations")
    print("python manage.py migrate")
