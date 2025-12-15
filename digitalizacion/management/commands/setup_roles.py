from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import RolUsuario, PerfilUsuario, Departamento


class Command(BaseCommand):
    help = 'Configura los roles por defecto y crea el usuario administrador'

    def handle(self, *args, **options):
        self.stdout.write('Configurando roles del sistema...')
        
        # Crear roles
        roles_data = [
            {
                'nombre': 'administrador',
                'descripcion': 'Acceso completo al sistema. Puede aprobar usuarios, gestionar expedientes y administrar el sistema.',
                'puede_aprobar_usuarios': True,
                'puede_editar_expedientes': True,
                'puede_ver_expedientes': True,
                'puede_crear_expedientes': True,
                'puede_eliminar_expedientes': True,
                'puede_administrar_sistema': True,
            },
            {
                'nombre': 'editor',
                'descripcion': 'Puede ver y editar expedientes, pero no puede aprobar usuarios ni administrar el sistema.',
                'puede_aprobar_usuarios': False,
                'puede_editar_expedientes': True,
                'puede_ver_expedientes': True,
                'puede_crear_expedientes': True,
                'puede_eliminar_expedientes': False,
                'puede_administrar_sistema': False,
            },
            {
                'nombre': 'visualizador',
                'descripcion': 'Solo puede ver expedientes. No puede editar, crear ni eliminar.',
                'puede_aprobar_usuarios': False,
                'puede_editar_expedientes': False,
                'puede_ver_expedientes': True,
                'puede_crear_expedientes': False,
                'puede_eliminar_expedientes': False,
                'puede_administrar_sistema': False,
            },
        ]
        
        for rol_data in roles_data:
            rol, created = RolUsuario.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults=rol_data
            )
            if created:
                self.stdout.write(f'  ✓ Rol "{rol.get_nombre_display()}" creado')
            else:
                self.stdout.write(f'  - Rol "{rol.get_nombre_display()}" ya existe')
        
        # Crear departamento por defecto si no existe
        departamento, created = Departamento.objects.get_or_create(
            nombre='Desarrollo y Base de Datos',
            defaults={
                'descripcion': 'Departamento de desarrollo y administración de base de datos',
                'activo': True
            }
        )
        if created:
            self.stdout.write(f'  ✓ Departamento "{departamento.nombre}" creado')
        
        # Crear usuario administrador
        admin_username = 'jacqueline.diaz'
        if not User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.create_user(
                username=admin_username,
                email='jacquelinediazdeleon045@gmail.com',
                password='Jacqueline250102',
                first_name='Jacqueline',
                last_name='Díaz de León Díaz de León',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            
            # Obtener rol administrador
            rol_admin = RolUsuario.objects.get(nombre='administrador')
            
            # Crear perfil
            perfil = PerfilUsuario.objects.create(
                usuario=admin_user,
                rol=rol_admin,
                departamento=departamento,
                puesto='Desarrolladora/DB',
                telefono='',
                extension='',
                activo=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Usuario administrador "{admin_user.get_full_name()}" creado'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'    Username: {admin_username}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'    Email: {admin_user.email}'
                )
            )
        else:
            self.stdout.write(f'  - Usuario administrador ya existe')
        
        self.stdout.write(
            self.style.SUCCESS('¡Configuración completada exitosamente!')
        )
