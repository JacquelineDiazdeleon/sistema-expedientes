from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('digitalizacion', '0004_rename_tamano_fields'),  # This should match your last migration
    ]

    operations = [
        migrations.RenameField(
            model_name='documentoexpediente',
            old_name='tamaño_archivo',
            new_name='tamano_archivo',
        ),
    ]
