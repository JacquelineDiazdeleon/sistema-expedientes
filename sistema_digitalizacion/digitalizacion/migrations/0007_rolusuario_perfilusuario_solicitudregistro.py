# Generated manually for auth models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('digitalizacion', '0006_comentarioarea_notificacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='RolUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('administrador', 'Administrador'), ('editor', 'Editor'), ('visualizador', 'Visualizador')], max_length=20, unique=True)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('puede_aprobar_usuarios', models.BooleanField(default=False)),
                ('puede_editar_expedientes', models.BooleanField(default=False)),
                ('puede_ver_expedientes', models.BooleanField(default=True)),
                ('puede_crear_expedientes', models.BooleanField(default=False)),
                ('puede_eliminar_expedientes', models.BooleanField(default=False)),
                ('puede_administrar_sistema', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Rol de Usuario',
                'verbose_name_plural': 'Roles de Usuario',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puesto', models.CharField(blank=True, max_length=100, null=True)),
                ('telefono', models.CharField(blank=True, max_length=20, null=True)),
                ('extension', models.CharField(blank=True, max_length=10, null=True)),
                ('foto_perfil', models.ImageField(blank=True, null=True, upload_to='perfiles/')),
                ('activo', models.BooleanField(default=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('fecha_ultimo_acceso', models.DateTimeField(blank=True, null=True)),
                ('departamento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='digitalizacion.departamento')),
                ('rol', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='digitalizacion.rolusuario')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de Usuario',
                'verbose_name_plural': 'Perfiles de Usuario',
            },
        ),
        migrations.CreateModel(
            name='SolicitudRegistro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombres', models.CharField(max_length=100)),
                ('apellidos', models.CharField(max_length=100)),
                ('email_institucional', models.EmailField(max_length=254, unique=True)),
                ('puesto', models.CharField(blank=True, max_length=100, null=True)),
                ('telefono', models.CharField(blank=True, max_length=20, null=True)),
                ('extension', models.CharField(blank=True, max_length=10, null=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')], default='pendiente', max_length=20)),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_resolucion', models.DateTimeField(blank=True, null=True)),
                ('password_hash', models.CharField(blank=True, max_length=255, null=True)),
                ('motivo_rechazo', models.TextField(blank=True, null=True)),
                ('departamento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='digitalizacion.departamento')),
                ('resuelto_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitudes_resueltas', to=settings.AUTH_USER_MODEL)),
                ('rol_solicitado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='digitalizacion.rolusuario')),
                ('usuario_creado', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitud_registro', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitud de Registro',
                'verbose_name_plural': 'Solicitudes de Registro',
                'ordering': ['-fecha_solicitud'],
            },
        ),
    ]

