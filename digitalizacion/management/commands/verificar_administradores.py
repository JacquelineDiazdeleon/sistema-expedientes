from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import PerfilUsuario, RolUsuario


class Command(BaseCommand):
    help = 'Verifica y corrige los permisos de administradores'

    def handle(self, *args, **options):
        self.stdout.write('Verificando permisos de administradores...')
        
        # Obtener el rol de administrador
        try:
            rol_admin = RolUsuario.objects.get(nombre='administrador')
            self.stdout.write(f'✓ Rol administrador encontrado: {rol_admin.nombre}')
        except RolUsuario.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Rol administrador no encontrado'))
            return
        
        # Verificar usuarios con rol de administrador
        usuarios_admin = User.objects.filter(
            perfil__rol=rol_admin,
            is_active=True
        ).select_related('perfil', 'perfil__rol')
        
        self.stdout.write(f'\nUsuarios con rol administrador: {usuarios_admin.count()}')
        
        for usuario in usuarios_admin:
            self.stdout.write(f'\n--- Usuario: {usuario.username} ---')
            self.stdout.write(f'  Nombre: {usuario.get_full_name()}')
            self.stdout.write(f'  Email: {usuario.email}')
            self.stdout.write(f'  Activo: {usuario.is_active}')
            self.stdout.write(f'  Staff: {usuario.is_staff}')
            self.stdout.write(f'  Superuser: {usuario.is_superuser}')
            self.stdout.write(f'  Rol: {usuario.perfil.rol.nombre}')
            self.stdout.write(f'  Puede administrar: {usuario.perfil.rol.puede_administrar_sistema}')
            
            # Verificar si puede acceder al panel
            tiene_perfil = hasattr(usuario, 'perfil')
            tiene_rol = tiene_perfil and usuario.perfil.rol is not None
            puede_administrar = tiene_rol and usuario.perfil.rol.puede_administrar_sistema
            
            if tiene_perfil and tiene_rol and puede_administrar:
                self.stdout.write(self.style.SUCCESS('  ✓ Puede acceder al panel de administración'))
            else:
                self.stdout.write(self.style.ERROR('  ✗ NO puede acceder al panel de administración'))
                if not tiene_perfil:
                    self.stdout.write(self.style.WARNING('    - No tiene perfil'))
                if not tiene_rol:
                    self.stdout.write(self.style.WARNING('    - No tiene rol'))
                if not puede_administrar:
                    self.stdout.write(self.style.WARNING('    - Rol no tiene permisos de administración'))
        
        # Mostrar todos los usuarios activos
        self.stdout.write(f'\n\nTodos los usuarios activos:')
        usuarios_activos = User.objects.filter(is_active=True).select_related('perfil', 'perfil__rol')
        
        for usuario in usuarios_activos:
            rol_nombre = usuario.perfil.rol.nombre if hasattr(usuario, 'perfil') and usuario.perfil.rol else 'Sin rol'
            puede_admin = usuario.perfil.rol.puede_administrar_sistema if hasattr(usuario, 'perfil') and usuario.perfil.rol else False
            
            self.stdout.write(f'  {usuario.username}: {rol_nombre} (Admin: {puede_admin})')
        
        self.stdout.write(self.style.SUCCESS('\n¡Verificación completada!'))
