from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.db.models import Count, Q, F, ExpressionWrapper, fields, Avg
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.contrib import messages
from django.contrib.auth import views as auth_views, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse_lazy
import os
import json
import logging
from pathlib import Path
from .models import (
    Departamento, Expediente, 
    EtapaExpediente, DocumentoExpediente, NotaExpediente,
    Notificacion, ComentarioArea, SolicitudRegistro, RolUsuario,
    MensajeExpediente, User, TipoDocumento, HistorialExpediente,
    UserSession, AreaTipoExpediente, ValorAreaExpediente
)
from .search_utils import search_documents, index_document, remove_document

logger = logging.getLogger(__name__)

@login_required
def buscar_documentos(request):
    """Vista para la página de búsqueda de documentos"""
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    expediente_id = request.GET.get('expediente_id')
    
    # Obtener el expediente si se especificó un ID
    expediente = None
    if expediente_id:
        try:
            expediente = Expediente.objects.get(id=expediente_id)
        except Expediente.DoesNotExist:
            pass
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return api_buscar_documentos(request)
    
    # Obtener los expedientes para el filtro (aumentar límite para mejor búsqueda)
    expedientes = Expediente.objects.all().order_by('-fecha_creacion')[:200]
    
    return render(request, 'digitalizacion/buscar.html', {
        'query': query,
        'tipo': tipo,
        'expediente_actual': expediente,
        'expedientes': expedientes,
        'tipos_documento': ['todos', 'pdf', 'docx', 'doc', 'xls', 'xlsx', 'jpg', 'png'],
    })

