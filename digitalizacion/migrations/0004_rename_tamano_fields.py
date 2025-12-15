from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('digitalizacion', '0003_documentoexpediente_area'),
    ]

    operations = [
        migrations.RenameField(
            model_name='areatipoexpediente',
            old_name='tamaño_max_archivo',
            new_name='tamano_max_archivo',
        ),
    ]
