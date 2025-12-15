from django.core.management.base import BaseCommand
from django.db import transaction
from digitalizacion.models import DocumentoExpediente
from digitalizacion.search_utils import index_document, get_or_create_index
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Indexa todos los documentos existentes en el sistema de búsqueda'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reindexar',
            action='store_true',
            help='Reindexar todos los documentos (incluso los ya indexados)',
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Limitar el número de documentos a indexar',
        )

    def handle(self, *args, **options):
        reindexar = options.get('reindexar', False)
        limite = options.get('limite')
        
        self.stdout.write('Inicializando índice de búsqueda...')
        
        # Crear o verificar el índice
        try:
            ix = get_or_create_index()
            self.stdout.write(self.style.SUCCESS('✓ Índice de búsqueda listo'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error al crear el índice: {str(e)}'))
            return
        
        # Obtener documentos a indexar
        if reindexar:
            documentos = DocumentoExpediente.objects.all()
            self.stdout.write('Reindexando todos los documentos...')
        else:
            # Solo indexar documentos que tengan archivo
            documentos = DocumentoExpediente.objects.filter(archivo__isnull=False).exclude(archivo='')
            self.stdout.write('Indexando documentos no indexados...')
        
        if limite:
            documentos = documentos[:limite]
        
        total = documentos.count()
        self.stdout.write(f'Total de documentos a procesar: {total}')
        
        if total == 0:
            self.stdout.write(self.style.WARNING('No hay documentos para indexar'))
            return
        
        exitosos = 0
        fallidos = 0
        sin_archivo = 0
        
        self.stdout.write('\nIniciando indexación...\n')
        
        for i, documento in enumerate(documentos, 1):
            try:
                # Verificar que el documento tenga archivo
                if not documento.archivo:
                    sin_archivo += 1
                    self.stdout.write(f'[{i}/{total}] ⚠ Documento {documento.id}: Sin archivo')
                    continue
                
                # Intentar indexar
                if index_document(documento):
                    exitosos += 1
                    self.stdout.write(f'[{i}/{total}] ✓ Documento {documento.id}: "{documento.nombre_documento[:50]}"')
                else:
                    fallidos += 1
                    self.stdout.write(f'[{i}/{total}] ✗ Documento {documento.id}: Error al indexar')
                    
            except Exception as e:
                fallidos += 1
                self.stdout.write(f'[{i}/{total}] ✗ Documento {documento.id}: {str(e)}')
                logger.error(f"Error indexando documento {documento.id}: {str(e)}", exc_info=True)
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE INDEXACIÓN'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total procesados: {total}')
        self.stdout.write(self.style.SUCCESS(f'✓ Exitosos: {exitosos}'))
        self.stdout.write(self.style.ERROR(f'✗ Fallidos: {fallidos}'))
        if sin_archivo > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Sin archivo: {sin_archivo}'))
        self.stdout.write('='*60)