@login_required
def api_buscar_documentos(request):
    """API para realizar búsquedas de documentos con información completa"""
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    expediente_id = request.GET.get('expediente_id')
    page = int(request.GET.get('page', 1))
    
    # Validar que haya una consulta
    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Por favor ingresa un término de búsqueda',
            'resultados': {
                'items': [],
                'total': 0,
                'page': 1,
                'total_paginas': 0
            }
        })
    
    # Realizar la búsqueda
    try:
        results = search_documents(
            query=query,
            expediente_id=expediente_id,
            page=page,
            limit=20
        )
    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error al realizar la búsqueda: {str(e)}',
            'resultados': {
                'items': [],
                'total': 0,
                'page': 1,
                'total_paginas': 0
            }
        }, status=500)
    
    # Si hay un error en la búsqueda
    if 'error' in results:
        return JsonResponse({
            'success': False,
            'error': results.get('error', 'Error desconocido'),
            'resultados': {
                'items': [],
                'total': 0,
                'page': page,
                'total_paginas': 0
            }
        }, status=500)
    
    # Obtener los IDs de los documentos para obtener más información de la base de datos
    doc_ids = []
    for r in results.get('results', []):
        try:
            doc_id = int(r.get('id', 0))
            if doc_id > 0:
                doc_ids.append(doc_id)
        except (ValueError, TypeError):
            continue
    
    if not doc_ids:
        return JsonResponse({
            'success': True,
            'resultados': {
                'items': [],
                'total': 0,
                'page': page,
                'total_paginas': 0
            }
        })
    
    # Obtener los documentos con toda la información relacionada
    # IMPORTANTE: Filtrar solo documentos que tienen archivo y expediente válido
    # Además, verificar que el expediente tenga al menos un documento
    documentos = DocumentoExpediente.objects.filter(
        id__in=doc_ids,
        archivo__isnull=False,  # Solo documentos con archivo
        expediente__isnull=False,  # Solo documentos con expediente válido
        expediente__documentos__isnull=False  # Asegurar que el expediente tenga documentos
    ).select_related(
        'expediente',
        'subido_por',
        'area'
    ).prefetch_related('expediente__creado_por').distinct()
    
    # Aplicar filtro de tipo si es necesario
    if tipo != 'todos':
        documentos = documentos.filter(tipo_archivo__icontains=tipo)
    
    # Validar que los archivos existan físicamente y crear diccionario
    import os
    from django.conf import settings
    documentos_dict = {}
    documentos_validos = []
    expedientes_con_documentos = set()
    
    for doc in documentos:
        try:
            # Validar que el expediente existe y tiene documentos
            if not doc.expediente:
                logger.warning(f"Documento {doc.id} no tiene expediente asociado")
                continue
            
            # Verificar que el expediente tenga al menos este documento
            if not DocumentoExpediente.objects.filter(
                expediente=doc.expediente,
                archivo__isnull=False
            ).exists():
                logger.warning(f"Expediente {doc.expediente.id} no tiene documentos válidos")
                continue
            
            # Verificar que el archivo existe físicamente
            file_path = None
            file_exists = False
            
            if doc.archivo:
                if hasattr(doc.archivo, 'path'):
                    file_path = doc.archivo.path
                    file_exists = os.path.exists(file_path)
                else:
                    # Si tiene archivo pero no tiene path, verificar con name
                    file_name = doc.archivo.name
                    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                    file_exists = os.path.exists(file_path)
            
            if file_exists and file_path:
                documentos_dict[doc.id] = doc
                documentos_validos.append(doc.id)
                expedientes_con_documentos.add(doc.expediente.id)
                logger.debug(f"Documento {doc.id} validado correctamente: {file_path}")
            else:
                logger.warning(f"Archivo no encontrado para documento {doc.id}: {file_path}")
        except Exception as e:
            logger.error(f"Error validando documento {doc.id}: {str(e)}", exc_info=True)
            continue
    
    # Si no hay documentos válidos, retornar vacío
    if not documentos_dict:
        logger.info(f"No se encontraron documentos válidos para la búsqueda: '{query}'")
        return JsonResponse({
            'success': True,
            'resultados': {
                'items': [],
                'total': 0,
                'page': page,
                'total_paginas': 0
            }
        })
    
    # Filtrar resultados del índice para incluir solo documentos válidos
    resultados_filtrados = [
        r for r in results.get('results', [])
        if int(r.get('id', 0)) in documentos_validos
    ]
    
    # Formatear resultados con información completa
    formatted_results = []
    for result in resultados_filtrados:
        try:
            doc_id = int(result.get('id', 0))
            if doc_id not in documentos_dict:
                continue
                
            doc = documentos_dict[doc_id]
            
            # Validar que el expediente existe y tiene documentos
            if not doc.expediente:
                logger.warning(f"Documento {doc_id} no tiene expediente asociado")
                continue
            
            expediente = doc.expediente
            
            # Verificación adicional: asegurar que el expediente tenga documentos
            if not DocumentoExpediente.objects.filter(
                expediente=expediente,
                archivo__isnull=False
            ).exists():
                logger.warning(f"Expediente {expediente.id} no tiene documentos válidos, omitiendo")
                continue
            
            # Obtener información del usuario que subió el documento
            usuario_nombre = 'Usuario desconocido'
            if doc.subido_por:
                usuario_nombre = doc.subido_por.get_full_name() or doc.subido_por.username
            
            # Obtener información del área - siempre intentar obtener el área exacta
            area_nombre = 'No especificada'
            if doc.area:
                # Si el documento tiene área asignada directamente, usarla
                area_nombre = doc.area.titulo
            else:
                # Si no tiene área asignada, intentar encontrarla por etapa y tipo de expediente
                try:
                    from .models import AreaTipoExpediente
                    # Buscar área que coincida con la etapa del documento y el tipo de expediente
                    area_encontrada = AreaTipoExpediente.objects.filter(
                        nombre=doc.etapa,
                        tipo_expediente=expediente.tipo_expediente,
                        activa=True
                    ).first()
                    
                    if area_encontrada:
                        area_nombre = area_encontrada.titulo
                    else:
                        # Si no se encuentra por nombre exacto, buscar por tipo de expediente
                        area_encontrada = AreaTipoExpediente.objects.filter(
                            tipo_expediente=expediente.tipo_expediente,
                            activa=True
                        ).first()
                        
                        if area_encontrada:
                            area_nombre = area_encontrada.titulo
                        else:
                            # Si aún no se encuentra, usar el nombre de la etapa formateado
                            if doc.etapa:
                                area_nombre = doc.etapa.replace('_', ' ').title()
                except Exception as e:
                    logger.warning(f"Error buscando área para documento {doc_id}: {str(e)}")
                    # Si hay error, usar el nombre de la etapa como fallback
                    if doc.etapa:
                        area_nombre = doc.etapa.replace('_', ' ').title()
            
            # Formatear fecha
            fecha_str = ''
            if doc.fecha_subida:
                fecha_str = doc.fecha_subida.strftime('%d/%m/%Y %H:%M')
            
            # Obtener fragmento destacado
            fragmento = result.get('fragmento', '')
            if not fragmento and doc.descripcion:
                fragmento = doc.descripcion[:300] + '...' if len(doc.descripcion) > 300 else doc.descripcion
            
            # Obtener información del expediente
            expediente_info = {
                'id': expediente.id,
                'numero': expediente.numero_expediente or f'EXP-{expediente.id}',
                'titulo': expediente.titulo or expediente.numero_expediente,
                'tipo_expediente': expediente.get_tipo_expediente_display() if hasattr(expediente, 'get_tipo_expediente_display') else 'Sin tipo',
                'url': f'/expedientes/{expediente.id}/'
            }
            
            # Validar que el documento tiene archivo antes de agregarlo
            if not doc.archivo:
                logger.warning(f"Documento {doc_id} no tiene archivo asociado")
                continue
            
            formatted_results.append({
                'id': doc.id,
                'titulo': doc.nombre_documento or 'Documento sin título',
                'fragmento': fragmento,
                'fecha_creacion': fecha_str,
                'tipo_archivo': doc.tipo_archivo or 'desconocido',
                'usuario': usuario_nombre,
                'area': area_nombre,
                'ruta_archivo': doc.archivo.url if doc.archivo else '',
                'expediente': expediente_info,
                'url_descarga': f'/documentos/{doc.id}/descargar/' if doc.archivo else '',
                'url_ver': f'/expedientes/{expediente.id}/',
                'score': result.get('score', 0)
            })
        except Exception as e:
            logger.error(f"Error formateando resultado: {str(e)}", exc_info=True)
            continue
    
    # Ordenar por score (relevancia) descendente
    formatted_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Calcular el total real basado en documentos válidos encontrados
    # El total del índice puede incluir documentos eliminados o inválidos
    # Por lo tanto, usamos el número de documentos válidos encontrados
    total_valido = len(formatted_results)
    total_index = results.get('total', 0)
    
    # Si hay más resultados en el índice que documentos válidos encontrados,
    # significa que algunos documentos en el índice pueden ser inválidos
    # Usamos el número de documentos válidos como total real
    if total_index > total_valido:
        # Hay más resultados en el índice, pero algunos pueden ser inválidos
        # Usar el total del índice como estimación, pero limitado por los documentos válidos
        # que realmente encontramos
        total = min(total_index, len(documentos_validos)) if 'documentos_validos' in locals() else total_valido
    else:
        total = total_valido
    
    # Calcular páginas basado en el total real de documentos válidos
    page_count = max(1, (total + 19) // 20)  # 20 documentos por página
    
    return JsonResponse({
        'success': True,
        'resultados': {
            'items': formatted_results,
            'total': total,
            'page': page,
            'total_paginas': page_count
        }
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def indexar_documentos(request):
    """
    Vista para indexar manualmente los documentos existentes
    Solo accesible para superusuarios
    """
    if request.method == 'POST':
        # Obtener todos los documentos
        documentos = DocumentoExpediente.objects.all()
        total = documentos.count()
        exitosos = 0
        
        # Indexar cada documento
        for doc in documentos:
            try:
                if index_document(doc):
                    exitosos += 1
            except Exception as e:
                logger.error(f"Error indexando documento {doc.id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'total': total,
            'exitosos': exitosos,
            'fallidos': total - exitosos
        })
    
    # Mostrar formulario de indexación
    return render(request, 'digitalizacion/admin/indexar_documentos.html')

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views, authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, ExpressionWrapper, fields, Avg
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.timezone import now
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
from .models import (
    Departamento, Expediente, 
    EtapaExpediente, DocumentoExpediente, NotaExpediente,
    Notificacion, ComentarioArea, SolicitudRegistro, RolUsuario,
    MensajeExpediente, User, TipoDocumento, HistorialExpediente,
    UserSession, AreaTipoExpediente, ValorAreaExpediente
)

@login_required
@require_http_methods(["POST"])
def actualizar_progreso_expediente(request, expediente_id):
    """Vista para actualizar el progreso de un expediente"""
    logger.info(f'[INICIO] Actualización de progreso para expediente {expediente_id}')
    logger.debug(f'Datos recibidos: {request.body}')
    
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        logger.debug(f'Expediente encontrado: ID {expediente.id}')
        
        # Verificar que el usuario tenga permiso para editar este expediente
        if not request.user.has_perm('digitalizacion.change_expediente', expediente):
            error_msg = f'Usuario {request.user} no tiene permiso para actualizar el expediente {expediente_id}'
            logger.warning(error_msg)
            return JsonResponse({
                'success': False,
                'error': 'No tiene permiso para actualizar este expediente',
                'code': 'permission_denied'
            }, status=403)
        
        # Obtener los datos del cuerpo de la petición
        try:
            data = json.loads(request.body.decode('utf-8'))
            porcentaje = int(data.get('porcentaje', 0))
            completadas = int(data.get('completadas', 0))
            total = int(data.get('total', 1))
            
            logger.debug(f'Datos parseados - Porcentaje: {porcentaje}, Completadas: {completadas}, Total: {total}')
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            error_msg = f'Error al procesar los datos de progreso: {str(e)}'
            logger.error(error_msg)
            return JsonResponse({
                'success': False,
                'error': 'Datos de progreso inválidos',
                'details': str(e),
                'code': 'invalid_data'
            }, status=400)
        
        # Validar los datos
        if not (0 <= porcentaje <= 100):
            error_msg = f'Porcentaje inválido: {porcentaje}. Debe estar entre 0 y 100.'
            logger.error(error_msg)
            return JsonResponse({
                'success': False,
                'error': 'El porcentaje debe estar entre 0 y 100',
                'code': 'invalid_percentage'
            }, status=400)
        
        # Guardar el estado anterior para el historial
        estado_anterior = expediente.estado
        estado_actual_anterior = expediente.estado_actual
        
        # Actualizar el progreso
        expediente.progreso = min(100, max(0, porcentaje))  # Asegurar que esté entre 0 y 100
        
        # Determinar el nuevo estado basado en el progreso
        if porcentaje == 100:
            nuevo_estado = 'completo'
            nuevo_estado_actual = 'completado'  # Usar 'completado' que es el valor en ESTADO_CHOICES
            update_fields = ['progreso', 'estado', 'estado_actual', 'fecha_actualizacion']
        elif porcentaje < 100 and estado_anterior == 'completo':
            # Si el progreso baja del 100%, volver a 'en_proceso'
            nuevo_estado = 'en_proceso'
            nuevo_estado_actual = estado_actual_anterior  # Mantener el estado_actual anterior
            update_fields = ['progreso', 'estado', 'fecha_actualizacion']
        else:
            nuevo_estado = estado_anterior
            nuevo_estado_actual = estado_actual_anterior
            update_fields = ['progreso', 'fecha_actualizacion']
        
        # Actualizar los estados si es necesario
        if nuevo_estado != estado_anterior:
            expediente.estado = nuevo_estado
            
        if porcentaje == 100 and estado_actual_anterior != 'completado':
            expediente.estado_actual = 'completado'
        
        # Guardar los cambios
        expediente.save(update_fields=update_fields)
        logger.info(f'[OK] Progreso actualizado - Expediente: {expediente_id}, Progreso: {porcentaje}%, Estado: {expediente.estado}, Estado Actual: {expediente.estado_actual}')
        
        # Registrar el cambio en el historial
        try:
            HistorialExpediente.objects.create(
                expediente=expediente,
                usuario=request.user,
                accion='actualizacion_progreso',
                descripcion=f'Progreso actualizado a {porcentaje}%',
                etapa_anterior=estado_anterior,
                etapa_nueva=nuevo_estado
            )
            
            # Si el estado cambió a completo, registrar también ese evento
            if porcentaje == 100 and estado_anterior != 'completo':
                HistorialExpediente.objects.create(
                    expediente=expediente,
                    usuario=request.user,
                    accion='cambio_estado',
                    descripcion=f'Estado cambiado a "Expediente completo"',
                    etapa_anterior=estado_actual_anterior,
                    etapa_nueva='completado'
                )
                
        except Exception as e:
            logger.error(f'Error al registrar en el historial: {str(e)}')
        
        # Devolver respuesta exitosa
        response_data = {
            'success': True,
            'message': 'Progreso actualizado correctamente',
            'progreso': expediente.progreso,
            'completadas': completadas,
            'total': total
        }
        logger.debug(f'Respuesta exitosa: {response_data}')
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_msg = f'Error al actualizar progreso del expediente {expediente_id}: {str(e)}'
        logger.error(error_msg, exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno al actualizar el progreso del expediente',
            'code': 'server_error',
            'details': str(e) if settings.DEBUG else None
        }, status=500)


def obtener_progreso_documentos(request, expediente_id):
    """Vista para obtener el progreso de documentos de un expediente"""
    try:
        # Obtener el expediente
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar que el expediente tenga un número de expediente
        if not hasattr(expediente, 'numero_expediente') or not expediente.numero_expediente:
            return JsonResponse({
                'success': False,
                'error': 'El expediente no tiene un número de expediente asignado',
                'code': 'missing_expediente_number'
            }, status=400)
        
        # Obtener todas las áreas configuradas para este tipo de expediente
        areas = AreaTipoExpediente.objects.filter(
            tipo_expediente=expediente.tipo_expediente,
            activa=True
        ).order_by('orden')
        
        # Si hay un subtipo de expediente, filtrar por él
        if hasattr(expediente, 'subtipo_expediente') and expediente.subtipo_expediente:
            areas = areas.filter(
                Q(subtipo_expediente=expediente.subtipo_expediente) | 
                Q(subtipo_expediente__isnull=True)
            )
        
        # Obtener el conteo de documentos por área
        areas_data = []
        areas_completadas = 0
        
        for area in areas:
            # Contar documentos en esta área
            documentos_count = DocumentoExpediente.objects.filter(
                expediente=expediente,
                etapa=area.nombre
            ).count()
            
            # Verificar si el área está completada
            valor_area = ValorAreaExpediente.objects.filter(
                expediente=expediente,
                area=area
            ).first()
            
            completada = bool(valor_area and valor_area.completada)
            if completada:
                areas_completadas += 1
            
            areas_data.append({
                'id': str(area.id),
                'nombre': area.nombre,
                'titulo': area.titulo,
                'completada': completada,
                'documentos_count': documentos_count,
                'obligatoria': area.obligatoria,
                'fecha_completada': valor_area.fecha_completada if valor_area else None,
                'completada_por': valor_area.completada_por.get_full_name() if valor_area and valor_area.completada_por else None
            })
        
        # Calcular el porcentaje de completado
        total_areas = len(areas_data)
        porcentaje_completo = 0
        if total_areas > 0:
            porcentaje_completo = int((areas_completadas / total_areas) * 100)
        
        # Devolver los datos en formato JSON
        return JsonResponse({
            'success': True,
            'expediente_id': expediente_id,
            'numero_expediente': expediente.numero_expediente,  # Asegurarse de incluir el número de expediente
            'areas': areas_data,
            'porcentaje_completo': porcentaje_completo,
            'areas_completadas': areas_completadas,
            'total_areas': total_areas,
            'ultima_actualizacion': timezone.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc() if settings.DEBUG else None
        }, status=500)

from .forms import (
    ExpedienteForm, 
    DepartamentoForm
)

def inicio(request):
    """Vista de inicio para usuarios no autenticados"""
    if request.user.is_authenticated:
        return redirect('digitalizacion:dashboard')
    
    return render(request, 'digitalizacion/inicio.html')

@login_required
def dashboard(request):
    try:
        # Obtener todos los expedientes
        total_expedientes = Expediente.objects.count()
        
        # Obtener datos para el gráfico de actividad
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        # Nombres de los días en español
        nombres_dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        
        # Inicializar listas para el gráfico con valores predeterminados
        expedientes_por_dia = [0, 0, 0, 0, 0, 0, 0]  # 7 ceros para los días de la semana
        dias_semana = nombres_dias.copy()  # Usar los nombres de los días en español
        
        try:
            # Obtener conteo de expedientes para cada día de la semana actual
            for i in range(7):
                dia = inicio_semana + timedelta(days=i)
                dia_siguiente = dia + timedelta(days=1)
                
                # Contar expedientes creados en este día
                conteo = Expediente.objects.filter(
                    fecha_creacion__date__gte=dia,
                    fecha_creacion__date__lt=dia_siguiente
                ).count()
                
                expedientes_por_dia[i] = conteo
        except Exception as e:
            print(f"Error al obtener datos para el gráfico: {str(e)}")
            # En caso de error, usamos los valores predeterminados (todos ceros)
        
        # Definir estados para cada categoría
        estados_completados = ['completado', 'finalizado', 'aprobado', 'terminado', 'pago']
        estados_rechazados = ['rechazado', 'rechazada', 'denegado', 'cancelado']
        estados_en_proceso = [
            'inicio', 'solicitud_area', 'cotizacion', 'requisicion_sima',
            'suficiencia_presupuestal', 'aprobacion_director', 'aprobacion_secretario',
            'notificacion_compras', 'valoracion_tipo', 'adjudicacion', 'formalizacion',
            'contrato', 'recepcion_bien', 'recepcion_facturacion', 'generacion_evidencia',
            'envio_compras'
        ]
        
        # Contar expedientes por estado
        expedientes_en_proceso = Expediente.objects.filter(estado_actual__in=estados_en_proceso).count()
        expedientes_completados = Expediente.objects.filter(estado_actual__in=estados_completados).count()
        expedientes_rechazados = Expediente.objects.filter(estado_actual__in=estados_rechazados).count()
        
        # Calcular total para porcentajes (excluyendo estados vacíos)
        total_no_cero = expedientes_en_proceso + expedientes_completados + expedientes_rechazados
        
        # Obtener expedientes de este mes
        primer_dia_mes = hoy.replace(day=1)
        expedientes_este_mes = Expediente.objects.filter(
            fecha_creacion__date__gte=primer_dia_mes
        ).count()
        
        # Inicializar diccionario para tipos de expediente
        tipos_expediente = {}
        
        # Mapeo de modalidades de monto a nombres legibles
        mapeo_modalidades = {
            'licitacion': 'Licitación',
            'adjudicacion_directa': 'Adjudicación Directa',
            'compra_directa': 'Compra Directa',
            'concurso_invitacion': 'Concurso por Invitación',
            'sin_especificar': 'Sin Especificar'  # Para expedientes sin modalidad definida
        }
        
        # Inicializar todos los tipos con contador en 0
        for clave, nombre in mapeo_modalidades.items():
            tipos_expediente[clave] = {
                'nombre': nombre,
                'total': 0,
                'porcentaje': 0.0
            }
        
        # Contar expedientes por modalidad de monto
        if hasattr(Expediente, 'modalidad_monto'):
            # Obtener conteo de expedientes por modalidad
            expedientes_por_modalidad = Expediente.objects.values('modalidad_monto').annotate(
                total=Count('id')
            )
            
            # Inicializar contador para expedientes sin modalidad
            total_con_modalidad = 0
            
            # Actualizar contadores con los valores reales
            for item in expedientes_por_modalidad:
                modalidad = item['modalidad_monto']
                if modalidad in mapeo_modalidades:
                    tipos_expediente[modalidad]['total'] = item['total']
                    total_con_modalidad += item['total']
            
            # Calcular expedientes sin modalidad definida
            if total_con_modalidad < total_expedientes:
                tipos_expediente['sin_especificar']['total'] = total_expedientes - total_con_modalidad
        
        # Calcular porcentajes basados en el total de expedientes
        for datos in tipos_expediente.values():
            porcentaje = (datos['total'] * 100.0 / total_expedientes) if total_expedientes > 0 else 0
            datos['porcentaje'] = round(porcentaje, 1)
        
        # Si no hay expedientes sin especificar, eliminamos la categoría
        if tipos_expediente['sin_especificar']['total'] == 0:
            del tipos_expediente['sin_especificar']
        
        
        # Obtener expedientes recientes
        expedientes_recientes = Expediente.objects.order_by('-fecha_creacion')[:5]
        
        # Obtener actividades recientes del historial (incluyendo inicios de sesión)
        actividades_recientes = HistorialExpediente.objects.select_related('expediente', 'usuario')\
            .order_by('-fecha')[:10]  # Mostrar más actividades para incluir inicios de sesión
        
        # Obtener expedientes de hoy
        hoy = timezone.now().date()
        manana = hoy + timedelta(days=1)
        expedientes_hoy = Expediente.objects.filter(
            fecha_creacion__date__gte=hoy,
            fecha_creacion__date__lt=manana
        ).count()
        
        # Obtener documentos subidos hoy y su tamaño total
        from django.db.models import Sum
        
        # Obtener la fecha de hoy a medianoche (00:00:00) en la zona horaria del servidor
        hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoy_fin = hoy_inicio + timedelta(days=1)
        
        # Obtener documentos del día actual
        documentos_hoy = DocumentoExpediente.objects.filter(
            fecha_subida__gte=hoy_inicio,
            fecha_subida__lt=hoy_fin
        )
        
        # Contar documentos del día
        total_documentos_hoy = documentos_hoy.count()
        
        # Calcular tamaño total de los documentos subidos hoy (en MB)
        # Usar el campo tamano_archivo que se calcula automáticamente al guardar
        total_tamano = documentos_hoy.aggregate(
            total=Sum('tamano_archivo')
        )['total'] or 0
        
        total_tamano_hoy_mb = round(total_tamano / (1024 * 1024), 2) if total_tamano > 0 else 0
        
        # Obtener la última subida
        ultima_subida = documentos_hoy.order_by('-fecha_subida').first()
        tiempo_ultima_subida = 'Nunca'
        
        if ultima_subida and ultima_subida.fecha_subida:
            ahora = timezone.now()
            diferencia = ahora - ultima_subida.fecha_subida
            
            if diferencia < timedelta(minutes=1):
                segundos = int(diferencia.total_seconds())
                tiempo_ultima_subida = f'hace {segundos} segundos'
            elif diferencia < timedelta(hours=1):
                minutos = int(diferencia.total_seconds() / 60)
                tiempo_ultima_subida = f'hace {minutos} min'
            elif diferencia < timedelta(days=1):
                horas = int(diferencia.total_seconds() / 3600)
                tiempo_ultima_subida = f'hace {horas} horas'
            elif diferencia < timedelta(days=30):
                dias = diferencia.days
                tiempo_ultima_subida = f'hace {dias} días'
        
        # Preparar datos para el gráfico de estados
        estados_grafico = {
            'labels': ['En Proceso', 'Completados', 'Rechazados'],
            'data': [expedientes_en_proceso, expedientes_completados, expedientes_rechazados],
            'colors': ['#3b82f6', '#10b981', '#ef4444']  # azul, verde, rojo
        }
        
        # Calcular tiempo promedio de resolución (usando fecha_actualizacion como fecha de cierre)
        tiempo_promedio_dias = 0
        try:
            tiempo_promedio = Expediente.objects.filter(
                estado_actual__in=estados_completados,
                fecha_actualizacion__isnull=False
            ).annotate(
                tiempo_resolucion=ExpressionWrapper(
                    F('fecha_actualizacion') - F('fecha_creacion'),
                    output_field=fields.DurationField()
                )
            ).aggregate(
                avg_tiempo=Avg('tiempo_resolucion')
            )
            
            if tiempo_promedio['avg_tiempo']:
                tiempo_promedio_dias = round(tiempo_promedio['avg_tiempo'].total_seconds() / (24 * 3600), 1)
        except Exception as e:
            print(f"Error calculando tiempo promedio: {str(e)}")
            tiempo_promedio_dias = 0
        
        # Calcular tiempo promedio de resolución (usando fecha_creacion y fecha_actualizacion como aproximación)
        try:
            tiempo_promedio = Expediente.objects.filter(
                estado_actual__in=estados_completados
            ).annotate(
                tiempo_resolucion=ExpressionWrapper(
                    F('fecha_actualizacion') - F('fecha_creacion'),
                    output_field=fields.DurationField()
                )
            ).aggregate(
                avg_tiempo=Avg('tiempo_resolucion')
            )['avg_tiempo'] or timedelta(days=0)
            
            # Convertir a días
            tiempo_promedio_dias = round(tiempo_promedio.total_seconds() / 86400, 1)
        except Exception as e:
            print(f"Error calculando tiempo promedio: {e}")
            tiempo_promedio_dias = 0
        
        # Obtener departamentos con más expedientes
        from .models import Departamento
        departamentos_con_expedientes = Departamento.objects.annotate(
            num_expedientes=Count('expediente')
        ).filter(num_expedientes__gt=0).order_by('-num_expedientes')[:5]
        
        # Obtener total de departamentos y usuarios
        total_departamentos = Departamento.objects.filter(activo=True).count()
        total_usuarios = User.objects.filter(is_active=True).count()
        
        # Obtener usuarios conectados (últimos 5 minutos)
        threshold = timezone.now() - timedelta(minutes=5)
        # Usar values_list con distinct() para compatibilidad con SQLite
        usuarios_conectados_ids = UserSession.objects.filter(
            is_online=True,
            last_activity__gte=threshold
        ).values_list('user_id', flat=True).distinct()
        usuarios_conectados = len(usuarios_conectados_ids)
        
        # Obtener usuarios más activos (basado en expedientes creados)
        usuarios_activos = User.objects.filter(is_active=True).annotate(
            num_expedientes=Count('expedientes_creados')
        ).filter(num_expedientes__gt=0).order_by('-num_expedientes')[:5]
        
        # Calcular porcentajes para usuarios activos
        for usuario in usuarios_activos:
            usuario.porcentaje = min(100, int((usuario.num_expedientes / max(total_expedientes, 1)) * 100))
        
        # Convertir a JSON para el template
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        
        # Contexto con estadísticas
        context = {
            # Datos para el gráfico
            'dias_semana': json.dumps(dias_semana, cls=DjangoJSONEncoder, ensure_ascii=False),
            'expedientes_por_dia': json.dumps(expedientes_por_dia, cls=DjangoJSONEncoder),
            'expedientes_hoy': expedientes_hoy,
            # Estadísticas principales
            'total_expedientes': total_expedientes,
            'expedientes_en_proceso': expedientes_en_proceso,
            'expedientes_completados': expedientes_completados,
            'expedientes_rechazados': expedientes_rechazados,
            'expedientes_este_mes': expedientes_este_mes,
            'expedientes_recientes': expedientes_recientes,
            'actividades_recientes': actividades_recientes,
            'estados_grafico': estados_grafico,
            'tiempo_promedio': tiempo_promedio_dias,
            'total_departamentos': total_departamentos,
            'total_usuarios': total_usuarios,
            'usuarios_conectados': usuarios_conectados,
            'usuarios_activos': usuarios_activos,
            
            # Porcentajes
            'porcentaje_completados': round((expedientes_completados / total_no_cero) * 100, 1) if total_no_cero > 0 else 0,
            'porcentaje_en_proceso': round((expedientes_en_proceso / total_no_cero) * 100, 1) if total_no_cero > 0 else 0,
            'porcentaje_rechazados': round((expedientes_rechazados / total_no_cero) * 100, 1) if total_no_cero > 0 else 0,
            
            # Datos para documentos subidos hoy
            'total_documentos_hoy': total_documentos_hoy,
            'total_tamano_hoy_mb': total_tamano_hoy_mb,
            'tiempo_ultima_subida': tiempo_ultima_subida,
            
            # Datos para gráficos adicionales
            'departamentos_con_expedientes': departamentos_con_expedientes,
            'tasa_exito': round((expedientes_completados / total_no_cero) * 100, 1) if total_no_cero > 0 else 0,
            'expedientes_mes': expedientes_este_mes,
            'porcentaje_mes': round((expedientes_este_mes / total_no_cero) * 100, 1) if total_no_cero > 0 else 0,
            
            # Notificaciones
            'notificaciones_usuario': Notificacion.objects.filter(
                usuario=request.user
            ).order_by('-fecha_creacion')[:5],
            'total_notificaciones': Notificacion.objects.filter(
                usuario=request.user, 
                leida=False
            ).count(),
            
            # Tipos de expediente
            'tipos_expediente': tipos_expediente,
        }
        
        return render(request, 'digitalizacion/dashboard.html', context)
        
    except Exception as e:
        print(f"Error en la vista dashboard: {str(e)}")
        # Retornar un contexto vacío en caso de error
        return render(request, 'digitalizacion/dashboard.html', {
            'error': 'Ocurrió un error al cargar el dashboard. Por favor, intente nuevamente.'
        })










def reportes(request):
    """Vista para mostrar reportes del sistema"""
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Limpiar mensajes del sistema al acceder a reportes
    # Esto evita que mensajes de otras páginas aparezcan aquí
    storage = messages.get_messages(request)
    storage.used = True
    
    # Obtener fecha actual
    now = timezone.now()
    today = now.date()
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.GET.get('fecha_fin', today.strftime('%Y-%m-%d'))
    
    # Convertir fechas para filtros
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except:
        fecha_inicio_dt = today - timedelta(days=30)
        fecha_fin_dt = today
    
    # Estadísticas generales
    total_expedientes = Expediente.objects.count()
    expedientes_periodo = Expediente.objects.filter(
        fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).count()
    
    # Expedientes por tipo (aplicar filtros de fecha)
    expedientes_por_tipo = Expediente.objects.filter(
        fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).values('tipo_expediente').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Expedientes por estado (aplicar filtros de fecha)
    expedientes_por_estado = Expediente.objects.filter(
        fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).values('estado_actual').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Expedientes por departamento (aplicar filtros de fecha)
    expedientes_por_departamento = Expediente.objects.filter(
        fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).values('departamento__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # Usuarios más activos (por expedientes creados en el período)
    usuarios_activos = User.objects.filter(
        expedientes_creados__fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).annotate(
        total_expedientes=Count('expedientes_creados')
    ).filter(
        total_expedientes__gt=0
    ).order_by('-total_expedientes')[:10]
    
    # Expedientes por mes (últimos 12 meses)
    expedientes_por_mes = []
    for i in range(12):
        fecha = now - timedelta(days=30*i)
        mes = fecha.strftime('%Y-%m')
        total = Expediente.objects.filter(
            fecha_creacion__year=fecha.year,
            fecha_creacion__month=fecha.month
        ).count()
        expedientes_por_mes.append({'mes': mes, 'total': total})
    
    expedientes_por_mes.reverse()
    
    # Documentos subidos por período
    documentos_periodo = DocumentoExpediente.objects.filter(
        fecha_subida__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).count()
    
    # Usuarios que subieron documentos en el período
    usuarios_subieron_documentos = User.objects.filter(
        documentoexpediente__fecha_subida__date__range=[fecha_inicio_dt, fecha_fin_dt]
    ).distinct().count()
    
    context = {
        'total_expedientes': total_expedientes,
        'expedientes_periodo': expedientes_periodo,
        'expedientes_por_tipo': expedientes_por_tipo,
        'expedientes_por_estado': expedientes_por_estado,
        'expedientes_por_departamento': expedientes_por_departamento,
        'usuarios_activos': usuarios_activos,
        'expedientes_por_mes': expedientes_por_mes,
        'documentos_periodo': documentos_periodo,
        'usuarios_subieron_documentos': usuarios_subieron_documentos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_inicio_dt': fecha_inicio_dt,
        'fecha_fin_dt': fecha_fin_dt,
    }
    
    return render(request, 'digitalizacion/reportes.html', context)

def obtener_expedientes_filtrados(request):
    """Vista AJAX para obtener expedientes filtrados por fecha y otros criterios"""
    from django.http import JsonResponse
    from django.db.models import Q
    import json
    
    if request.method == 'POST':
        try:
            # Obtener parámetros de filtro del body JSON
            data = json.loads(request.body)
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            estado = data.get('estado', '')
            tipo = data.get('tipo', '')
            
            # Validar fechas
            if not fecha_inicio or not fecha_fin:
                return JsonResponse({'success': False, 'error': 'Fechas de inicio y fin son requeridas'})
            
            # Construir filtros con manejo correcto de fechas
            from datetime import datetime, time
            import logging
            
            # Configurar logging
            logger = logging.getLogger(__name__)
            
            # Log de los datos recibidos del frontend
            logger.info(f'Datos recibidos del frontend: {data}')
            logger.info(f'Fecha inicio recibida: {fecha_inicio}')
            logger.info(f'Fecha fin recibida: {fecha_fin}')
            
            # Convertir fechas string a datetime aware en la zona horaria local
            from datetime import time as dt_time
            from datetime import timedelta
            
            # Convertir las fechas string a objetos date
            fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            
            # Obtener la zona horaria local de Django
            local_tz = timezone.get_current_timezone()
            
            # Crear datetime objects naive primero
            fecha_inicio_naive = datetime.combine(fecha_inicio_date, dt_time.min)
            fecha_fin_naive = datetime.combine(fecha_fin_date, dt_time.max.replace(microsecond=999999))
            
            # Convertir a datetime aware en la zona horaria local usando make_aware
            fecha_inicio_local = timezone.make_aware(fecha_inicio_naive, local_tz)
            fecha_fin_local = timezone.make_aware(fecha_fin_naive, local_tz)
            
            # Convertir a UTC explícitamente para la comparación
            # Usar get_fixed_timezone(0) que es compatible con todas las versiones de Django
            utc_tz = timezone.get_fixed_timezone(0)
            fecha_inicio_utc = fecha_inicio_local.astimezone(utc_tz)
            fecha_fin_utc = fecha_fin_local.astimezone(utc_tz)
            
            # Usar fecha_creacion__gte y fecha_creacion__lte con datetime UTC
            filtros = Q(fecha_creacion__gte=fecha_inicio_utc) & Q(fecha_creacion__lte=fecha_fin_utc)
            
            # Log para depuración
            logger.info(f'Filtros de fecha - Seleccionado: {fecha_inicio} a {fecha_fin}')
            logger.info(f'Filtros de fecha - Local: {fecha_inicio_local} a {fecha_fin_local}')
            logger.info(f'Filtros de fecha - UTC: {fecha_inicio_utc} a {fecha_fin_utc}')
            logger.info(f'Zona horaria del sistema: {local_tz}')
            logger.info(f'Consulta SQL: fecha_creacion__gte={fecha_inicio_utc} AND fecha_creacion__lte={fecha_fin_utc}')
            
            if estado:
                filtros &= Q(estado_actual=estado)
            
            if tipo:
                filtros &= Q(tipo_expediente=tipo)
            
            # Obtener expedientes filtrados con sus documentos
            expedientes = Expediente.objects.filter(filtros).select_related(
                'departamento', 'creado_por'
            ).prefetch_related(
                'documentos__subido_por', 'documentos__validado_por', 'documentos__area'
            ).order_by('-fecha_creacion')
            
            # Log para depuración
            logger.info(f'Consulta SQL: {expedientes.query}')
            logger.info(f'Total de expedientes encontrados: {expedientes.count()}')
            
            # Preparar datos para la respuesta
            expedientes_data = []
            local_tz = timezone.get_current_timezone()
            for expediente in expedientes:
                # Convertir fechas a la zona horaria local antes de formatear
                fecha_creacion_local = timezone.localtime(expediente.fecha_creacion, local_tz)
                fecha_actualizacion_local = timezone.localtime(expediente.fecha_actualizacion, local_tz) if expediente.fecha_actualizacion else None
                
                # Obtener todos los documentos del expediente
                documentos = expediente.documentos.all().select_related('subido_por', 'validado_por', 'area')
                documentos_data = []
                for doc in documentos:
                    fecha_subida_local = timezone.localtime(doc.fecha_subida, local_tz) if doc.fecha_subida else None
                    fecha_validacion_local = timezone.localtime(doc.fecha_validacion, local_tz) if doc.fecha_validacion else None
                    documentos_data.append({
                        'nombre': doc.nombre_documento,
                        'descripcion': doc.descripcion or '',
                        'etapa': doc.etapa,
                        'area': doc.area.titulo if doc.area else 'No especificada',
                        'tipo_archivo': doc.tipo_archivo or '',
                        'tamano_archivo': doc.tamano_archivo or 0,
                        'subido_por': doc.subido_por.get_full_name() if doc.subido_por else doc.subido_por.username if doc.subido_por else 'N/A',
                        'fecha_subida': fecha_subida_local.strftime('%Y-%m-%d %H:%M:%S') if fecha_subida_local else '',
                        'validado': 'Sí' if doc.validado else 'No',
                        'validado_por': doc.validado_por.get_full_name() if doc.validado_por else doc.validado_por.username if doc.validado_por else '',
                        'fecha_validacion': fecha_validacion_local.strftime('%Y-%m-%d %H:%M:%S') if fecha_validacion_local else ''
                    })
                
                expedientes_data.append({
                    'id': expediente.id,
                    'numero': expediente.numero_expediente or f'EXP-{expediente.id:04d}',
                    'titulo': expediente.titulo or '',
                    'descripcion': expediente.descripcion or '',
                    'tipo': expediente.tipo_expediente or 'No especificado',
                    'subtipo': expediente.subtipo_expediente or 'No especificado',
                    'estado': expediente.estado_actual or 'inicio',
                    'giro': expediente.giro or '',
                    'fuente_financiamiento': expediente.get_fuente_financiamiento_display() if expediente.fuente_financiamiento else '',
                    'tipo_adquisicion': expediente.get_tipo_adquisicion_display() if expediente.tipo_adquisicion else '',
                    'modalidad_monto': expediente.get_modalidad_monto_display() if expediente.modalidad_monto else '',
                    'numero_sima': expediente.numero_sima or '',
                    'fecha_expediente': expediente.fecha_expediente.strftime('%Y-%m-%d') if expediente.fecha_expediente else '',
                    'fecha_vencimiento': expediente.fecha_vencimiento.strftime('%Y-%m-%d') if expediente.fecha_vencimiento else '',
                    'fecha_creacion': fecha_creacion_local.strftime('%Y-%m-%d %H:%M:%S'),
                    'fecha_actualizacion': fecha_actualizacion_local.strftime('%Y-%m-%d %H:%M:%S') if fecha_actualizacion_local else '',
                    'departamento': expediente.departamento.nombre if expediente.departamento else 'Sin departamento',
                    'solicitante': expediente.creado_por.get_full_name() if expediente.creado_por else expediente.creado_por.username if expediente.creado_por else 'Usuario no especificado',
                    'progreso': expediente.progreso or 0,
                    'palabras_clave': expediente.palabras_clave or '',
                    'observaciones': expediente.observaciones or '',
                    'confidencial': 'Sí' if expediente.confidencial else 'No',
                    'motivo_rechazo': expediente.motivo_rechazo or '',
                    'fecha_rechazo': expediente.fecha_rechazo.strftime('%Y-%m-%d %H:%M:%S') if expediente.fecha_rechazo else '',
                    'documentos': documentos_data,
                    'total_documentos': len(documentos_data)
                })
            
            logger.info(f'Datos preparados: {len(expedientes_data)} expedientes')
            
            return JsonResponse({
                'success': True,
                'expedientes': expedientes_data
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Formato JSON inválido'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al obtener expedientes: {str(e)}'})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(['POST'])
@login_required
@require_http_methods(['GET', 'DELETE'])
def api_documento(request, documento_id):
    """
    API endpoint para obtener o eliminar un documento específico
    """
    try:
        # Obtener el documento
        documento = get_object_or_404(DocumentoExpediente, id=documento_id)
        expediente = documento.expediente
        
        # Verificar permisos
        if not request.user.has_perm('digitalizacion.view_documentoexpediente', documento):
            if request.user != documento.subido_por and request.user != expediente.creado_por:
                return JsonResponse(
                    {'success': False, 'error': 'No tiene permiso para acceder a este documento'}, 
                    status=403
                )
        
        # Manejar método GET (obtener detalles del documento)
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'documento': {
                    'id': documento.id,
                    'nombre': documento.nombre_documento,
                    'tipo_documento': documento.tipo_documento.nombre if documento.tipo_documento else None,
                    'tipo_documento_id': documento.tipo_documento.id if documento.tipo_documento else None,
                    'expediente_id': expediente.id,
                    'fecha_subida': documento.fecha_subida.isoformat(),
                    'subido_por': documento.subido_por.get_full_name() or documento.subido_por.username,
                    'subido_por_id': documento.subido_por.id,
                    'tamano_bytes': documento.tamano_bytes,
                    'url': documento.archivo.url if documento.archivo else None,
                    'mime_type': documento.mime_type
                }
            })
            
        # Manejar método DELETE (eliminar documento)
        elif request.method == 'DELETE':
            if not request.user.has_perm('digitalizacion.delete_documentoexpediente'):
                if request.user != documento.subido_por and request.user != expediente.creado_por:
                    return JsonResponse(
                        {'success': False, 'error': 'No tiene permiso para eliminar este documento'}, 
                        status=403
                    )
            
            # Registrar en el historial antes de eliminar
            HistorialExpediente.objects.create(
                expediente=expediente,
                usuario=request.user,
                accion='Documento eliminado',
                detalles=f'Se eliminó el documento: {documento.nombre_documento}'
            )
            
            # Eliminar el archivo físico si existe
            if documento.archivo and hasattr(documento.archivo, 'path') and os.path.isfile(documento.archivo.path):
                try:
                    os.remove(documento.archivo.path)
                except Exception as e:
                    logger.error(f'Error al eliminar archivo físico {documento.archivo.path}: {str(e)}')
            
            # Eliminar el registro de la base de datos
            documento.delete()
            
            # Actualizar el progreso y estado del expediente
            # Esto automáticamente cambiará el estado de 'completo' a 'en_proceso' si el progreso baja del 100%
            nuevo_progreso = expediente.actualizar_progreso()
            logger.info(f'Expediente {expediente.id} - Progreso actualizado a {nuevo_progreso}% después de eliminar documento')
            
            return JsonResponse({
                'success': True,
                'message': 'Documento eliminado correctamente',
                'documento_id': documento_id,
                'nuevo_progreso': nuevo_progreso,
                'nuevo_estado': expediente.estado
            })
            
    except DocumentoExpediente.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Documento no encontrado'}, 
            status=404
        )
    except Exception as e:
        logger.error(f'Error en api_documento: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error interno del servidor al procesar la solicitud'}, 
            status=500
        )


