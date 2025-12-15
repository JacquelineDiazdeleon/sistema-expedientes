from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views, authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Documento, TipoDocumento, Departamento, HistorialDocumento
from .forms import DocumentoForm, TipoDocumentoForm, DepartamentoForm
import json


def dashboard(request):
    """Vista principal del dashboard - redirige al nuevo sistema de expedientes"""
    return redirect('expedientes:dashboard')


def lista_documentos(request):
    """Vista para listar documentos con filtros"""
    documentos = Documento.objects.all()
    
    # Filtros
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    departamento = request.GET.get('departamento')
    busqueda = request.GET.get('q')
    
    if estado:
        documentos = documentos.filter(estado=estado)
    
    if tipo:
        documentos = documentos.filter(tipo_documento_id=tipo)
    
    if departamento:
        documentos = documentos.filter(departamento_id=departamento)
    
    if busqueda:
        documentos = documentos.filter(
            Q(titulo__icontains=busqueda) |
            Q(numero_documento__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(palabras_clave__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(documentos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    tipos_documento = TipoDocumento.objects.filter(activo=True)
    departamentos = Departamento.objects.filter(activo=True)
    estados = Documento.ESTADO_CHOICES
    
    context = {
        'page_obj': page_obj,
        'tipos_documento': tipos_documento,
        'departamentos': departamentos,
        'estados': estados,
        'filtros_actuales': {
            'estado': estado,
            'tipo': tipo,
            'departamento': departamento,
            'busqueda': busqueda,
        }
    }
    
    return render(request, 'digitalizacion/lista_documentos.html', context)


def crear_documento(request):
    """Vista para crear un nuevo documento"""
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            if request.user.is_authenticated:
                documento.creado_por = request.user
            else:
                # Usuario por defecto para demo
                from django.contrib.auth.models import User
                usuario_demo, created = User.objects.get_or_create(
                    username='demo',
                    defaults={'first_name': 'Usuario', 'last_name': 'Demo'}
                )
                documento.creado_por = usuario_demo
            documento.save()
            
            # Crear entrada en el historial
            # Obtener usuario actual o demo
            usuario_actual = request.user if request.user.is_authenticated else documento.creado_por
            
            HistorialDocumento.objects.create(
                documento=documento,
                usuario=usuario_actual,
                accion='Creación',
                descripcion='Documento creado en el sistema',
                estado_nuevo=documento.estado
            )
            
            messages.success(request, 'Documento creado exitosamente.')
            return redirect('digitalizacion:detalle_documento', pk=documento.pk)
    else:
        form = DocumentoForm()
    
    return render(request, 'digitalizacion/crear_documento.html', {'form': form})


def detalle_documento(request, pk):
    """Vista para mostrar los detalles de un documento"""
    documento = get_object_or_404(Documento, pk=pk)
    historial = documento.historial.all()[:10]  # Últimos 10 registros
    
    context = {
        'documento': documento,
        'historial': historial,
    }
    
    return render(request, 'digitalizacion/detalle_documento.html', context)


def editar_documento(request, pk):
    """Vista para editar un documento existente"""
    documento = get_object_or_404(Documento, pk=pk)
    estado_anterior = documento.estado
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            documento = form.save()
            
            # Crear entrada en el historial si cambió el estado
            if estado_anterior != documento.estado:
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    accion='Cambio de estado',
                    descripcion=f'Estado cambiado de {estado_anterior} a {documento.estado}',
                    estado_anterior=estado_anterior,
                    estado_nuevo=documento.estado
                )
            else:
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    accion='Actualización',
                    descripcion='Documento actualizado',
                    estado_nuevo=documento.estado
                )
            
            messages.success(request, 'Documento actualizado exitosamente.')
            return redirect('digitalizacion:detalle_documento', pk=documento.pk)
    else:
        form = DocumentoForm(instance=documento)
    
    context = {
        'form': form,
        'documento': documento,
    }
    
    return render(request, 'digitalizacion/editar_documento.html', context)



def eliminar_documento(request, pk):
    """Vista para eliminar un documento"""
    documento = get_object_or_404(Documento, pk=pk)
    
    if request.method == 'POST':
        # Crear entrada en el historial antes de eliminar
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            accion='Eliminación',
            descripcion='Documento eliminado del sistema',
            estado_anterior=documento.estado
        )
        
        documento.delete()
        messages.success(request, 'Documento eliminado exitosamente.')
        return redirect('digitalizacion:lista_documentos')
    
    return render(request, 'digitalizacion/eliminar_documento.html', {'documento': documento})



def digitalizar_documento(request, pk):
    """Vista para marcar un documento como digitalizado"""
    documento = get_object_or_404(Documento, pk=pk)
    estado_anterior = documento.estado
    
    if request.method == 'POST':
        documento.estado = 'digitalizado'
        documento.digitalizado_por = request.user
        documento.fecha_digitalizacion = timezone.now()
        documento.save()
        
        # Crear entrada en el historial
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            accion='Digitalización',
            descripcion='Documento digitalizado',
            estado_anterior=estado_anterior,
            estado_nuevo='digitalizado'
        )
        
        messages.success(request, 'Documento marcado como digitalizado.')
        return redirect('digitalizacion:detalle_documento', pk=documento.pk)
    
    return render(request, 'digitalizacion/digitalizar_documento.html', {'documento': documento})



