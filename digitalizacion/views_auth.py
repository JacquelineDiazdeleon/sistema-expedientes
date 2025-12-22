from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .forms import SolicitudRegistroForm, LoginForm
from .models import SolicitudRegistro, PerfilUsuario, Notificacion, RolUsuario
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from .role_utils import puede_aprobar_usuarios


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
                    from django.contrib.auth.models import User
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
                
                messages.success(request, f'¡Bienvenido, {user.get_full_name()}!')
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
                
                # Notificar a administradores
                notificar_administradores_solicitud(solicitud)
                
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


def notificar_administradores_solicitud(solicitud):
    """Notifica a todos los administradores sobre una nueva solicitud de registro"""
    from django.contrib.auth.models import User
    
    try:
        # Obtener usuario del sistema para notificaciones automáticas
        system_user = User.objects.get(username='sistema')
        
        rol_admin = RolUsuario.objects.get(nombre='administrador')
        administradores = User.objects.filter(perfil__rol=rol_admin, is_active=True)
        
        for admin in administradores:
            Notificacion.objects.create(
                usuario=admin,
                expediente=None,  # No hay expediente asociado
                tipo='solicitud_registro',
                titulo='Nueva solicitud de registro',
                mensaje=f'{solicitud.nombre_completo} ha solicitado acceso al sistema con rol de {solicitud.rol_solicitado.get_nombre_display()}',
                generada_por=system_user,  # Usuario del sistema
                enlace=f'/admin/solicitudes/{solicitud.id}/'
            )
    except (RolUsuario.DoesNotExist, User.DoesNotExist):
        pass


@login_required
def solicitudes_pendientes(request):
    """Vista para administradores: listar solicitudes pendientes"""
    from .role_utils import puede_aprobar_usuarios
    if not puede_aprobar_usuarios(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('digitalizacion:dashboard')
    
    solicitudes_pendientes = SolicitudRegistro.objects.filter(estado='pendiente').order_by('-fecha_solicitud')
    solicitudes_aprobadas = SolicitudRegistro.objects.filter(estado='aprobada').order_by('-fecha_resolucion')
    solicitudes_rechazadas = SolicitudRegistro.objects.filter(estado='rechazada').order_by('-fecha_resolucion')
    total_solicitudes = SolicitudRegistro.objects.count()
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'total_solicitudes': total_solicitudes
    }
    return render(request, 'digitalizacion/auth/solicitudes_pendientes.html', context)


@login_required
def aprobar_solicitud(request, solicitud_id):
    """Vista para aprobar una solicitud - Solo administradores"""
    if not puede_aprobar_usuarios(request.user):
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    try:
        solicitud = SolicitudRegistro.objects.get(id=solicitud_id, estado='pendiente')
        user, password = solicitud.aprobar(request.user)
        
        # Notificar al usuario aprobado
        notificar_usuario_aprobado(solicitud, password)
        
        return JsonResponse({
            'success': True, 
            'message': f'Usuario {user.get_full_name()} aprobado exitosamente'
        })
    except SolicitudRegistro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Solicitud no encontrada'})


@login_required
def rechazar_solicitud(request, solicitud_id):
    """Vista para rechazar una solicitud - Solo administradores"""
    if not puede_aprobar_usuarios(request.user):
        return JsonResponse({'success': False, 'message': 'Sin permisos'})
    
    try:
        solicitud = SolicitudRegistro.objects.get(id=solicitud_id, estado='pendiente')
        motivo = request.POST.get('motivo', 'Solicitud rechazada por el administrador')
        solicitud.rechazar(request.user, motivo)
        
        # Notificar al usuario rechazado
        notificar_usuario_rechazado(solicitud, motivo)
        
        return JsonResponse({
            'success': True, 
            'message': 'Solicitud rechazada exitosamente'
        })
    except SolicitudRegistro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Solicitud no encontrada'})


def notificar_usuario_aprobado(solicitud, password):
    """Notifica al usuario que su solicitud fue aprobada"""
    from django.contrib.auth.models import User
    
    # Aquí podrías enviar un email con las credenciales
    # Por ahora solo creamos una notificación en el sistema
    if solicitud.usuario_creado:
        try:
            system_user = User.objects.get(username='sistema')
            Notificacion.objects.create(
                usuario=solicitud.usuario_creado,
                expediente=None,
                tipo='solicitud_aprobada',
                titulo='Solicitud de registro aprobada',
                mensaje=f'Tu solicitud de registro ha sido aprobada. Ya puedes iniciar sesión con tu correo y contraseña.',
                generada_por=system_user,
                enlace='/auth/login/'
            )
        except User.DoesNotExist:
            pass