def upload_documento(request):
    """
    API endpoint para subir documentos a un expediente
    """
    try:
        # Verificar que se haya enviado un archivo
        if 'archivo' not in request.FILES:
            return JsonResponse(
                {'success': False, 'error': 'No se ha proporcionado ningún archivo'}, 
                status=400
            )
            
        archivo = request.FILES['archivo']
        expediente_id = request.POST.get('expediente_id')
        tipo_documento_id = request.POST.get('tipo_documento_id')
        
        # Validar campos requeridos
        if not expediente_id or not tipo_documento_id:
            return JsonResponse(
                {'success': False, 'error': 'Faltan campos requeridos'}, 
                status=400
            )
            
        try:
            expediente = Expediente.objects.get(id=expediente_id)
            tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)
        except (Expediente.DoesNotExist, TipoDocumento.DoesNotExist) as e:
            return JsonResponse(
                {'success': False, 'error': 'Expediente o tipo de documento no encontrado'}, 
                status=404
            )
            
        # Verificar permisos
        if not (request.user.has_perm('digitalizacion.add_documentoexpediente') or 
                request.user == expediente.creado_por):
            return JsonResponse(
                {'success': False, 'error': 'No tiene permiso para subir documentos a este expediente'}, 
                status=403
            )
        
        # Obtener el tipo MIME del archivo
        mime_type = getattr(archivo, 'content_type', None)
        
        # Crear el documento
        documento = DocumentoExpediente(
            expediente=expediente,
            tipo_documento=tipo_documento,
            nombre_documento=archivo.name,
            subido_por=request.user,
            archivo=archivo,
            mime_type=mime_type,
            tamano_bytes=archivo.size
        )
        documento.save()
        
        # Registrar en el historial
        HistorialExpediente.objects.create(
            expediente=expediente,
            usuario=request.user,
            accion='Documento subido',
            detalles=f'Se subió el documento: {archivo.name}'
        )
        
        return JsonResponse({
            'success': True,
            'documento': {
                'id': documento.id,
                'nombre': documento.nombre_documento,
                'tipo_documento': documento.tipo_documento.nombre if documento.tipo_documento else None,
                'tipo_documento_id': documento.tipo_documento.id if documento.tipo_documento else None,
                'expediente_id': expediente.id,
                'fecha_subida': documento.fecha_subida.isoformat(),
                'subido_por': documento.subido_por.get_full_name() or documento.subido_por.username,
                'subido_por_id': documento.subido_por.id,
                'tamano_bytes': documento.tamano_bytes,
                'url': documento.archivo.url if documento.archivo else None,
                'mime_type': documento.mime_type
            }
        })
        
    except Exception as e:
        logger.error(f'Error al subir documento: {str(e)}')
        return JsonResponse(
            {'success': False, 'error': 'Error interno del servidor al procesar el documento'}, 
            status=500
        )


