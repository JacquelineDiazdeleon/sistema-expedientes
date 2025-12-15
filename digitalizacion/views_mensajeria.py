from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
from .models import Chat, Mensaje, ArchivoAdjunto, Departamento
from .forms import MensajeForm, ChatForm


@login_required
def mensajeria(request):
    """Vista principal de mensajería"""
    # Obtener chats del usuario
    chats_usuario = Chat.objects.filter(
        participantes=request.user,
        activo=True
    ).annotate(
        ultimo_mensaje_fecha=Max('mensajes__fecha_envio')
    ).order_by('-ultimo_mensaje_fecha')
    
    # Agregar conteo de mensajes no leídos a cada chat
    for chat in chats_usuario:
        chat.mensajes_no_leidos_count = chat.get_mensajes_no_leidos(request.user)
    
    # Obtener usuarios disponibles para chat individual
    usuarios_disponibles = User.objects.filter(
        is_active=True
    ).exclude(
        id=request.user.id
    ).order_by('first_name', 'username')
    
    # Obtener departamentos para chats de departamento
    departamentos = Departamento.objects.filter(activo=True)
    
    context = {
        'chats_usuario': chats_usuario,
        'usuarios_disponibles': usuarios_disponibles,
        'departamentos': departamentos,
        'usuario_actual': request.user,
    }
    
    return render(request, 'digitalizacion/mensajeria/mensajeria.html', context)


@login_required
def chat_individual(request, user_id):
    """Vista para chat individual con un usuario"""
    otro_usuario = get_object_or_404(User, id=user_id, is_active=True)
    
    # Buscar chat existente entre estos dos usuarios
    chat = Chat.objects.filter(
        tipo='individual',
        participantes=request.user
    ).filter(
        participantes=otro_usuario
    ).first()
    
    # Si no existe, crear uno nuevo
    if not chat:
        chat = Chat.objects.create(
            tipo='individual',
            creado_por=request.user
        )
        chat.participantes.add(request.user, otro_usuario)
    
    # Obtener mensajes del chat
    mensajes = chat.mensajes.all().order_by('fecha_envio')
    
    # Marcar mensajes como leídos
    for mensaje in mensajes.filter(remitente=otro_usuario, leido=False):
        mensaje.marcar_como_leido(request.user)
    
    context = {
        'chat': chat,
        'mensajes': mensajes,
        'otro_usuario': otro_usuario,
        'usuario_actual': request.user,
    }
    
    return render(request, 'digitalizacion/mensajeria/chat_individual.html', context)


@login_required
def chat_grupo(request, chat_id):
    """Vista para chat de grupo"""
    chat = get_object_or_404(Chat, id=chat_id, participantes=request.user, activo=True)
    
    # Obtener mensajes del chat
    mensajes = chat.mensajes.all().order_by('fecha_envio')
    
    # Marcar mensajes como leídos
    for mensaje in mensajes.filter(remitente__in=chat.participantes.exclude(id=request.user.id), leido=False):
        mensaje.marcar_como_leido(request.user)
    
    context = {
        'chat': chat,
        'mensajes': mensajes,
        'usuario_actual': request.user,
    }
    
    return render(request, 'digitalizacion/mensajeria/chat_grupo.html', context)


