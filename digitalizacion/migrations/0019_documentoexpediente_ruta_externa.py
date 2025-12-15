# Generated manually for ruta_externa and fecha_descargado fields

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('digitalizacion', '0018_solicitudescaneo'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoexpediente',
            name='ruta_externa',
            field=models.CharField(blank=True, help_text='Ruta del archivo en el servidor local (PC) si fue descargado desde Render', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='documentoexpediente',
            name='fecha_descargado',
            field=models.DateTimeField(blank=True, help_text='Fecha en que el archivo fue descargado a la PC local', null=True),
        ),
    ]