def eliminar_expediente(request, expediente_id):
    """Vista para eliminar un expediente"""
    from django.http import JsonResponse
    from django.contrib.auth.decorators import login_required
    from django.views.decorators.http import require_http_methods
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar permisos (opcional: solo el creador o administradores pueden eliminar)
        if not request.user.is_staff and expediente.creado_por != request.user:
            return JsonResponse({'error': 'No tienes permisos para eliminar este expediente'}, status=403)
        
        # Obtener información del expediente antes de eliminarlo
        numero_expediente = expediente.numero_expediente or f'EXP-{expediente.id:04d}'
        
        # Eliminar el expediente
        expediente.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Expediente {numero_expediente} eliminado correctamente'
        })
        
    except Expediente.DoesNotExist:
        return JsonResponse({'error': 'Expediente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar expediente: {str(e)}'}, status=500)



def exportar_reporte(request):
    """Vista para exportar reportes"""
    from django.http import HttpResponse
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    import csv
    import json
    
    # Obtener parámetros
    tipo_reporte = request.GET.get('tipo', 'expedientes')
    formato = request.GET.get('formato', 'csv')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    # Calcular fechas según el período si no se proporcionan fechas específicas
    now = timezone.now()
    today = now.date()
    
    if not fecha_inicio or not fecha_fin:
        # Usar período por defecto (último mes)
        fecha_inicio = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_fin = today.strftime('%Y-%m-%d')
    
    # Convertir fechas para filtros
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except:
        fecha_inicio_dt = today - timedelta(days=30)
        fecha_fin_dt = today
    
    # Obtener datos según el tipo de reporte
    if tipo_reporte == 'expedientes':
        datos = Expediente.objects.filter(
            fecha_creacion__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).select_related('departamento', 'creado_por')
        
        if formato == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_expedientes_{fecha_inicio}_{fecha_fin}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Número', 'Título', 'Tipo', 'Departamento', 'Estado', 'Fecha Creación', 'Creado por'])
            
            for expediente in datos:
                writer.writerow([
                    expediente.numero_expediente,
                    expediente.titulo,
                    expediente.get_tipo_expediente_display(),
                    expediente.departamento.nombre if expediente.departamento else 'N/A',
                    expediente.get_estado_actual_display(),
                    expediente.fecha_creacion.strftime('%d/%m/%Y'),
                    expediente.creado_por.username if expediente.creado_por else 'N/A'
                ])
            
            return response
            
        elif formato == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="reporte_expedientes_{fecha_inicio}_{fecha_fin}.json"'
            
            data = []
            for expediente in datos:
                data.append({
                    'numero': expediente.numero_expediente,
                    'titulo': expediente.titulo,
                    'tipo': expediente.get_tipo_expediente_display(),
                    'departamento': expediente.departamento.nombre if expediente.departamento else 'N/A',
                    'estado': expediente.get_estado_actual_display(),
                    'fecha_creacion': expediente.fecha_creacion.strftime('%d/%m/%Y'),
                    'creado_por': expediente.creado_por.username if expediente.creado_por else 'N/A'
                })
            
            response.write(json.dumps(data, indent=2, ensure_ascii=False))
            return response
    
    elif tipo_reporte == 'usuarios':
        datos = User.objects.annotate(
            total_expedientes=Count('expedientes_creados'),
            total_documentos=Count('documentoexpediente')
        ).filter(
            total_expedientes__gt=0
        ).order_by('-total_expedientes')
        
        if formato == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_usuarios_{fecha_inicio}_{fecha_fin}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Usuario', 'Nombre Completo', 'Email', 'Expedientes Creados', 'Documentos Subidos', 'Fecha Registro'])
            
            for usuario in datos:
                writer.writerow([
                    usuario.username,
                    usuario.get_full_name() or 'N/A',
                    usuario.email or 'N/A',
                    usuario.total_expedientes,
                    usuario.total_documentos,
                    usuario.date_joined.strftime('%d/%m/%Y')
                ])
            
            return response
            
        elif formato == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="reporte_usuarios_{fecha_inicio}_{fecha_fin}.json"'
            
            data = []
            for usuario in datos:
                data.append({
                    'username': usuario.username,
                    'nombre_completo': usuario.get_full_name() or 'N/A',
                    'email': usuario.email or 'N/A',
                    'total_expedientes': usuario.total_expedientes,
                    'total_documentos': usuario.total_documentos,
                    'fecha_registro': usuario.date_joined.strftime('%d/%m/%Y')
                })
            
            response.write(json.dumps(data, indent=2, ensure_ascii=False))
            return response
    
    elif tipo_reporte == 'documentos':
        datos = DocumentoExpediente.objects.filter(
            fecha_subida__date__range=[fecha_inicio_dt, fecha_fin_dt]
        ).select_related('expediente', 'subido_por')
        
        if formato == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_documentos_{fecha_inicio}_{fecha_fin}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Nombre', 'Expediente', 'Etapa', 'Subido por', 'Fecha Subida', 'Tamaño'])
            
            for documento in datos:
                writer.writerow([
                    documento.nombre_documento,
                    documento.expediente.numero_expediente if documento.expediente else 'N/A',
                    documento.etapa,
                    documento.subido_por.username if documento.subido_por else 'N/A',
                    documento.fecha_subida.strftime('%d/%m/%Y %H:%M'),
                    f"{documento.tamaño_archivo / 1024:.1f} KB" if documento.tamaño_archivo else 'N/A'
                ])
            
            return response
            
        elif formato == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="reporte_documentos_{fecha_inicio}_{fecha_fin}.json"'
            
            data = []
            for documento in datos:
                data.append({
                    'nombre': documento.nombre_documento,
                    'expediente': documento.expediente.numero_expediente if documento.expediente else 'N/A',
                    'etapa': documento.etapa,
                    'subido_por': documento.subido_por.username if documento.subido_por else 'N/A',
                    'fecha_subida': documento.fecha_subida.strftime('%d/%m/%Y %H:%M'),
                    'tamaño': f"{documento.tamaño_archivo / 1024:.1f} KB" if documento.tamaño_archivo else 'N/A'
                })
            
            response.write(json.dumps(data, indent=2, ensure_ascii=False))
            return response
    
    # Reporte por defecto
    return HttpResponse("Tipo de reporte no válido. Use: expedientes, usuarios, o documentos")


