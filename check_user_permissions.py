import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

def check_user_permissions(username):
    from django.contrib.auth import get_user_model
    from digitalizacion.models import PerfilUsuario, RolUsuario
    
    User = get_user_model()
    
    try:
        # Get the user
        user = User.objects.get(username=username)
        print(f"\n=== User Information ===")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        
        # Check if user has a profile
        has_profile = hasattr(user, 'perfil')
        print(f"\n=== Profile Information ===")
        print(f"Has profile: {has_profile}")
        
        if has_profile:
            profile = user.perfil
            print(f"Profile active: {profile.activo}")
            
            # Check role
            if profile.rol:
                print(f"\n=== Role Information ===")
                print(f"Role name: {profile.rol.nombre}")
                print(f"Can manage system: {profile.rol.puede_administrar_sistema}")
                print(f"Can approve users: {profile.rol.puede_aprobar_usuarios}")
                print(f"Can edit records: {profile.rol.puede_editar_expedientes}")
                print(f"Can view records: {profile.rol.puede_ver_expedientes}")
                print(f"Can create records: {profile.rol.puede_crear_expedientes}")
                print(f"Can delete records: {profile.rol.puede_eliminar_expedientes}")
                
                # Check if admin role exists and is assigned
                admin_role = RolUsuario.objects.filter(nombre='administrador').first()
                if admin_role:
                    print(f"\n=== Admin Role Check ===")
                    print(f"Admin role exists: Yes")
                    print(f"User has admin role: {profile.rol == admin_role}")
                    
                    # If user doesn't have admin role, assign it
                    if profile.rol != admin_role:
                        print("\nAssigning admin role to user...")
                        profile.rol = admin_role
                        profile.save()
                        print("Admin role assigned successfully!")
                else:
                    print("\nError: Admin role does not exist in the system.")
                    print("Please run 'python manage.py setup_roles' first.")
            else:
                print("\nError: User does not have a role assigned.")
                admin_role = RolUsuario.objects.filter(nombre='administrador').first()
                if admin_role:
                    print("\nAssigning admin role to user...")
                    profile.rol = admin_role
                    profile.activo = True
                    profile.save()
                    print("Admin role assigned successfully!")
        else:
            print("\nError: User does not have a profile. Creating one...")
            from digitalizacion.models import Departamento
            
            # Get or create a default department
            departamento = Departamento.objects.first()
            if not departamento:
                departamento = Departamento.objects.create(
                    nombre='Administración',
                    descripcion='Departamento de administración del sistema',
                    activo=True
                )
            
            # Get or create admin role
            admin_role = RolUsuario.objects.filter(nombre='administrador').first()
            if not admin_role:
                print("Error: Admin role does not exist. Please run 'python manage.py setup_roles' first.")
                return
            
            # Create profile with admin role
            perfil = PerfilUsuario.objects.create(
                usuario=user,
                rol=admin_role,
                departamento=departamento,
                activo=True
            )
            print(f"Profile created with admin role for user {username}")
            
    except User.DoesNotExist:
        print(f"\nError: User '{username}' does not exist.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    check_user_permissions("jacquelinediazdeleon045")
