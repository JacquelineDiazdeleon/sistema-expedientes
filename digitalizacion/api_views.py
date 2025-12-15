"""
Vistas de la API para el manejo de documentos
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
import os
from datetime import datetime
from .models import Documento, Departamento as Area, Expediente
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Importaciones para el nuevo endpoint de escáner
try:
    from .models import DocumentoExpediente, AreaTipoExpediente, HistorialExpediente
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
except ImportError:
    pass

@csrf_exempt
@require_http_methods(["POST"])
def subir_documento_api(request):
    """
    Vista para subir documentos a través de la API
    """
    try:
        # Obtener datos del formulario
        archivo = request.FILES.get('archivo')
        area_id = request.POST.get('area_id')
        expediente_id = request.POST.get('expediente_id')
        
        # Validaciones básicas
        if not archivo:
            return JsonResponse({'error': 'No se proporcionó ningún archivo'}, status=400)
            
        if not area_id:
            return JsonResponse({'error': 'ID de área no proporcionado'}, status=400)
            
        # Verificar que el área existe
        area = get_object_or_404(Area, id=area_id)
        
        # Si se proporciona un expediente_id, verificar que existe
        expediente = None
        if expediente_id:
            expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Crear directorio si no existe
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documentos', area_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        nombre_archivo = f"{timestamp}_{archivo.name}"
        file_path = os.path.join(upload_dir, nombre_archivo)
        
        # Guardar el archivo
        with open(file_path, 'wb+') as destination:
            for chunk in archivo.chunks():
                destination.write(chunk)
        
        # Crear el registro en la base de datos
        documento = Documento.objects.create(
            archivo=os.path.join('documentos', area_id, nombre_archivo),
            nombre=archivo.name,
            tipo_contenido=archivo.content_type,
            tamano=archivo.size,
            area=area,
            expediente=expediente,
            subido_por=request.user if request.user.is_authenticated else None
        )
        
        # Devolver respuesta exitosa
        return JsonResponse({
            'success': True,
            'documento': {
                'id': documento.id,
                'nombre': documento.nombre,
                'url': documento.archivo.url if documento.archivo else '',
                'fecha_subida': documento.fecha_subida.isoformat(),
                'tamano': documento.tamano
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al procesar el archivo: {str(e)}'
        }, status=500)


# ============================================================================
# ENDPOINT PARA ESCÁNER LOCAL (Servicio NAPS2)
# ============================================================================

# Token de autenticación para el servicio local
# IMPORTANTE: Cambia este token por uno seguro y configúralo también en scan_service.py
INTERNAL_UPLOAD_TOKEN = os.environ.get('SCANNER_UPLOAD_TOKEN', 'CAMBIA_POR_TU_TOKEN_SECRETO_AQUI')


@csrf_exempt
@require_http_methods(["POST"])
def subir_documento_escaneado_api(request):
    """
    Endpoint API que recibe el PDF escaneado desde el servicio local (NAPS2).
    
    Requiere cabecera: Authorization: Bearer <TOKEN>
    
    Espera multipart form-data con:
      - archivo (file) - El PDF escaneado
      - nombre_documento (string) - Nombre del documento
      - descripcion (string, opcional) - Descripción del documento
      - area (int) - ID del área
      - expediente (int) - ID del expediente
    
    Este endpoint es llamado por el servicio local scan_service.py después de escanear.
    """
    try:
        # Autenticación simple por token (servicio local)
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Bearer "):
            logger.warning("Intento de acceso sin token Bearer")
            return JsonResponse({"success": False, "error": "Unauthorized - missing token"}, status=401)
        
        token = auth.split(" ", 1)[1].strip()
        if token != INTERNAL_UPLOAD_TOKEN:
            logger.warning(f"Intento de acceso con token inválido")
            return JsonResponse({"success": False, "error": "Unauthorized - invalid token"}, status=401)
        
        # Obtener campos del formulario
        archivo = request.FILES.get("archivo")
        nombre_documento = request.POST.get("nombre_documento", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        area_id = request.POST.get("area")
        expediente_id = request.POST.get("expediente")
        
        # Validaciones básicas
        if not archivo:
            return JsonResponse({"success": False, "error": "No se proporcionó ningún archivo"}, status=400)
        
        if not nombre_documento:
            return JsonResponse({"success": False, "error": "Falta el nombre del documento"}, status=400)
        
        if not area_id:
            return JsonResponse({"success": False, "error": "Falta el ID del área"}, status=400)
        
        if not expediente_id:
            return JsonResponse({"success": False, "error": "Falta el ID del expediente"}, status=400)
        
        # Validar que el área existe y está activa
        try:
            area = AreaTipoExpediente.objects.get(id=int(area_id), activa=True)
        except AreaTipoExpediente.DoesNotExist:
            return JsonResponse({"success": False, "error": f"Área con ID {area_id} no existe o no está activa"}, status=400)
        except ValueError:
            return JsonResponse({"success": False, "error": "ID de área inválido"}, status=400)
        
        # Validar que el expediente existe
        try:
            expediente = Expediente.objects.get(id=int(expediente_id))
        except Expediente.DoesNotExist:
            return JsonResponse({"success": False, "error": f"Expediente con ID {expediente_id} no existe"}, status=400)
        except ValueError:
            return JsonResponse({"success": False, "error": "ID de expediente inválido"}, status=400)
        
        # Obtener o crear usuario para el servicio local
        # Si no existe, creamos uno llamado 'servicio_local' para auditoría
        try:
            servicio_user = User.objects.get(username='servicio_local')
        except User.DoesNotExist:
            # Crear usuario del servicio si no existe
            servicio_user = User.objects.create_user(
                username='servicio_local',
                email='servicio@local',
                first_name='Servicio',
                last_name='Escáner Local',
                is_active=True,
                is_staff=False
            )
            logger.info("Usuario 'servicio_local' creado automáticamente")
        
        # Guardar archivo usando el storage configurado
        try:
            # Generar nombre seguro para el archivo
            fs_name, ext = os.path.splitext(archivo.name)
            if not ext:
                ext = '.pdf'  # Por defecto PDF si no tiene extensión
            
            timestamp = int(timezone.now().timestamp())
            safe_filename = f"{slugify(fs_name)}_{timestamp}{ext}"
            
            # Usar el mismo patrón de guardado que el resto del sistema
            upload_path = f'expedientes/{expediente_id}/documentos/{safe_filename}'
            
            # Leer el contenido del archivo
            archivo_content = archivo.read()
            
            # Guardar usando default_storage
            saved_path = default_storage.save(upload_path, ContentFile(archivo_content))
            
            # Determinar tipo de archivo
            tipo_archivo = ext.lower().lstrip('.')
            if archivo.content_type:
                tipo_archivo = archivo.content_type
            
            # Obtener la etapa del expediente
            etapa = expediente.estado if hasattr(expediente, 'estado') else expediente.estado_actual
            
            # Crear el documento en la base de datos
            documento = DocumentoExpediente(
                nombre_documento=nombre_documento,
                descripcion=descripcion or f'Documento escaneado para el área {area.titulo}',
                archivo=saved_path,
                tipo_archivo=tipo_archivo,
                subido_por=servicio_user,
                area=area,
                expediente=expediente,
                etapa=etapa,
                tamano_archivo=len(archivo_content),
                validado=False
            )
            
            documento.save()
            
            # Registrar en el historial
            HistorialExpediente.objects.create(
                expediente=expediente,
                usuario=servicio_user,
                accion='Carga por escáner automático',
                descripcion=f'Se subió el documento escaneado: {nombre_documento} (Área: {area.titulo})',
                estado_anterior=expediente.estado_actual,
                estado_nuevo=expediente.estado_actual
            )
            
            logger.info(f"Documento escaneado guardado: {documento.id} - {nombre_documento} - Expediente: {expediente_id} - Área: {area_id}")
            
            return JsonResponse({
                "success": True, 
                "documento_id": documento.id, 
                "path": saved_path,
                "nombre": nombre_documento,
                "expediente_id": expediente.id,
                "area_id": area.id
            })
            
        except Exception as e:
            logger.error(f"Error al guardar documento escaneado: {str(e)}", exc_info=True)
            return JsonResponse({"success": False, "error": f"Error al guardar el documento: {str(e)}"}, status=500)
        
    except Exception as e:
        logger.error(f"Error en subir_documento_escaneado_api: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": f"Error inesperado: {str(e)}"}, status=500)
