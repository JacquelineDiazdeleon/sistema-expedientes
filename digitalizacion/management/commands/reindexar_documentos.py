from django.core.management.base import BaseCommand
from django.db import transaction
from digitalizacion.models import DocumentoExpediente
from digitalizacion.search_utils import index_document
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reindexa todos los documentos en el motor de búsqueda'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Número de documentos a procesar por lote (default: 100)'
        )
        parser.add_argument(
            '--documento-inicial',
            type=int,
            default=0,
            help='ID del documento inicial para comenzar la reindexación'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        documento_inicial = options['documento_inicial']
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando reindexación de documentos...'))
        
        # Obtener el total de documentos a procesar
        total_documentos = DocumentoExpediente.objects.count()
        self.stdout.write(f'Total de documentos a procesar: {total_documentos}')
        
        # Procesar documentos en lotes
        offset = 0
        documentos_procesados = 0
        documentos_indexados = 0
        
        while True:
            with transaction.atomic():
                # Obtener un lote de documentos
                documentos = DocumentoExpediente.objects.filter(
                    id__gte=documento_inicial
                ).order_by('id')[offset:offset + batch_size]
                
                if not documentos:
                    break
                
                # Procesar cada documento en el lote
                for documento in documentos:
                    try:
                        if index_document(documento):
                            documentos_indexados += 1
                        documentos_procesados += 1
                        
                        # Mostrar progreso cada 10 documentos
                        if documentos_procesados % 10 == 0:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Procesados {documentos_procesados}/{total_documentos} documentos. '
                                    f'Índice actualizado para {documentos_indexados} documentos.'
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error al indexar documento ID {documento.id}: {str(e)}'
                            )
                        )
                        logger.error(f'Error al indexar documento ID {documento.id}: {str(e)}', exc_info=True)
                
                offset += batch_size
        
        self.stdout.write(self.style.SUCCESS(
            f'Reindexación completada. Procesados {documentos_procesados} documentos. '
            f'Índice actualizado para {documentos_indexados} documentos.'
        ))