def exportar_grafico(request):
    """Vista para exportar datos de gráficos específicos"""
    from django.http import HttpResponse
    from django.db.models import Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    import csv
    import json
    
    # Obtener parámetros
    tipo_grafico = request.GET.get('tipo', '')
    formato = request.GET.get('formato', 'csv')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    # Calcular fechas por defecto si no se proporcionan
    now = timezone.now()
    today = now.date()
    
    if not fecha_inicio or not fecha_fin:
        fecha_inicio = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_fin = today.strftime('%Y-%m-%d')
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except:
        fecha_inicio_dt = today - timedelta(days=30)
        fecha_fin_dt = today
    
    # Obtener datos según el tipo de gráfico
    if tipo_grafico == 'expedientes_mes':
        # Expedientes por mes (últimos 12 meses)
        datos = []
        for i in range(12):
            fecha = now - timedelta(days=30*i)
            mes = fecha.strftime('%Y-%m')
            total = Expediente.objects.filter(
                fecha_creacion__year=fecha.year,
                fecha_creacion__month=fecha.month
            ).count()
            datos.append({'mes': mes, 'total': total})
        
        datos.reverse()
        
    elif tipo_grafico == 'expedientes_tipo':
        # Expedientes por tipo
        datos = list(Expediente.objects.values('tipo_expediente').annotate(
            total=Count('id')
        ).order_by('-total'))
        
    elif tipo_grafico == 'expedientes_estado':
        # Expedientes por estado
        datos = list(Expediente.objects.values('estado_actual').annotate(
            total=Count('id')
        ).order_by('-total'))
        
    elif tipo_grafico == 'usuarios_activos':
        # Usuarios más activos
        datos = list(User.objects.annotate(
            total_expedientes=Count('expedientes_creados')
        ).filter(
            total_expedientes__gt=0
        ).order_by('-total_expedientes')[:10])
        
    else:
        return HttpResponse("Tipo de gráfico no válido")
    
    # Exportar en el formato solicitado
    if formato == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{tipo_grafico}_{fecha_inicio}_{fecha_fin}.csv"'
        
        writer = csv.writer(response)
        
        if tipo_grafico == 'expedientes_mes':
            writer.writerow(['Mes', 'Total Expedientes'])
            for item in datos:
                writer.writerow([item['mes'], item['total']])
        elif tipo_grafico == 'expedientes_tipo':
            writer.writerow(['Tipo de Expediente', 'Total'])
            for item in datos:
                writer.writerow([item['tipo_expediente'] or 'Sin Tipo', item['total']])
        elif tipo_grafico == 'expedientes_estado':
            writer.writerow(['Estado', 'Total'])
            for item in datos:
                writer.writerow([item['estado_actual'] or 'Sin Estado', item['total']])
        elif tipo_grafico == 'usuarios_activos':
            writer.writerow(['Usuario', 'Total Expedientes'])
            for item in datos:
                writer.writerow([item['username'], item['total_expedientes']])
        
        return response
        
    elif formato == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{tipo_grafico}_{fecha_inicio}_{fecha_fin}.json"'
        
        # Preparar datos para JSON
        if tipo_grafico == 'expedientes_mes':
            json_data = {
                'tipo': 'expedientes_por_mes',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'datos': datos
            }
        elif tipo_grafico == 'expedientes_tipo':
            json_data = {
                'tipo': 'expedientes_por_tipo',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'datos': datos
            }
        elif tipo_grafico == 'expedientes_estado':
            json_data = {
                'tipo': 'expedientes_por_estado',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'datos': datos
            }
        elif tipo_grafico == 'usuarios_activos':
            json_data = {
                'tipo': 'usuarios_activos',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'datos': datos
            }
        
        response.write(json.dumps(json_data, indent=2, ensure_ascii=False))
        return response
    
    return HttpResponse("Formato no válido. Use: csv o json")


def exportar_tabla(request):
    """Vista para exportar tablas específicas"""
    from django.http import HttpResponse
    from django.db.models import Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    import csv
    import json
    
    # Obtener parámetros
    tipo_tabla = request.GET.get('tipo', '')
    formato = request.GET.get('formato', 'csv')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    # Calcular fechas por defecto si no se proporcionan
    now = timezone.now()
    today = now.date()
    
    if not fecha_inicio or not fecha_fin:
        fecha_inicio = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_fin = today.strftime('%Y-%m-%d')
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except:
        fecha_inicio_dt = today - timedelta(days=30)
        fecha_fin_dt = today
    
    # Obtener datos según el tipo de tabla
    if tipo_tabla == 'departamentos':
        # Expedientes por departamento
        datos = list(Expediente.objects.values('departamento__nombre').annotate(
            total=Count('id')
        ).order_by('-total')[:10])
        
        # Calcular porcentajes
        total_general = sum(item['total'] for item in datos)
        for item in datos:
            if total_general > 0:
                item['porcentaje'] = round((item['total'] / total_general) * 100, 1)
            else:
                item['porcentaje'] = 0
        
    else:
        return HttpResponse("Tipo de tabla no válido")
    
    # Exportar en el formato solicitado
    if formato == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{tipo_tabla}_{fecha_inicio}_{fecha_fin}.csv"'
        
        writer = csv.writer(response)
        
        if tipo_tabla == 'departamentos':
            writer.writerow(['Departamento', 'Total Expedientes', 'Porcentaje'])
            for item in datos:
                writer.writerow([
                    item['departamento__nombre'] or 'Sin Departamento',
                    item['total'],
                    f"{item['porcentaje']}%"
                ])
        
        return response
        
    elif formato == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{tipo_tabla}_{fecha_inicio}_{fecha_fin}.json"'
        
        json_data = {
            'tipo': tipo_tabla,
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
            'datos': datos
        }
        
        response.write(json.dumps(json_data, indent=2, ensure_ascii=False))
        return response
    
    return HttpResponse("Formato no válido. Use: csv o json")


def configuracion(request):
    """Vista para configuración del sistema"""
    return render(request, 'digitalizacion/configuracion.html')







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
    
    return render(request, 'digitalizacion/admin/departamentos/gestionar_departamentos.html', context)


# API Views

def api_estadisticas(request):
    """API para obtener estadísticas del sistema"""
    estadisticas = {
        'total_expedientes': Expediente.objects.count(),
        'expedientes_por_estado': dict(
            Expediente.objects.values('estado_actual').annotate(
                total=Count('estado_actual')
            ).values_list('estado_actual', 'total')
        ),
        'expedientes_por_tipo': dict(
            Expediente.objects.values('tipo_expediente').annotate(
                total=Count('tipo_expediente')
            ).values_list('tipo_expediente', 'total')
        ),
    }
    
    return JsonResponse(estadisticas)


