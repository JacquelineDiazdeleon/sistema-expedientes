import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.contrib.auth import get_user_model
from digitalizacion.models import PerfilUsuario, RolUsuario

def set_admin_role():
    try:
        # Get the user
        User = get_user_model()
        user = User.objects.get(email='jacquelinediazdeleon045@gmail.com')
        
        # Get or create admin role
        admin_role, created = RolUsuario.objects.get_or_create(
            nombre='Administrador',
            defaults={
                'descripcion': 'Administrador del sistema con acceso completo',
                'puede_administrar_sistema': True,
                'puede_crear_expedientes': True,
                'puede_editar_expedientes': True,
                'puede_eliminar_expedientes': True,
                'puede_ver_todos_expedientes': True,
                'puede_ver_reportes': True,
                'puede_gestionar_usuarios': True,
                'puede_gestionar_roles': True,
                'es_administrador': True
            }
        )
        
        # Create or update user profile with admin role
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={'rol': admin_role}
        )
        
        if not created and perfil.rol != admin_role:
            perfil.rol = admin_role
            perfil.save()
        
        # Ensure user is active and staff
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        print(f"Usuario {user.email} configurado como administrador exitosamente.")
        print(f"Rol asignado: {admin_role.nombre}")
        
    except User.DoesNotExist:
        print("Error: El usuario no existe.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    set_admin_role()