def verificar_documento(request, pk):
    """Vista para verificar un documento digitalizado"""
    documento = get_object_or_404(Documento, pk=pk)
    estado_anterior = documento.estado
    
    if request.method == 'POST':
        documento.estado = 'verificado'
        documento.verificado_por = request.user
        documento.save()
        
        # Crear entrada en el historial
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            accion='Verificación',
            descripcion='Documento verificado',
            estado_anterior=estado_anterior,
            estado_nuevo='verificado'
        )
        
        messages.success(request, 'Documento verificado exitosamente.')
        return redirect('digitalizacion:detalle_documento', pk=documento.pk)
    
    return render(request, 'digitalizacion/verificar_documento.html', {'documento': documento})


def buscar_documentos(request):
    """Vista para búsqueda avanzada de documentos"""
    # Implementar lógica de búsqueda avanzada
    return render(request, 'digitalizacion/buscar_documentos.html')



def reportes(request):
    """Vista para mostrar reportes del sistema"""
    # Implementar lógica de reportes
    return render(request, 'digitalizacion/reportes.html')



def exportar_reporte(request):
    """Vista para exportar reportes"""
    # Implementar lógica de exportación
    return HttpResponse("Función de exportación en desarrollo")



def configuracion(request):
    """Vista para configuración del sistema"""
    return render(request, 'digitalizacion/configuracion.html')



def gestionar_tipos_documento(request):
    """Vista para gestionar tipos de documento"""
    tipos = TipoDocumento.objects.all()
    
    if request.method == 'POST':
        form = TipoDocumentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de documento creado exitosamente.')
            return redirect('digitalizacion:tipos_documento')
    else:
        form = TipoDocumentoForm()
    
    context = {
        'tipos': tipos,
        'form': form,
    }
    
    return render(request, 'digitalizacion/gestionar_tipos_documento.html', context)



def gestionar_departamentos(request):
    """Vista para gestionar departamentos"""
    departamentos = Departamento.objects.all()
    
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento creado exitosamente.')
            return redirect('digitalizacion:departamentos')
    else:
        form = DepartamentoForm()
    
    context = {
        'departamentos': departamentos,
        'form': form,
    }
    
    return render(request, 'digitalizacion/gestionar_departamentos.html', context)


# API Views

def api_documentos(request):
    """API para obtener documentos en formato JSON"""
    documentos = Documento.objects.all()
    data = []
    
    for doc in documentos:
        data.append({
            'id': doc.id,
            'numero_documento': doc.numero_documento,
            'titulo': doc.titulo,
            'estado': doc.get_estado_display(),
            'fecha_creacion': doc.fecha_creacion.isoformat(),
        })
    
    return JsonResponse({'documentos': data})



def api_estadisticas(request):
    """API para obtener estadísticas del sistema"""
    estadisticas = {
        'total_documentos': Documento.objects.count(),
        'documentos_por_estado': dict(
            Documento.objects.values('estado').annotate(
                total=Count('estado')
            ).values_list('estado', 'total')
        ),
        'documentos_por_tipo': dict(
            Documento.objects.values('tipo_documento__nombre').annotate(
                total=Count('tipo_documento')
            ).values_list('tipo_documento__nombre', 'total')
        ),
    }
    
    return JsonResponse(estadisticas)


# ============================================
# VISTAS DE AUTENTICACIÓN SIMPLES
# ============================================

def user_login(request):
    """Vista simple para login"""
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                return redirect('expedientes:dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'digitalizacion/auth/login.html', {'form': form})


def user_register(request):
    """Vista simple para registro"""
    if request.method == 'POST':
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('digitalizacion:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'digitalizacion/auth/register.html', {'form': form})


def user_logout(request):
    """Vista simple para logout"""
    user_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else "Usuario"
    logout(request)
    messages.success(request, f'¡Hasta luego, {user_name}! Has cerrado sesión exitosamente.')
    return redirect('digitalizacion:login')


@login_required
def user_profile(request):
    """Vista simple de perfil"""
    from .models import Expediente
    
    user = request.user
    total_expedientes = Expediente.objects.filter(creado_por=user).count()
    expedientes_completados = Expediente.objects.filter(creado_por=user, estado_actual='PAGO').count()
    
    context = {
        'user': user,
        'total_expedientes': total_expedientes,
        'expedientes_completados': expedientes_completados,
    }
    return render(request, 'digitalizacion/auth/profile.html', context)