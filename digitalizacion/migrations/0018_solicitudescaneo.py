# Generated manually for SolicitudEscaneo model

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digitalizacion', '0017_hacer_expediente_opcional_en_historial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudEscaneo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area_id', models.IntegerField(help_text='ID del área donde se guardará el documento')),
                ('nombre_documento', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('duplex', models.BooleanField(default=False, help_text='Escanear por ambos lados')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('procesando', 'Procesando'), ('completado', 'Completado'), ('error', 'Error'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('mensaje_error', models.TextField(blank=True, null=True)),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_procesamiento', models.DateTimeField(blank=True, null=True)),
                ('fecha_completado', models.DateTimeField(blank=True, null=True)),
                ('documento_creado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitud_escaneo', to='digitalizacion.documentoexpediente')),
                ('expediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_escaneo', to='digitalizacion.expediente')),
                ('solicitado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitudes_escaneo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitud de Escaneo',
                'verbose_name_plural': 'Solicitudes de Escaneo',
                'ordering': ['-fecha_solicitud'],
            },
        ),
    ]

