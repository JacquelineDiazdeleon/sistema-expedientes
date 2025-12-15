from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import RolUsuario, PerfilUsuario, Departamento


class Command(BaseCommand):
    help = 'Crea un usuario del sistema para notificaciones automáticas'

    def handle(self, *args, **options):
        self.stdout.write('Creando usuario del sistema...')
        
        # Crear usuario del sistema
        system_username = 'sistema'
        if not User.objects.filter(username=system_username).exists():
            system_user = User.objects.create_user(
                username=system_username,
                email='sistema@serviciospublicos.gob.mx',
                password='Sistema2024!',  # Contraseña segura pero no se usará
                first_name='Sistema',
                last_name='Automático',
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
            
            # Obtener rol visualizador (mínimo privilegio)
            try:
                rol_visualizador = RolUsuario.objects.get(nombre='visualizador')
            except RolUsuario.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Error: Rol "visualizador" no encontrado. Ejecuta setup_roles primero.')
                )
                return
            
            # Obtener departamento por defecto
            try:
                departamento = Departamento.objects.first()
                if not departamento:
                    departamento = Departamento.objects.create(
                        nombre='Sistema',
                        descripcion='Departamento del sistema para notificaciones automáticas',
                        activo=True
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando departamento: {e}')
                )
                return
            
            # Crear perfil
            perfil = PerfilUsuario.objects.create(
                usuario=system_user,
                rol=rol_visualizador,
                departamento=departamento,
                puesto='Sistema Automático',
                telefono='',
                extension='',
                activo=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Usuario del sistema "{system_user.username}" creado exitosamente'
                )
            )
            self.stdout.write(
                f'  - Usuario: {system_user.username}'
            )
            self.stdout.write(
                f'  - Rol: {rol_visualizador.get_nombre_display()}'
            )
            self.stdout.write(
                f'  - Departamento: {departamento.nombre}'
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'  - Usuario del sistema "{system_username}" ya existe'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('Usuario del sistema configurado correctamente')
        )
