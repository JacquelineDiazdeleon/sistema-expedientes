#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Crear roles y superusuario automáticamente
python manage.py shell << EOF
from django.contrib.auth.models import User
from digitalizacion.models import RolUsuario, PerfilUsuario

# Crear roles si no existen
roles_data = [
    {'nombre': 'administrador', 'descripcion': 'Acceso completo al sistema', 'puede_aprobar_usuarios': True, 'puede_editar_expedientes': True, 'puede_crear_expedientes': True, 'puede_eliminar_expedientes': True, 'puede_administrar_sistema': True},
    {'nombre': 'editor', 'descripcion': 'Puede crear y editar expedientes', 'puede_editar_expedientes': True, 'puede_crear_expedientes': True},
    {'nombre': 'visualizador', 'descripcion': 'Solo puede ver expedientes', 'puede_ver_expedientes': True},
]

for rol_data in roles_data:
    nombre = rol_data.pop('nombre')
    rol, created = RolUsuario.objects.get_or_create(nombre=nombre, defaults=rol_data)
    if created:
        print(f'Rol creado: {nombre}')
    else:
        print(f'Rol ya existe: {nombre}')

# Crear superusuario si no existe
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@sistema.com', 'Admin123!')
    # Crear perfil para el superusuario
    rol_admin = RolUsuario.objects.get(nombre='administrador')
    PerfilUsuario.objects.create(usuario=user, rol=rol_admin)
    print('Superusuario creado: admin / Admin123!')
else:
    print('El usuario admin ya existe')
EOF