def notificar_usuario_rechazado(solicitud, motivo):
    """Notifica al usuario que su solicitud fue rechazada"""
    from django.contrib.auth.models import User
    
    # Aquí podrías enviar un email con el motivo
    # Por ahora solo creamos una notificación en el sistema
    if solicitud.email:
        try:
            system_user = User.objects.get(username='sistema')
            # Intentar encontrar el usuario si ya fue creado
            try:
                usuario = User.objects.get(email=solicitud.email)
                Notificacion.objects.create(
                    usuario=usuario,
                    expediente=None,
                    tipo='solicitud_rechazada',
                    titulo='Solicitud de registro rechazada',
                    mensaje=f'Tu solicitud de registro ha sido rechazada. Motivo: {motivo}',
                    generada_por=system_user,
                    enlace='/register/'
                )
            except User.DoesNotExist:
                # Si el usuario no existe, no podemos crear notificación
                pass
        except User.DoesNotExist:
            pass


@login_required
def gestionar_usuarios(request):
    """Vista para que los administradores gestionen usuarios"""
    if not request.user.perfil.rol.puede_aprobar_usuarios:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('digitalizacion:dashboard')
    
    usuarios = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count()
    }
    return render(request, 'digitalizacion/auth/gestionar_usuarios.html', context)

@login_required
def eliminar_usuario(request, user_id):
    """Vista para eliminar un usuario (solo administradores)"""
    if not request.user.perfil.rol.puede_aprobar_usuarios:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('digitalizacion:dashboard')
    
    try:
        usuario = User.objects.get(pk=user_id, is_active=True)
        
        # No permitir que un administrador se elimine a sí mismo
        if usuario == request.user:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
            return redirect('digitalizacion:gestionar_usuarios')
        
        # Verificar que el usuario a eliminar no sea el superusuario principal
        if usuario.username == 'jacquelinediazdeleon045@gmail.com':
            messages.error(request, 'No se puede eliminar la cuenta principal del administrador.')
            return redirect('digitalizacion:gestionar_usuarios')
        
        if request.method == 'POST':
            # Desactivar el usuario en lugar de eliminarlo
            usuario.is_active = False
            usuario.save()
            
            # Crear notificación
            Notificacion.objects.create(
                usuario=usuario,
                expediente=None,
                tipo='usuario_eliminado',
                titulo='Cuenta Desactivada',
                mensaje=f'Tu cuenta ha sido desactivada por el administrador {request.user.get_full_name()}.',
                generada_por=request.user,
                enlace='/auth/login/'
            )
            
            messages.success(request, f'Usuario {usuario.get_full_name()} ha sido desactivado exitosamente.')
            return redirect('digitalizacion:gestionar_usuarios')
        
        context = {
            'usuario_a_eliminar': usuario
        }
        return render(request, 'digitalizacion/auth/confirmar_eliminar_usuario.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('digitalizacion:gestionar_usuarios')


@login_required
def cambiar_password_usuario(request, user_id):
    """Vista para que los administradores cambien la contraseña de un usuario"""
    if not request.user.perfil.rol.puede_aprobar_usuarios:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('digitalizacion:dashboard')
    
    try:
        usuario = User.objects.get(pk=user_id, is_active=True)
        
        if request.method == 'POST':
            nueva_password = request.POST.get('nueva_password')
            confirmar_password = request.POST.get('confirmar_password')
            
            if not nueva_password:
                messages.error(request, 'La nueva contraseña es requerida.')
                return render(request, 'digitalizacion/auth/cambiar_password_usuario.html', {'usuario': usuario})
            
            if nueva_password != confirmar_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'digitalizacion/auth/cambiar_password_usuario.html', {'usuario': usuario})
            
            if len(nueva_password) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return render(request, 'digitalizacion/auth/cambiar_password_usuario.html', {'usuario': usuario})
            
            # Cambiar la contraseña
            usuario.set_password(nueva_password)
            usuario.save()
            
            # Crear notificación para el usuario
            try:
                system_user = User.objects.get(username='sistema')
                Notificacion.objects.create(
                    usuario=usuario,
                    expediente=None,
                    tipo='password_cambiada',
                    titulo='Contraseña Actualizada',
                    mensaje=f'Tu contraseña ha sido actualizada por el administrador {request.user.get_full_name()}.',
                    generada_por=system_user,
                    enlace='/auth/login/'
                )
            except User.DoesNotExist:
                pass
            
            messages.success(request, f'Contraseña de {usuario.get_full_name()} actualizada exitosamente.')
            return redirect('digitalizacion:gestionar_usuarios')
        
        context = {
            'usuario': usuario
        }
        return render(request, 'digitalizacion/auth/cambiar_password_usuario.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('digitalizacion:gestionar_usuarios')


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
    
    return render(request, 'digitalizacion/auth/cambiar_password_actual.html')


def get_csrf_token(request):
    """Vista para obtener el token CSRF actualizado"""
    return JsonResponse({'csrfToken': get_token(request)})