@login_required
def crear_chat_grupo(request):
    """Vista para crear un nuevo chat de grupo"""
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.creado_por = request.user
            chat.tipo = 'grupo'
            chat.save()
            
            # Agregar participantes
            participantes = form.cleaned_data.get('participantes', [])
            chat.participantes.add(request.user)
            for participante in participantes:
                chat.participantes.add(participante)
            
            return redirect('digitalizacion:chat_grupo', chat_id=chat.id)
    else:
        form = ChatForm()
    
    context = {
        'form': form,
        'usuarios_disponibles': User.objects.filter(is_active=True).exclude(id=request.user.id),
    }
    
    return render(request, 'digitalizacion/mensajeria/crear_chat_grupo.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def enviar_mensaje(request):
    """API para enviar mensajes"""
    try:
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        contenido = data.get('contenido')
        tipo = data.get('tipo', 'texto')
        icono = data.get('icono')
        
        chat = get_object_or_404(Chat, id=chat_id, participantes=request.user)
        
        mensaje = Mensaje.objects.create(
            chat=chat,
            remitente=request.user,
            contenido=contenido,
            tipo=tipo,
            icono=icono
        )
        
        # Actualizar última actividad del chat
        chat.ultima_actividad = timezone.now()
        chat.save()
        
        return JsonResponse({
            'success': True,
            'mensaje_id': mensaje.id,
            'fecha_envio': mensaje.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'remitente': mensaje.remitente.get_full_name() or mensaje.remitente.username,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def subir_archivo(request):
    """API para subir archivos"""
    try:
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se proporcionó archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        chat_id = request.POST.get('chat_id')
        contenido = request.POST.get('contenido', '')
        
        chat = get_object_or_404(Chat, id=chat_id, participantes=request.user)
        
        # Crear archivo adjunto
        archivo_adjunto = ArchivoAdjunto.objects.create(
            nombre_original=archivo.name,
            nombre_archivo=f"chat_{chat_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}",
            tipo_mime=archivo.content_type,
            tamaño=archivo.size,
            ruta=f"mensajeria/archivos/{archivo.name}",
            usuario=request.user
        )
        
        # Guardar archivo físicamente
        ruta_completa = os.path.join('media', 'mensajeria', 'archivos', archivo_adjunto.nombre_archivo)
        os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
        
        with open(ruta_completa, 'wb+') as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)
        
        # Crear mensaje con archivo
        mensaje = Mensaje.objects.create(
            chat=chat,
            remitente=request.user,
            contenido=contenido or f"Archivo: {archivo.name}",
            tipo='archivo',
            archivo_adjunto=archivo_adjunto
        )
        
        # Actualizar última actividad del chat
        chat.ultima_actividad = timezone.now()
        chat.save()
        
        return JsonResponse({
            'success': True,
            'mensaje_id': mensaje.id,
            'archivo': {
                'nombre': archivo_adjunto.nombre_original,
                'tamaño': archivo_adjunto.get_tamaño_formateado(),
                'tipo': archivo_adjunto.tipo_mime,
                'url': archivo_adjunto.ruta
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def obtener_mensajes(request, chat_id):
    """API para obtener mensajes de un chat"""
    chat = get_object_or_404(Chat, id=chat_id, participantes=request.user)
    
    # Obtener mensajes paginados
    mensajes = chat.mensajes.all().order_by('-fecha_envio')
    paginator = Paginator(mensajes, 50)
    page = request.GET.get('page', 1)
    mensajes_paginados = paginator.get_page(page)
    
    mensajes_data = []
    for mensaje in mensajes_paginados:
        mensaje_data = {
            'id': mensaje.id,
            'contenido': mensaje.contenido,
            'tipo': mensaje.tipo,
            'remitente': mensaje.remitente.get_full_name() or mensaje.remitente.username,
            'fecha_envio': mensaje.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'leido': mensaje.leido,
            'editado': mensaje.editado,
        }
        
        if mensaje.es_archivo():
            mensaje_data['archivo'] = {
                'nombre': mensaje.archivo_adjunto.nombre_original,
                'tamaño': mensaje.archivo_adjunto.get_tamaño_formateado(),
                'tipo': mensaje.archivo_adjunto.tipo_mime,
                'url': mensaje.archivo_adjunto.ruta
            }
        
        if mensaje.es_icono():
            mensaje_data['icono'] = mensaje.icono
        
        mensajes_data.append(mensaje_data)
    
    return JsonResponse({
        'success': True,
        'mensajes': mensajes_data,
        'has_next': mensajes_paginados.has_next(),
        'has_previous': mensajes_paginados.has_previous(),
    })


@login_required
def buscar_usuarios(request):
    """API para buscar usuarios para chat"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'success': False, 'error': 'Búsqueda muy corta'})
    
    usuarios = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query),
        is_active=True
    ).exclude(id=request.user.id)[:10]
    
    usuarios_data = []
    for usuario in usuarios:
        usuarios_data.append({
            'id': usuario.id,
            'nombre': usuario.get_full_name() or usuario.username,
            'username': usuario.username,
            'email': usuario.email,
        })
    
    return JsonResponse({
        'success': True,
        'usuarios': usuarios_data
    })


@login_required
def marcar_leido(request, mensaje_id):
    """API para marcar mensaje como leído"""
    mensaje = get_object_or_404(Mensaje, id=mensaje_id, chat__participantes=request.user)
    mensaje.marcar_como_leido(request.user)
    
    return JsonResponse({'success': True})


@login_required
def eliminar_mensaje(request, mensaje_id):
    """API para eliminar mensaje (solo el propio)"""
    mensaje = get_object_or_404(Mensaje, id=mensaje_id, remitente=request.user)
    mensaje.delete()
    
    return JsonResponse({'success': True})


@login_required
def editar_mensaje(request, mensaje_id):
    """API para editar mensaje (solo el propio)"""
    if request.method == 'POST':
        mensaje = get_object_or_404(Mensaje, id=mensaje_id, remitente=request.user)
        nuevo_contenido = request.POST.get('contenido')
        
        if nuevo_contenido and nuevo_contenido.strip():
            mensaje.contenido = nuevo_contenido.strip()
            mensaje.editado = True
            mensaje.fecha_edicion = timezone.now()
            mensaje.save()
            
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
