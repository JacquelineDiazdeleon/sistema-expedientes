import os
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from .models import DocumentoExpediente, Expediente
from .search_utils import search_documents, index_document, remove_document

logger = logging.getLogger(__name__)

@login_required
def buscar_documentos(request):
    """
    Vista para la página de búsqueda de documentos
    """
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    expediente_id = request.GET.get('expediente_id')
    page = request.GET.get('page', 1)
    
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
    
    # Obtener los expedientes para el filtro
    expedientes = Expediente.objects.all().order_by('-fecha_creacion')[:50]
    
    return render(request, 'digitalizacion/buscar.html', {
        'query': query,
        'tipo': tipo,
        'expediente_actual': expediente,
        'expedientes': expedientes,
        'tipos_documento': ['todos', 'pdf', 'docx', 'doc', 'xls', 'xlsx', 'jpg', 'png'],
    })

@login_required
def api_buscar_documentos(request):
    """
    API para realizar búsquedas de documentos
    """
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    expediente_id = request.GET.get('expediente_id')
    page = int(request.GET.get('page', 1))
    
    # Construir filtros
    filters = {}
    if tipo != 'todos':
        filters['tipo_archivo'] = tipo
    
    # Realizar la búsqueda
    results = search_documents(
        query=query,
        expediente_id=expediente_id,
        page=page,
        limit=20
    )
    
    # Si hay un error en la búsqueda
    if 'error' in results:
        return JsonResponse({
            'success': False,
            'error': results['error']
        }, status=500)
    
    # Obtener los IDs de los documentos para obtener más información de la base de datos
    doc_ids = [int(r['id']) for r in results['results']]
    documentos = DocumentoExpediente.objects.filter(id__in=doc_ids).in_bulk()
    
    # Formatear resultados con información adicional
    formatted_results = []
    for result in results['results']:
        doc_id = int(result['id'])
        if doc_id in documentos:
            doc = documentos[doc_id]
            formatted_results.append({
                'id': doc.id,
                'titulo': doc.nombre_documento,
                'fragmento': result.get('fragmento', ''),
                'fecha': result.get('fecha_creacion', doc.fecha_subida.strftime('%d/%m/%Y %H:%M')),
                'tipo_archivo': doc.tipo_archivo or 'desconocido',
                'expediente': {
                    'id': doc.expediente_id,
                    'numero': doc.expediente.numero_expediente,
                    'asunto': doc.expediente.asunto,
                    'url': doc.expediente.get_absolute_url() if hasattr(doc.expediente, 'get_absolute_url') else f'/expedientes/{doc.expediente_id}/'
                },
                'url_descarga': f'/documentos/{doc.id}/descargar/',
                'url_ver': f'/documentos/{doc.id}/',
                'score': result.get('score', 0)
            })
    
    return JsonResponse({
        'success': True,
        'results': formatted_results,
        'total': results.get('total', 0),
        'page': results.get('page', 1),
        'has_next': results.get('has_next', False),
        'has_previous': results.get('has_previous', False),
        'page_count': results.get('page_count', 1)
    })

@login_required
def indexar_documentos(request):
    """
    Vista para indexar manualmente los documentos existentes
    Solo accesible para superusuarios
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
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

def document_post_save(sender, instance, created, **kwargs):
    ""
    Señal para indexar documentos cuando se crean o actualizan
    ""
    if created or instance.archivo:
        index_document(instance)

def document_pre_delete(sender, instance, **kwargs):
    ""
    Señal para eliminar documentos del índice cuando se borran
    ""
    remove_document(instance.id)
