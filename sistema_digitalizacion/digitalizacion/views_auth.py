from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .forms import SolicitudRegistroForm, LoginForm
from .models import SolicitudRegistro, PerfilUsuario, Notificacion, RolUsuario
from django.contrib.auth.models import User


def login_view(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('digitalizacion:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Intentar autenticar con username o email
            user = authenticate(username=username, password=password)
            if user is None:
                # Intentar con email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None and user.is_active:
                login(request, user)
                
                # Actualizar último acceso
                try:
                    perfil = user.perfil
                    perfil.fecha_ultimo_acceso = timezone.now()
                    perfil.save()
                except PerfilUsuario.DoesNotExist:
                    pass
                
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                return redirect('digitalizacion:dashboard')
            else:
                messages.error(request, 'Credenciales inválidas o usuario inactivo')
    else:
        form = LoginForm()
    
    return render(request, 'digitalizacion/auth/login.html', {'form': form})


def register_view(request):
    """Vista de registro con solicitud"""
    if request.user.is_authenticated:
        return redirect('digitalizacion:dashboard')
    
    if request.method == 'POST':
        form = SolicitudRegistroForm(request.POST)
        if form.is_valid():
            # Verificar si ya existe una solicitud con ese email
            email = form.cleaned_data['email_institucional']
            if SolicitudRegistro.objects.filter(email_institucional=email).exists():
                messages.error(request, 'Ya existe una solicitud con este correo electrónico')
            else:
                # Crear la solicitud
                solicitud = form.save(commit=False)
                solicitud.estado = 'pendiente'
                
                # Guardar la contraseña encriptada
                password = form.cleaned_data['password']
                solicitud.password_hash = password
                
                solicitud.save()
                
                messages.success(
                    request, 
                    'Tu solicitud de registro ha sido enviada. Serás notificado cuando sea aprobada.'
                )
                return redirect('digitalizacion:login')
    else:
        form = SolicitudRegistroForm()
    
    return render(request, 'digitalizacion/auth/register.html', {'form': form})


@login_required
def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('digitalizacion:login')


def terminos_condiciones(request):
    """Vista para mostrar términos y condiciones"""
    return render(request, 'digitalizacion/auth/terminos_condiciones.html')


def politica_privacidad(request):
    """Vista para mostrar política de privacidad"""
    return render(request, 'digitalizacion/auth/politica_privacidad.html')


@login_required
def cambiar_password(request):
    """Vista para que los usuarios cambien su propia contraseña"""
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual')
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')
        
        if not request.user.check_password(password_actual):
            messages.error(request, 'La contraseña actual es incorrecta')
        elif nueva_password != confirmar_password:
            messages.error(request, 'Las nuevas contraseñas no coinciden')
        elif not nueva_password:
            messages.error(request, 'La nueva contraseña no puede estar vacía')
        elif len(nueva_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
        else:
            # Cambiar la contraseña
            request.user.set_password(nueva_password)
            request.user.save()
            
            # Actualizar la sesión para evitar cierre de sesión
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Tu contraseña ha sido actualizada exitosamente')
            return redirect('digitalizacion:perfil_usuario')
    
    return render(request, 'digitalizacion/auth/cambiar_password.html')

