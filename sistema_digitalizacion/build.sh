#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Crear superusuario automáticamente si no existe
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sistema.com', 'Admin123!')
    print('Superusuario creado: admin / Admin123!')
else:
    print('El usuario admin ya existe')
EOF
