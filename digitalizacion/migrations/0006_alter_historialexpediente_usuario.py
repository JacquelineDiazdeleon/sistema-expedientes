# Generated manually
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

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
