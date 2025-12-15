# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.text import slugify
import os

from .models import AreaTipoExpediente, DocumentoExpediente, HistorialExpediente, TipoDocumento, Expediente

@login_required
def subir_documento(request):
    """
    Vista para subir un documento independiente (no asociado a un expediente)
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_documento = request.POST.get('nombre_documento', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            area_id = request.POST.get('area')
            expediente_id = request.POST.get('expediente')
            archivo = request.FILES.get('archivo')
            
            # Validaciones básicas
            if not nombre_documento or not archivo or not area_id or not expediente_id:
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return redirect('digitalizacion:subir_documento')
            
            # Verificar que el área existe y está activa
            try:
                area = AreaTipoExpediente.objects.get(id=area_id, activa=True)
            except AreaTipoExpediente.DoesNotExist:
                messages.error(request, 'El área seleccionada no es válida.')
                return redirect('digitalizacion:subir_documento')
            
            # Verificar que el expediente existe
            try:
                expediente = Expediente.objects.get(id=expediente_id)  # type: ignore
            except Expediente.DoesNotExist:  # type: ignore
                messages.error(request, 'El expediente seleccionado no es válido.')
                return redirect('digitalizacion:subir_documento')
            
            # Procesar el archivo
            fs = FileSystemStorage()
            filename, ext = os.path.splitext(archivo.name)
            safe_filename = f"{slugify(filename)}_{int(timezone.now().timestamp())}{ext}"
            filename = fs.save(f'documentos/{safe_filename}', archivo)
            
            # Obtener el tipo de archivo
            tipo_archivo = ext.lower().lstrip('.') if ext else ''
            
            # Crear el documento
            documento = DocumentoExpediente(
                nombre_documento=nombre_documento,
                descripcion=descripcion,
                archivo=filename,
                tipo_archivo=tipo_archivo,
                subido_por=request.user,
                area=area,
                expediente=expediente,
                etapa=expediente.estado,
                tamano_archivo=archivo.size
            )
            documento.save()

            # Registrar en el historial
            HistorialExpediente.objects.create(
                expediente=documento.expediente,
                usuario=request.user,
                accion='Subida de documento',
                descripcion=f'Se subió el documento: {documento.nombre_documento}'
            )

            messages.success(request, 'Documento subido exitosamente.')
            return redirect('digitalizacion:buscar_documentos')

        except Exception as e:
            messages.error(request, f'Error al subir el documento: {str(e)}')
            return redirect('digitalizacion:subir_documento')

    # Si es GET, mostrar el formulario
    from .models import Expediente
    areas = AreaTipoExpediente.objects.filter(activa=True).order_by('titulo')
    expedientes = Expediente.objects.all().order_by('-fecha_creacion')[:50]
    
    context = {
        'areas': areas,
        'expedientes': expedientes,
        'titulo_pagina': 'Subir Documento',
    }
    return render(request, 'digitalizacion/documentos/subir_documento.html', context)


@login_required
def ver_documento(request, documento_id):
    """
    Vista para ver los detalles de un documento
    """
    try:
        # Obtener el documento o devolver 404 si no existe
        documento = get_object_or_404(
            DocumentoExpediente.objects.select_related('subido_por', 'area', 'expediente'),
            id=documento_id
        )
        
        # Verificar permisos (solo el usuario que subió el documento o superusuarios pueden verlo)
        if not (documento.subido_por == request.user or request.user.is_superuser):
            messages.error(request, 'No tienes permiso para ver este documento.')
            return redirect('digitalizacion:dashboard')
        
        # Obtener información adicional si es necesario
        historial = []
        if documento.expediente:
            historial = HistorialExpediente.objects.filter(
                expediente=documento.expediente,
                descripcion__icontains=documento.nombre_documento
            ).order_by('-fecha')[:10]  # Últimos 10 registros de historial
        
        context = {
            'documento': documento,
            'historial': historial,
            'titulo_pagina': f'Documento: {documento.nombre_documento}'
        }
        
        return render(request, 'digitalizacion/documentos/ver_documento.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el documento: {str(e)}')
        return redirect('digitalizacion:buscar_documentos')


@login_required
def editar_documento(request, documento_id):
    """
    Vista para editar los detalles de un documento existente
    """
    try:
        # Obtener el documento o devolver 404 si no existe
        documento = get_object_or_404(
            DocumentoExpediente.objects.select_related('subido_por', 'area', 'expediente'),
            id=documento_id
        )
        
        # Verificar permisos (solo el usuario que subió el documento o superusuarios pueden editarlo)
        if not (documento.subido_por == request.user or request.user.is_superuser):
            messages.error(request, 'No tienes permiso para editar este documento.')
            return redirect('digitalizacion:ver_documento', documento_id=documento_id)
        
        if request.method == 'POST':
            try:
                # Procesar el formulario de edición
                nombre_documento = request.POST.get('nombre_documento', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
                archivo_nuevo = request.FILES.get('archivo')
                
                # Validaciones básicas
                if not nombre_documento:
                    messages.error(request, 'El nombre del documento es obligatorio.')
                    return redirect('digitalizacion:editar_documento', documento_id=documento_id)
                
                # Actualizar los campos del documento
                documento.nombre_documento = nombre_documento
                documento.descripcion = descripcion
                
                # Si se subió un nuevo archivo, reemplazar el existente
                if archivo_nuevo:
                    # Eliminar el archivo anterior si existe
                    if documento.archivo and os.path.isfile(documento.archivo.path):
                        os.remove(documento.archivo.path)
                    
                    # Guardar el nuevo archivo
                    fs = FileSystemStorage()
                    filename, ext = os.path.splitext(archivo_nuevo.name)
                    safe_filename = f"{slugify(filename)}_{int(timezone.now().timestamp())}{ext}"
                    filename = fs.save(f'documentos/{safe_filename}', archivo_nuevo)
                    documento.archivo = filename
                    documento.tamano_archivo = archivo_nuevo.size
                
                # Guardar los cambios
                documento.save()
                
                # Registrar en el historial si el documento tiene expediente
                if documento.expediente:
                    HistorialExpediente.objects.create(
                        expediente=documento.expediente,
                        usuario=request.user,
                        accion='Edición de documento',
                        descripcion=f'Se editó el documento: {documento.nombre_documento}'
                    )
                
                messages.success(request, 'Documento actualizado exitosamente.')
                return redirect('digitalizacion:ver_documento', documento_id=documento_id)
                
            except Exception as e:
                messages.error(request, f'Error al actualizar el documento: {str(e)}')
                return redirect('digitalizacion:editar_documento', documento_id=documento_id)
        
        # Si es GET, mostrar el formulario de edición
        tipos_documento = TipoDocumento.objects.filter(activo=True).order_by('nombre')
        
        context = {
            'documento': documento,
            'titulo_pagina': f'Editar Documento: {documento.nombre_documento}'
        }
        
        return render(request, 'digitalizacion/documentos/editar_documento.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el documento para edición: {str(e)}')
        return redirect('digitalizacion:buscar_documentos')


@login_required
def eliminar_documento(request, documento_id):
    """
    Vista para eliminar un documento existente
    """
    # Verificar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        # Obtener el documento o devolver 404 si no existe
        try:
            documento = DocumentoExpediente.objects.select_related('subido_por').get(id=documento_id)
        except DocumentoExpediente.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False, 
                    'error': 'El documento no existe o ya ha sido eliminado.'
                }, status=404)
            messages.error(request, 'El documento no existe o ya ha sido eliminado.')
            return redirect('digitalizacion:buscar_documentos')
        
        # Verificar permisos (solo el usuario que subió el documento o superusuarios pueden eliminarlo)
        if not (documento.subido_por == request.user or request.user.is_superuser):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'No tienes permiso para eliminar este documento.'}, status=403)
            messages.error(request, 'No tienes permiso para eliminar este documento.')
            return redirect('digitalizacion:ver_documento', documento_id=documento_id)
        
        if request.method == 'POST':
            try:
                # Guardar información para el historial antes de eliminar
                titulo_documento = documento.nombre_documento
                
                # Eliminar el archivo físico si existe
                if documento.archivo and os.path.isfile(documento.archivo.path):
                    try:
                        os.remove(documento.archivo.path)
                    except Exception as e:
                        error_msg = f"Error al eliminar el archivo físico: {str(e)}"
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'error': error_msg}, status=500)
                        messages.error(request, error_msg)
                        return redirect('digitalizacion:ver_documento', documento_id=documento_id)
                
                # Registrar en el historial antes de eliminar
                from .models import HistorialExpediente
                # Si el documento está asociado a un expediente, creamos el registro de historial
                expediente_ref = documento.expediente if hasattr(documento, 'expediente') else None
                if expediente_ref:
                    HistorialExpediente.objects.create(
                        expediente=expediente_ref,
                        usuario=request.user,
                        accion='Eliminación de documento',
                        descripcion=f'Se eliminó el documento: {titulo_documento}'
                    )
                
                # Eliminar el documento de la base de datos
                documento.delete()
                
                # Actualizar el progreso y estado del expediente
                # Esto automáticamente cambiará el estado de 'completo' a 'en_proceso' si el progreso baja del 100%
                if expediente_ref:
                    expediente_ref.actualizar_progreso()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': 'Documento eliminado exitosamente.'
                    })
                    
                messages.success(request, 'Documento eliminado exitosamente.')
                return redirect('digitalizacion:buscar_documentos')
                
            except Exception as e:
                error_msg = f'Error al eliminar el documento: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg}, status=500)
                messages.error(request, error_msg)
                return redirect('digitalizacion:ver_documento', documento_id=documento_id)
        
        # Si es GET y es una petición AJAX, devolver error de método no permitido
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': 'Método no permitido. Se requiere una petición POST.'
            }, status=405)
            
        # Si es GET normal, mostrar la página de confirmación
        context = {
            'documento': documento,
            'titulo_pagina': f'Eliminar Documento: {documento.nombre_documento}'
        }
        
        return render(request, 'digitalizacion/documentos/confirmar_eliminar_documento.html', context)
        
    except Exception as e:
        error_msg = f'Error al procesar la solicitud: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect('digitalizacion:buscar_documentos')


@login_required
def descargar_documento(request, documento_id):
    """
    Vista para descargar un documento
    """
    try:
        # Obtener el documento o devolver 404 si no existe
        documento = get_object_or_404(
            DocumentoExpediente.objects.select_related('subido_por'),
            id=documento_id
        )
        
        # Verificar permisos (solo el usuario que subió el documento o superusuarios pueden descargarlo)
        if not (documento.subido_por == request.user or request.user.is_superuser):
            messages.error(request, 'No tienes permiso para descargar este documento.')
            return redirect('digitalizacion:ver_documento', documento_id=documento_id)
        
        # Verificar que el archivo existe
        if not documento.archivo or not os.path.isfile(documento.archivo.path):
            messages.error(request, 'El archivo solicitado no existe.')
            return redirect('digitalizacion:ver_documento', documento_id=documento_id)
        
        try:
            # Obtener la extensión del archivo
            _, ext = os.path.splitext(documento.archivo.name)
            # Generar un nombre de archivo seguro para la descarga
            safe_filename = f"{slugify(documento.nombre_documento)}{ext}"
            
            # Registrar la descarga en el historial si el documento tiene expediente
            if documento.expediente:
                HistorialExpediente.objects.create(
                    expediente=documento.expediente,
                    usuario=request.user,
                    accion='Descarga de documento',
                    descripcion=f'Se descargó el documento: {documento.nombre_documento}'
                )
            
            # Usar FileResponse para manejar eficientemente archivos grandes
            response = FileResponse(open(documento.archivo.path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
            return response
                
        except Exception as e:
            messages.error(request, f'Error al preparar el archivo para descarga: {str(e)}')
            return redirect('digitalizacion:ver_documento', documento_id=documento_id)
            
    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud de descarga: {str(e)}')
        return redirect('digitalizacion:buscar_documentos')
