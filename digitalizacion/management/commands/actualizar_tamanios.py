import os
from django.core.management.base import BaseCommand
from django.conf import settings
from digitalizacion.models import DocumentoExpediente

class Command(BaseCommand):
    help = 'Actualiza los tamaños de los archivos en la base de datos'

    def handle(self, *args, **options):
        documentos = DocumentoExpediente.objects.all()
        actualizados = 0
        
        for doc in documentos:
            try:
                if doc.archivo:
                    # Obtener la ruta completa del archivo
                    file_path = os.path.join(settings.MEDIA_ROOT, str(doc.archivo))
                    
                    # Verificar si el archivo existe
                    if os.path.exists(file_path):
                        # Obtener el tamaño real del archivo
                        size = os.path.getsize(file_path)
                        
                        # Actualizar si el tamaño es diferente
                        if doc.tamaño_archivo != size:
                            doc.tamaño_archivo = size
                            doc.save(update_fields=['tamaño_archivo'])
                            actualizados += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'Actualizado: ID {doc.id} - {doc.archivo.name} - {size} bytes'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Archivo no encontrado: {file_path}'
                        ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error al procesar documento {doc.id}: {str(e)}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nProceso completado. {actualizados} documentos actualizados.'
        ))
