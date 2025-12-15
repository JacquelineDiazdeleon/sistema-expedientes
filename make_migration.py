import os
import sys

def main():
    # Asegurarse de que el directorio raíz del proyecto esté en el path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    
    import django
    django.setup()
    
    from django.db.migrations import Migration
    from django.db.migrations.operations import AlterField
    from django.db import models
    
    # Crear una migración manual
    migration = Migration('0006_alter_historialexpediente_usuario', 'digitalizacion')
    
    # Agregar la operación para modificar el campo usuario
    migration.operations = [
        AlterField(
            model_name='historialexpediente',
            name='usuario',
            field=models.ForeignKey(
                to='auth.User',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='historial_expedientes'
            ),
        ),
    ]
    
    # Guardar la migración
    migration_path = os.path.join(
        project_root,
        'digitalizacion',
        'migrations',
        '0006_alter_historialexpediente_usuario.py'
    )
    
    with open(migration_path, 'w') as f:
        f.write('''# Generated manually
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('digitalizacion', '0005_rename_tamano_archivo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historialexpediente',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                related_name='historial_expedientes'
            ),
        ),
    ]
''')
    
    print(f"Migración creada en: {migration_path}")
    print("\nPor favor, aplica la migración con:")
    print("python manage.py migrate")

if __name__ == "__main__":
    main()
