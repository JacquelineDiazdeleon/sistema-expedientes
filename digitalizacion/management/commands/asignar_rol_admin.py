from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from digitalizacion.models import RolUsuario, PerfilUsuario, Departamento

User = get_user_model()

class Command(BaseCommand):
    help = 'Asigna el rol de administrador a un usuario existente'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')

    def handle(self, *args, **options):
        username = options['username']
        
        # Buscar el usuario por nombre de usuario
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Error: No existe ningún usuario con el nombre de usuario {username}')
            )
            return
            
        # Obtener el rol de administrador
        try:
            rol_admin = RolUsuario.objects.get(nombre='administrador')
        except RolUsuario.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Error: El rol "administrador" no existe. Ejecuta setup_roles primero.')
            )
            return
        
        # Obtener o crear el perfil del usuario
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={
                'rol': rol_admin,
                'activo': True
            }
        )
        
        # Si el perfil ya existía, actualizar el rol
        if not created:
            perfil.rol = rol_admin
            perfil.activo = True
            perfil.save()
            self.stdout.write(
                self.style.SUCCESS(f'Se ha actualizado el rol del usuario {username} a administrador')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Se ha asignado el rol de administrador al usuario {username}')
            )