@require_GET
def api_expedientes_por_tipo(request):
    """
    API para obtener el conteo de expedientes por tipo
    Solo muestra los tipos específicos: Licitación, Compra Directa, Concurso por Invitación, Adjudicación Directa
    """
    try:
        # Definir los tipos de expediente que queremos mostrar
        tipos_a_mostrar = {
            'licitacion': 'Licitación',
            'compra_directa': 'Compra Directa',
            'concurso_invitacion': 'Concurso por Invitación',
            'adjudicacion_directa': 'Adjudicación Directa'
        }
        
        # Obtener el conteo de expedientes por tipo, solo para los tipos que nos interesan
        tipos_expediente = Expediente.objects.filter(
            tipo_expediente__in=tipos_a_mostrar.keys()
        ).values('tipo_expediente').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Crear un diccionario con los resultados para búsqueda rápida
        conteos = {item['tipo_expediente']: item['total'] for item in tipos_expediente}
        
        # Crear la lista de resultados con todos los tipos, incluso si tienen 0
        resultado = []
        for codigo, nombre in tipos_a_mostrar.items():
            resultado.append({
                'tipo': nombre,
                'total': conteos.get(codigo, 0)
            })
        
        # Ordenar por cantidad (mayor a menor)
        resultado.sort(key=lambda x: x['total'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'data': resultado,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_usuarios_conectados(request):
    """
    API para obtener la lista de usuarios conectados
    
    Returns:
        JsonResponse: Lista de usuarios conectados con su información
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Importar timezone aquí para evitar problemas de importación circular
            from django.utils import timezone
            
            logger.info("Iniciando api_usuarios_conectados")
            
            # Considerar usuarios activos en los últimos 5 minutos
            threshold = timezone.now() - timezone.timedelta(minutes=5)
            logger.info(f"Threshold calculado: {threshold}")
            
            # Obtener IDs de usuarios únicos que están conectados
            usuarios_conectados_ids = list(UserSession.objects.filter(
                is_online=True,
                last_activity__gte=threshold
            ).values_list('user_id', flat=True).distinct())
            
            logger.info(f"IDs de usuarios conectados encontrados: {usuarios_conectados_ids}")
            
            # Si no hay usuarios conectados, devolver lista vacía
            if not usuarios_conectados_ids:
                return JsonResponse({
                    'status': 'success',
                    'total': 0,
                    'usuarios': [],
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Obtener los objetos de usuario con sus perfiles
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            usuarios = []
            for user in User.objects.filter(id__in=usuarios_conectados_ids).select_related('perfil'):
                try:
                    # Obtener la última sesión para este usuario
                    ultima_sesion = UserSession.objects.filter(
                        user=user,
                        is_online=True,
                        last_activity__gte=threshold
                    ).order_by('-last_activity').first()
                    
                    if ultima_sesion:
                        # Manejar el avatar de manera segura
                        avatar_url = None
                        try:
                            if hasattr(user, 'perfil') and hasattr(user.perfil, 'avatar') and user.perfil.avatar:
                                avatar_url = user.perfil.avatar.url
                        except Exception as e:
                            logger.warning(f"Error al obtener avatar para usuario {user.id}: {str(e)}")
                        
                        # Manejar el rol de manera segura
                        rol = 'Usuario'
                        try:
                            if hasattr(user, 'perfil') and hasattr(user.perfil, 'rol') and user.perfil.rol:
                                rol = user.perfil.rol.nombre
                        except Exception as e:
                            logger.warning(f"Error al obtener rol para usuario {user.id}: {str(e)}")
                        
                        usuarios.append({
                            'id': user.id,
                            'username': user.username,
                            'nombre_completo': user.get_full_name() or user.username,
                            'ultima_actividad': ultima_sesion.last_activity.strftime('%Y-%m-%d %H:%M:%S'),
                            'esta_activo': (timezone.now() - ultima_sesion.last_activity).seconds < 300,
                            'avatar_url': avatar_url,
                            'rol': rol
                        })
                except Exception as e:
                    logger.error(f"Error procesando usuario {getattr(user, 'id', 'unknown')}: {str(e)}", exc_info=True)
            
            logger.info(f"Devolviendo {len(usuarios)} usuarios conectados")
            
            return JsonResponse({
                'status': 'success',
                'total': len(usuarios),
                'usuarios': usuarios,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.error("Error en api_usuarios_conectados", exc_info=True)
            return JsonResponse(
                {"status": "error", "message": f"Error interno del servidor: {str(e)}"}, 
                status=500
            )
            
    except Exception as e:
        # Esto capturará cualquier error en el manejo de la solicitud
        import traceback
        error_msg = f"Error inesperado: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Para ver en la consola
        return JsonResponse(
            {"status": "error", "message": "Error interno del servidor"}, 
            status=500
        )

@require_http_methods(["GET"])
def api_expedientes_semanales(request):
    """
    API para obtener estadísticas de expedientes por día (últimos 7 días)
    """
    try:
        from django.utils import timezone
        from datetime import timedelta, datetime
        from django.db.models import Count
        from .models import Expediente
        
        hoy = timezone.now().date()
        data = []
        labels = []
        
        # Obtener datos de los últimos 7 días
        for i in range(6, -1, -1):
            fecha = hoy - timedelta(days=i)
            
            # Contar expedientes del día
            conteo = Expediente.objects.filter(
                fecha_creacion__date=fecha
            ).count()
            
            data.append(conteo)
            # Formatear la fecha como 'Lun 1', 'Mar 2', etc.
            labels.append(fecha.strftime('%a %d'))
        
        return JsonResponse({
            'success': True,
            'data': data,
            'labels': labels,
            'start_date': (hoy - timedelta(days=6)).strftime('%Y-%m-%d'),
            'end_date': hoy.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en api_expedientes_semanales: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_expedientes_mensuales(request):
    """
    API para obtener estadísticas de expedientes por mes (últimos 12 meses)
    """
    try:
        from django.utils import timezone
        from datetime import datetime, timedelta
        from django.db.models.functions import TruncMonth
        from django.db.models import Count
        from django.http import JsonResponse
        from .models import Expediente
        
        hoy = timezone.now().date()
        primer_dia_mes_actual = hoy.replace(day=1)
        
        # Obtener datos de los últimos 12 meses
        expedientes_mes = Expediente.objects.filter(
            fecha_creacion__date__gte=primer_dia_mes_actual - timedelta(days=365)
        ).annotate(
            mes=TruncMonth('fecha_creacion')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')
        
        # Crear un diccionario con todos los meses del último año
        meses = {}
        for i in range(12):
            fecha = (primer_dia_mes_actual - timedelta(days=30*i)).replace(day=1)
            meses[fecha.strftime('%Y-%m')] = 0
        
        # Actualizar con datos reales
        for item in expedientes_mes:
            mes_key = item['mes'].strftime('%Y-%m')
            if mes_key in meses:
                meses[mes_key] = item['total']
        
        # Ordenar los meses
        meses_ordenados = sorted(meses.items())
        
        # Preparar datos para la respuesta
        data = [valor for _, valor in meses_ordenados]
        labels = [datetime.strptime(mes, '%Y-%m').strftime('%b %Y') for mes, _ in meses_ordenados]
        
        return JsonResponse({
            'success': True,
            'data': data,
            'labels': labels,
            'start_date': (primer_dia_mes_actual - timedelta(days=365)).strftime('%Y-%m-%d'),
            'end_date': hoy.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en api_expedientes_mensuales: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_GET
def api_expedientes_por_mes(request):
    """
    API para obtener estadísticas de expedientes por mes para el año 2025
    """
    try:
        from django.utils import timezone
        from datetime import datetime
        from django.db.models.functions import ExtractMonth, ExtractYear
        from django.db.models import Count, Q
        
        # Definir el rango de fechas para 2025
        fecha_inicio = datetime(2025, 1, 1).date()
        fecha_fin = datetime(2025, 12, 31).date()
            
        # Obtener los datos agrupados por mes para 2025
        expedientes_por_mes = Expediente.objects.filter(
            fecha_creacion__year=2025
        ).annotate(
            mes=ExtractMonth('fecha_creacion')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')
        
        # Crear un diccionario con los meses del año
        meses_espanol = [
            'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ]
        
        # Inicializar datos para todos los meses con 0
        datos_dict = {mes: 0 for mes in range(1, 13)}
        
        # Actualizar con los datos reales
        for item in expedientes_por_mes:
            datos_dict[item['mes']] = item['total']
        
        # Preparar etiquetas y datos ordenados
        etiquetas = []
        datos = []
        
        for mes in range(1, 13):
            etiquetas.append(f"{meses_espanol[mes-1]} 2025")
            datos.append(datos_dict[mes])
        
        return JsonResponse({
            'success': True,
            'labels': etiquetas,
            'data': datos,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en api_expedientes_por_mes: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        logger = logging.getLogger(__name__)
        logger.error(f"Error en api_expedientes_por_mes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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
    """Vista para el registro de nuevos usuarios"""
    if request.method == 'POST':
        form = SolicitudRegistroForm(request.POST)
        if form.is_valid():
            # Guardar la solicitud de registro
            solicitud = form.save(commit=False)
            
            # Si hay un usuario autenticado con permisos de administrador, aprobar automáticamente
            if request.user.is_authenticated and request.user.has_perm('digitalizacion.puede_aprobar_usuarios'):
                # Si es un administrador, aprobar automáticamente
                solicitud.estado = 'aprobada'
                solicitud.save()
                
                # Crear el usuario directamente
                usuario = User.objects.create_user(
                    username=form.cleaned_data['email_institucional'],
                    email=form.cleaned_data['email_institucional'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['nombres'],
                    last_name=form.cleaned_data['apellidos']
                )
                
                # Crear el perfil del usuario
                perfil = PerfilUsuario.objects.create(
                    usuario=usuario,
                    departamento=form.cleaned_data['departamento'],
                    puesto=form.cleaned_data['puesto'],
                    telefono=form.cleaned_data['telefono'],
                    extension=form.cleaned_data['extension']
                )
                
                # Asignar el rol solicitado
                perfil.rol = form.cleaned_data['rol_solicitado']
                perfil.save()
                
                # Actualizar la solicitud con el usuario creado
                solicitud.usuario_creado = usuario
                solicitud.resuelto_por = request.user
                solicitud.fecha_resolucion = timezone.now()
                solicitud.save()
                
                messages.success(request, f'¡Usuario {usuario.get_full_name()} creado y aprobado exitosamente!')
                return redirect('digitalizacion:panel_administracion')
            else:
                # Para usuarios no autenticados o sin permisos, crear solo la solicitud
                solicitud.save()
                
                # Notificar a los administradores
                admin_users = User.objects.filter(
                    perfil__rol__puede_aprobar_usuarios=True
                ).distinct()
                
                for admin in admin_users:
                    Notificacion.objects.create(
                        usuario=admin,
                        tipo='solicitud_registro',
                        titulo='Nueva solicitud de registro',
                        mensaje=f'Nueva solicitud de registro de {solicitud.nombre_completo()} ({solicitud.email_institucional})',
                        generada_por=request.user if request.user.is_authenticated else None,
                        enlace=reverse('digitalizacion:panel_administracion') + f'?tab=solicitudes'
                    )
                
                messages.success(
                    request,
                    '¡Solicitud de registro enviada con éxito! ' \
                    'Un administrador revisará tu solicitud y te notificará por correo electrónico cuando sea aprobada.'
                )
                return redirect('digitalizacion:login')
    else:
        # Si es un administrador, mostrar el formulario con todos los roles disponibles
        if request.user.is_authenticated and request.user.has_perm('digitalizacion.puede_aprobar_usuarios'):
            form = SolicitudRegistroForm()
        else:
            # Para usuarios no autenticados, solo mostrar roles no administrativos
            form = SolicitudRegistroForm()
            form.fields['rol_solicitado'].queryset = RolUsuario.objects.filter(
                puede_administrar_sistema=False
            )
    
    return render(request, 'digitalizacion/auth/register.html', {'form': form})


def user_logout(request):
    """Vista simple para logout"""
    user_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else "Usuario"
    logout(request)
    messages.success(request, f'¡Hasta luego, {user_name}! Has cerrado sesión exitosamente.')
    return redirect('digitalizacion:login')


@login_required
def perfil_usuario(request):
    """Vista para mostrar el perfil del usuario"""
    # Obtener estadísticas del usuario
    expedientes_creados = Expediente.objects.filter(creado_por=request.user).count()
    documentos_subidos = DocumentoExpediente.objects.filter(subido_por=request.user).count()
    
    # Obtener notificaciones no leídas
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-fecha_creacion')[:10]
    
    context = {
        'expedientes_creados': expedientes_creados,
        'documentos_subidos': documentos_subidos,
        'notificaciones': notificaciones,
        'usuario': request.user,
    }
    return render(request, 'digitalizacion/perfil/perfil_usuario.html', context)


def user_profile(request):
    """Vista de perfil con estadísticas detalladas (alias para compatibilidad)"""
    return perfil_usuario(request)


@login_required
def editar_perfil(request):
    """Vista para editar el perfil del usuario actual"""
    user = request.user
    
    if request.method == 'POST':
        # Actualizar información básica del usuario
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Actualizar información del perfil
        if hasattr(user, 'perfil'):
            user.perfil.puesto = request.POST.get('puesto', '')
            user.perfil.telefono = request.POST.get('telefono', '')
            user.perfil.extension = request.POST.get('extension', '')
            
            # Manejar foto de perfil
            if 'foto_perfil' in request.FILES:
                # Eliminar foto anterior si existe
                if user.perfil.foto_perfil:
                    user.perfil.foto_perfil.delete(save=False)
                user.perfil.foto_perfil = request.FILES['foto_perfil']
            
            user.perfil.save()
        
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('digitalizacion:profile')
    
    context = {
        'user': user
    }
    return render(request, 'digitalizacion/auth/editar_perfil.html', context)

@login_required
def cambiar_password_actual(request):
    """Vista para que el usuario cambie su propia contraseña"""
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual')
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')
        
        # Verificar contraseña actual
        if not request.user.check_password(password_actual):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return render(request, 'digitalizacion/auth/cambiar_password_actual.html')
        
        # Validar nueva contraseña
        if not nueva_password:
            messages.error(request, 'La nueva contraseña es requerida.')
            return render(request, 'digitalizacion/auth/cambiar_password_actual.html')
        
        if nueva_password != confirmar_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'digitalizacion/auth/cambiar_password_actual.html')
        
        if len(nueva_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'digitalizacion/auth/cambiar_password_actual.html')
        
        # Cambiar la contraseña
        request.user.set_password(nueva_password)
        request.user.save()
        
        # Actualizar la sesión para evitar que se cierre
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Tu contraseña ha sido actualizada exitosamente.')
        return redirect('digitalizacion:profile')
    
    return render(request, 'digitalizacion/auth/cambiar_password_actual.html')

@login_required
def marcar_notificaciones_leidas(request):
    """Vista para marcar todas las notificaciones del usuario como leídas"""
    if request.method == 'POST':
        try:
            # Marcar todas las notificaciones no leídas como leídas
            notificaciones = Notificacion.objects.filter(
                usuario=request.user,
                leida=False
            )
            notificaciones.update(leida=True, fecha_leido=timezone.now())
            
            return JsonResponse({'success': True, 'message': 'Notificaciones marcadas como leídas'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


def ayuda(request):
    """
    Vista para mostrar la página de ayuda del sistema
    """
    context = {
        'titulo': 'Centro de Ayuda',
        'secciones': [
            {
                'titulo': 'Inicio Rápido',
                'contenido': 'Bienvenido al sistema de digitalización de documentos. Aquí podrás gestionar todos tus expedientes y documentos de manera eficiente.'
            },
            {
                'titulo': 'Gestión de Expedientes',
                'contenido': 'Crea, edita y gestiona tus expedientes. Puedes asignarlos a diferentes áreas y realizar un seguimiento de su estado.'
            },
            {
                'titulo': 'Subida de Documentos',
                'contenido': 'Sube documentos a tus expedientes. Asegúrate de seleccionar el tipo de documento correcto.'
            },
            {
                'titulo': 'Búsqueda Avanzada',
                'contenido': 'Utiliza la búsqueda avanzada para encontrar rápidamente expedientes o documentos específicos.'
            },
            {
                'titulo': 'Notificaciones',
                'contenido': 'Mantente informado sobre las actualizaciones de tus expedientes a través del sistema de notificaciones.'
            },
            {
                'titulo': 'Soporte Técnico',
                'contenido': 'Si necesitas ayuda adicional, por favor contacta al equipo de soporte técnico en soporte@sistema.com'
            }
        ]
    }
    
    return render(request, 'ayuda/ayuda.html', context)


def acerca_de(request):
    """
    Vista para mostrar información sobre el sistema
    """
    context = {
        'titulo': 'Acerca del Sistema',
        'sistema': {
            'nombre': 'Sistema de Digitalización de Documentos',
            'version': '1.0.0',
            'descripcion': 'Plataforma integral para la gestión y seguimiento de documentos y expedientes digitales.',
            'anio': datetime.now().year
        },
        'caracteristicas': [
            'Gestión centralizada de documentos',
            'Seguimiento de expedientes',
            'Búsqueda avanzada',
            'Notificaciones en tiempo real',
            'Interfaz intuitiva y fácil de usar',
            'Seguridad y control de acceso'
        ],
        'contacto': {
            'email': 'contacto@sistema.com',
            'telefono': '+52 123 456 7890',
            'direccion': 'Av. Principal #123, Col. Centro, Ciudad de México'
        }
    }
    
    return render(request, 'acerca/acerca_de.html', context)


def panel_administracion(request):
    """
    Vista para el panel de administración del sistema
    """
    # Verificar si el usuario tiene permisos de administrador
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'No tiene permisos para acceder al panel de administración.')
        return redirect('digitalizacion:inicio')
    
    # Obtener estadísticas para el panel de administración
    from django.contrib.auth import get_user_model
    from .models import Expediente, DocumentoExpediente
    
    User = get_user_model()
    
    # Estadísticas de usuarios
    total_usuarios = User.objects.count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    usuarios_staff = User.objects.filter(is_staff=True).count()
    
    # Estadísticas de expedientes
    total_expedientes = Expediente.objects.count()
    expedientes_activos = Expediente.objects.filter(estado__in=['en_progreso', 'pendiente']).count()
    expedientes_completados = Expediente.objects.filter(
        Q(estado='completo') | Q(estado_actual='completado')
    ).count()
    
    # Estadísticas de documentos
    total_documentos = DocumentoExpediente.objects.count()
    documentos_por_tipo = DocumentoExpediente.objects.values('tipo_documento__nombre').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Últimas actividades
    from .models import HistorialExpediente
    ultimas_actividades = HistorialExpediente.objects.select_related('expediente', 'usuario')\
        .order_by('-fecha')[:10]
    
    context = {
        'titulo': 'Panel de Administración',
        'estadisticas_usuarios': {
            'total': total_usuarios,
            'activos': usuarios_activos,
            'staff': usuarios_staff,
        },
        'estadisticas_expedientes': {
            'total': total_expedientes,
            'activos': expedientes_activos,
            'completados': expedientes_completados,
        },
        'estadisticas_documentos': {
            'total': total_documentos,
            'por_tipo': documentos_por_tipo,
        },
        'ultimas_actividades': ultimas_actividades,
    }
    
    return render(request, 'digitalizacion/panel_administracion.html', context)


def contacto(request):
    """
    Vista para manejar el formulario de contacto
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            email = request.POST.get('email', '').strip()
            asunto = request.POST.get('asunto', '').strip()
            mensaje = request.POST.get('mensaje', '').strip()
            
            # Validar campos requeridos
            if not all([nombre, email, asunto, mensaje]):
                messages.error(request, 'Todos los campos son obligatorios')
                return redirect('contacto')
                
            # Aquí iría la lógica para enviar el correo electrónico
            # Por ejemplo, usando send_mail de Django
            # from django.core.mail import send_mail
            # send_mail(
            #     f'Contacto: {asunto}',
            #     f'De: {nombre} <{email}>\n\n{mensaje}',
            #     email,
            #     ['contacto@sistema.com'],
            #     fail_silently=False,
            # )
            
            # Registrar el mensaje en la base de datos
            from .models import MensajeContacto
            MensajeContacto.objects.create(
                nombre=nombre,
                email=email,
                asunto=asunto,
                mensaje=mensaje,
                direccion_ip=request.META.get('REMOTE_ADDR', '')
            )
            
            messages.success(request, 'Tu mensaje ha sido enviado correctamente. Nos pondremos en contacto contigo pronto.')
            return redirect('contacto')
            
        except Exception as e:
            logger.error(f'Error al procesar el formulario de contacto: {str(e)}')
            messages.error(request, 'Ocurrió un error al enviar tu mensaje. Por favor, inténtalo de nuevo más tarde.')
            return redirect('contacto')
    
    # Si es GET, mostrar el formulario
    return render(request, 'contacto/contacto.html', {
        'titulo': 'Contáctanos',
        'informacion_contacto': {
            'email': 'contacto@sistema.com',
            'telefono': '+52 123 456 7890',
            'direccion': 'Av. Principal #123, Col. Centro, Ciudad de México',
            'horario': 'Lunes a Viernes de 9:00 AM a 6:00 PM'
        }
    })


@login_required
def detalle_expediente(request, expediente_id):
    """Vista para mostrar el detalle de un expediente y sus documentos"""
    expediente = get_object_or_404(Expediente, id=expediente_id)
    tipos_documento = TipoDocumento.objects.filter(activo=True)
    
    # Obtener las áreas configuradas para este tipo de expediente
    from .models import AreaTipoExpediente, ValorAreaExpediente
    
    # Obtener el subtipo del expediente (puede ser None)
    subtipo_expediente = getattr(expediente, 'subtipo_expediente', None)
    
    # Obtener todas las áreas activas para este tipo de expediente
    # Primero intentamos filtrar por tipo y subtipo exacto
    areas_query = AreaTipoExpediente.objects.filter(
        tipo_expediente=expediente.tipo_expediente,
        activa=True
    )
    
    # Si hay un subtipo definido, intentamos filtrar por él
    if subtipo_expediente:
        # Primero intentamos con el subtipo exacto
        areas_subtipo = areas_query.filter(
            subtipo_expediente=subtipo_expediente
        )
        
        # Si no encontramos áreas con el subtipo exacto, intentamos con áreas genéricas (sin subtipo)
        if not areas_subtipo.exists():
            areas_subtipo = areas_query.filter(
                subtipo_expediente__isnull=True
            )
    else:
        # Si no hay subtipo, buscamos solo áreas genéricas (sin subtipo)
        areas_subtipo = areas_query.filter(
            subtipo_expediente__isnull=True
        )
    
    # Obtener nombres de áreas únicos para evitar duplicados
    nombres_areas = areas_subtipo.values_list('nombre', flat=True).distinct()
    
    # Obtener el primer objeto para cada nombre de área único
    areas_objs = []
    for nombre in nombres_areas:
        area = areas_subtipo.filter(
            nombre=nombre
        ).order_by('orden').first()
        if area:
            areas_objs.append(area)
    
    # Ordenar áreas por el campo 'orden'
    areas_objs = sorted(areas_objs, key=lambda x: x.orden)
    
    # Obtener el estado de completitud de cada área y crear diccionario de valores
    areas = []
    valores_areas = {}  # Diccionario para almacenar los valores de las áreas
    
    # Calcular el progreso total del expediente
    total_areas = len(areas_objs)
    areas_completadas = 0
    
    if total_areas > 0:
        # Contar áreas completadas
        areas_completadas = sum(1 for area in areas_objs if 
                             ValorAreaExpediente.objects.filter(
                                 expediente=expediente,
                                 area=area,
                                 completada=True
                             ).exists())
        
        # Calcular porcentaje de progreso
        progreso = int((areas_completadas / total_areas) * 100)
    else:
        progreso = 0
    
    for area in areas_objs:
        # Verificar si el área tiene un valor guardado
        valor_area = ValorAreaExpediente.objects.filter(
            expediente=expediente,
            area=area
        ).first()
        
        # Contar documentos en esta área
        documentos_count = expediente.documentos.filter(etapa=area.nombre).count()
        
        # Crear diccionario con la información del área
        area_info = {
            'id': area.id,
            'nombre': area.nombre,
            'titulo': area.titulo,
            'descripcion': area.descripcion,
            'tipo_area': area.tipo_area,
            'obligatoria': area.obligatoria,
            'completada': valor_area.completada if valor_area else False,
            'documentos_count': documentos_count,
            'fecha_completada': valor_area.fecha_completada if valor_area else None,
            'completada_por': valor_area.completada_por if valor_area else None
        }
        
        areas.append(area_info)
        
        # Agregar al diccionario de valores de áreas
        if valor_area:
            valores_areas[str(area.id)] = {
                'valor_texto': valor_area.valor_texto,
                'valor_fecha': valor_area.valor_fecha,
                'valor_datetime': valor_area.valor_datetime,
                'valor_numero': valor_area.valor_numero,
                'valor_json': valor_area.valor_json,
                'completo': valor_area.completada,
                'fecha_completada': valor_area.fecha_completada,
                'completada_por': valor_area.completada_por,
                'documentos': list(expediente.documentos.filter(etapa=area.nombre).values('id', 'nombre', 'archivo'))
            }
    
    # Obtener documentos agrupados por área
    documentos_por_area = {}
    for doc in expediente.documentos.all():
        # Buscar el área correspondiente al documento
        area = AreaTipoExpediente.objects.filter(
            nombre=doc.etapa,
            tipo_expediente=expediente.tipo_expediente
        ).first()
        
        if area:
            area_key = str(area.id)  # Usamos el ID del área como clave
            if area_key not in documentos_por_area:
                documentos_por_area[area_key] = {
                    'area': area,
                    'documentos': []
                }
            documentos_por_area[area_key]['documentos'].append(doc)
        else:
            # Si no encontramos el área, la agrupamos por el nombre de la etapa
            if doc.etapa not in documentos_por_area:
                documentos_por_area[doc.etapa] = {
                    'area': {'titulo': doc.etapa.replace('_', ' ').title(), 'id': doc.etapa},
                    'documentos': []
                }
            documentos_por_area[doc.etapa]['documentos'].append(doc)
    
    # Obtener la última fecha de actualización del expediente
    ultima_actualizacion = expediente.fecha_actualizacion or expediente.fecha_creacion
    
    # Calcular el progreso total del expediente
    total_areas = len(areas_objs)
    areas_completadas = 0
    
    if total_areas > 0:
        # Contar áreas completadas
        areas_completadas = sum(1 for area in areas_objs if 
                             ValorAreaExpediente.objects.filter(
                                 expediente=expediente,
                                 area=area,
                                 completada=True
                             ).exists())
        
        # Calcular porcentaje de progreso
        progreso = int((areas_completadas / total_areas) * 100)
    else:
        progreso = 0
    
    # Actualizar el progreso en el modelo Expediente si es necesario
    if hasattr(expediente, 'progreso'):
        expediente.progreso = progreso
        expediente.etapas_completadas = areas_completadas
        expediente.total_etapas = total_areas
        expediente.save(update_fields=['progreso', 'etapas_completadas', 'total_etapas', 'fecha_actualizacion'])
    
    context = {
        'expediente': expediente,
        'tipos_documento': tipos_documento,
        'documentos_por_area': documentos_por_area,
        'areas': areas,  # Lista de áreas con su información
        'valores_areas': valores_areas,  # Diccionario de valores de áreas para el filtro get_item
        'ultima_actualizacion': ultima_actualizacion,  # Última fecha de actualización
        'progreso': progreso,  # Porcentaje de progreso (0-100)
        'etapas_completadas': areas_completadas,  # Número de áreas completadas
        'total_etapas': total_areas,  # Total de áreas del expediente
    }
    
    return render(request, 'digitalizacion/expedientes/detalle_expediente.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def subir_documento_expediente(request, expediente_id):
    """Vista para subir un documento a un expediente"""
    try:
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Verificar si el archivo está presente
        if 'documento' not in request.FILES:
            return JsonResponse({'error': 'No se ha proporcionado ningún archivo'}, status=400)
        
        archivo = request.FILES['documento']
        nombre_documento = request.POST.get('nombre_documento', archivo.name)
        area_id = request.POST.get('area_id')
        observaciones = request.POST.get('observaciones', '')
        
        # Validar tamaño del archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if archivo.size > max_size:
            return JsonResponse({'error': 'El archivo es demasiado grande. El tamaño máximo permitido es 10MB'}, status=400)
        
        # Validar extensión del archivo
        extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
        nombre_archivo = archivo.name.lower()
        if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
            return JsonResponse({'error': 'Tipo de archivo no permitido. Formatos aceptados: PDF, Word, Excel, JPG, PNG'}, status=400)
        
        # Crear el directorio si no existe
        directorio = os.path.join('expedientes', str(expediente.id), 'documentos')
        os.makedirs(os.path.join(settings.MEDIA_ROOT, directorio), exist_ok=True)
        
        # Generar un nombre único para el archivo
        nombre_archivo = f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
        ruta_archivo = os.path.join(directorio, nombre_archivo)
        
        # Guardar el archivo
        ruta_completa = default_storage.save(ruta_archivo, archivo)
        
        # Obtener o crear un tipo de documento por defecto
        tipo_documento, _ = TipoDocumento.objects.get_or_create(
            nombre='Documento General',
            defaults={'descripcion': 'Documento general del expediente'}
        )
            
        # Depuración: Imprimir información del área
        print(f"Área recibida: {area_id} (tipo: {type(area_id)})")
        
        # Obtener las áreas válidas para este tipo de expediente
        try:
            area = AreaTipoExpediente.objects.get(
                id=area_id,
                tipo_expediente=expediente.tipo_expediente,
                activa=True
            )
            print(f"Área encontrada: {area.titulo} (ID: {area.id})")
            
        except AreaTipoExpediente.DoesNotExist:
            # Si no se encuentra el área, obtener la lista de áreas válidas para el mensaje de error
            areas_validas = AreaTipoExpediente.objects.filter(
                tipo_expediente=expediente.tipo_expediente,
                activa=True
            ).values_list('id', 'titulo')
            
            print(f"Área {area_id} no encontrada en las áreas configuradas")
            return JsonResponse({
                'error': 'Área no válida. Por favor, seleccione un área válida del sistema.',
                'area_solicitada': area_id,
                'areas_disponibles': list(areas_validas)
            }, status=400)
        
        # Usar el ID del área encontrada
        area_id = area.id
        
        # Crear el documento en la base de datos
        try:
            documento = DocumentoExpediente.objects.create(
                expediente=expediente,
                nombre_documento=nombre_documento,
                archivo=ruta_archivo,
                descripcion=observaciones,
                subido_por=request.user,
                tamaño_archivo=archivo.size,
                tipo_archivo=archivo.name.split('.')[-1].lower(),
                etapa=area.nombre,  # Mantener para compatibilidad
                area=area  # Nuevo campo de relación
            )
            print(f"Documento creado con éxito. ID: {documento.id}, Área: {documento.etapa}")
            
            # Actualizar la fecha de actualización del expediente
            expediente.fecha_actualizacion = timezone.now()
            expediente.save(update_fields=['fecha_actualizacion'])
            print(f"Fecha de actualización del expediente actualizada a: {expediente.fecha_actualizacion}")
        except Exception as e:
            print(f"Error al crear el documento: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'error': f'Error al guardar el documento en la base de datos: {str(e)}'
            }, status=500)
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=request.user,
            titulo='Nuevo documento subido',
            mensaje=f'Se ha subido un nuevo documento al expediente {expediente.numero_expediente}',
            tipo='documento',
            enlace=f'/expedientes/{expediente.id}/',
            generada_por=request.user,
            expediente=expediente
        )
        
        # Obtener los datos del documento para la respuesta
        documento_data = {
            'id': documento.id,
            'nombre_documento': documento.nombre_documento,
            'archivo': documento.archivo.name,
            'archivo_url': request.build_absolute_uri(documento.archivo.url),
            'fecha_subida': documento.fecha_subida.isoformat(),
            'subido_por': request.user.get_full_name() or request.user.username,
            'subido_por_id': request.user.id,
            'tipo_archivo': os.path.splitext(documento.archivo.name)[1][1:],
            'tamaño_archivo': documento.tamaño_archivo,
            'tamaño_archivo_formateado': documento.tamaño_archivo_formateado,
            'etapa': documento.etapa
        }
        
        return JsonResponse({
            'success': True,
            'documento': documento_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def obtener_documentos_por_area(request, expediente_id, area_id):
    """API para obtener los documentos de un área específica de un expediente"""
    try:
        # Verificar que el expediente existe
        expediente = get_object_or_404(Expediente, id=expediente_id)
        
        # Normalizar el ID del área (eliminar acentos y convertir a minúsculas)
        import unicodedata
        def normalize_text(text):
            return ''.join(c for c in unicodedata.normalize('NFD', str(text).lower()) 
                         if unicodedata.category(c) != 'Mn').replace(' ', '_')
        
        area_id_normalized = normalize_text(area_id)
        
        # Buscar el área por ID o nombre normalizado
        area = None
        
        # 1. Intentar por ID numérico
        try:
            area = AreaTipoExpediente.objects.get(id=area_id)
            print(f"Área encontrada por ID: {area.nombre} (ID: {area.id})")
        except (ValueError, AreaTipoExpediente.DoesNotExist):
            # 2. Si no es un ID numérico o no se encuentra, buscar por nombre normalizado
            areas = AreaTipoExpediente.objects.all()
            for a in areas:
                if normalize_text(a.nombre) == area_id_normalized:
                    area = a
                    print(f"Área encontrada por nombre normalizado: {area.nombre} (ID: {area.id})")
                    break
        
        # Si no se encontró el área, devolver error
        if not area:
            return JsonResponse({
                'success': False,
                'error': 'Área no encontrada',
                'area_solicitada': area_id,
                'sugerencia': 'Verifique el nombre del área o el ID proporcionado',
                'areas_disponibles': [
                    {'id': a.id, 'nombre': a.nombre, 'nombre_normalizado': normalize_text(a.nombre)}
                    for a in AreaTipoExpediente.objects.all()
                ]
            }, status=404)
        
        # Verificar si el área está asociada al tipo de expediente
        if area.tipo_expediente != expediente.tipo_expediente:
            return JsonResponse({
                'success': False,
                'error': 'Área no asociada',
                'area_solicitada': area.nombre,
                'area_id': area.id,
                'tipo_expediente_area': area.tipo_expediente.nombre if area.tipo_expediente else 'No definido',
                'tipo_expediente_expediente': expediente.tipo_expediente.nombre if expediente.tipo_expediente else 'No definido',
                'sugerencia': f'El área {area.nombre} no está asociada al tipo de expediente {expediente.get_tipo_expediente_display() if expediente.tipo_expediente else "desconocido"}.'
            }, status=400)
        
        # Buscar documentos por el campo 'area' (relación directa)
        documentos = DocumentoExpediente.objects.filter(
            expediente=expediente,
            area=area
        ).select_related('subido_por').order_by('-fecha_subida')
        
        # Si no hay documentos, buscar en el campo 'etapa' para mantener compatibilidad
        if not documentos.exists():
            print("No se encontraron documentos en el área especificada. Buscando en el campo 'etapa' para compatibilidad...")
            
            documentos = DocumentoExpediente.objects.filter(
                Q(expediente=expediente) &
                (Q(etapa=str(area.id)) | 
                 Q(etapa__iexact=area.nombre))
            ).select_related('subido_por').order_by('-fecha_subida')
        
        # Preparar la respuesta
        documentos_list = []
        for doc in documentos:
            try:
                # Obtener información del archivo
                if doc.archivo:
                    archivo_url = doc.archivo.url
                    nombre_archivo = os.path.basename(str(doc.archivo))
                    extension = os.path.splitext(nombre_archivo)[1].lower()
                else:
                    archivo_url = ''
                    nombre_archivo = ''
                    extension = ''
                
                # Crear el diccionario del documento
                doc_dict = {
                    'id': doc.id,
                    'nombre': doc.nombre_documento,
                    'nombre_documento': doc.nombre_documento,
                    'archivo': nombre_archivo,
                    'archivo_url': archivo_url,
                    'url': archivo_url,  # Para compatibilidad con el frontend
                    'fecha_subida': doc.fecha_subida.isoformat(),
                    'fecha_subida_formateada': doc.fecha_subida.strftime('%Y-%m-%d %H:%M:%S'),
                    'subido_por': doc.subido_por.get_full_name() if doc.subido_por else 'Usuario desconocido',
                    'tipo_archivo': extension.lstrip('.').lower(),
                    'tipo': extension.lstrip('.').lower(),  # Para compatibilidad
                    'tamano': getattr(doc, 'tamaño_archivo', 0) or 0,
                    'tamaño_archivo': getattr(doc, 'tamaño_archivo', 0) or 0,
                    'tamaño_archivo_formateado': getattr(doc, 'tamaño_archivo_formateado', '0 Bytes'),
                    'etapa': doc.etapa,
                    'observaciones': getattr(doc, 'observaciones', '')
                }
                documentos_list.append(doc_dict)
                
            except Exception as e:
                import traceback
                print(f"Error procesando documento {getattr(doc, 'id', 'desconocido')}:")
                print(traceback.format_exc())
                continue
        
        # Devolver directamente el array de documentos para compatibilidad con el frontend
        return JsonResponse(documentos_list, safe=False)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("Error en obtener_documentos_por_area:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("Traceback:")
        print(error_trace)
        
        # Asegurarse de que el mensaje de error no contenga referencias a atributos incorrectos
        error_message = str(e).replace("'Expediente' object has no attribute 'numero'", 
                                     "Error al obtener los documentos del área: número de expediente no disponible")
        
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener los documentos del área',
            'debug': error_message if settings.DEBUG else None
        }, status=500)


@login_required
@require_http_methods(["GET"])
def contar_documentos_expediente(request, expediente_id):
    """
    Vista para obtener el conteo de documentos de un expediente
    """
    from .models import Expediente  # Importar aquí para evitar conflicto de nombres
    
    try:
        expediente = Expediente.objects.get(id=expediente_id)
        return JsonResponse({
            'success': True,
            'count': expediente.documentos.count()
        })
    except Expediente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Expediente no encontrado'
        }, status=404)
    except Exception as e:
        # Registrar el error para depuración
        import traceback
        error_trace = traceback.format_exc()
        print("Error en contar_documentos_expediente:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("Traceback:")
        print(error_trace)
        
        # Devolver información detallada del error en desarrollo
        from django.conf import settings
        if settings.DEBUG:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'trace': error_trace.split('\n')
            }, status=500)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)