import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente
from digitalizacion.search_utils import index_document, remove_document

def reindexar_documentos():
    """Reindexa todos los documentos en la base de datos con soporte OCR"""
    documentos = DocumentoExpediente.objects.all()
    total = documentos.count()
    exitosos = 0
    fallidos = 0
    
    print(f"Iniciando reindexación de {total} documentos con soporte OCR...\n")
    
    for i, doc in enumerate(documentos, 1):
        try:
            # Primero eliminamos el documento del índice si ya existe
            remove_document(doc.id)
            
            # Luego lo volvemos a indexar
            if index_document(doc):
                exitosos += 1
                print(f"[{i}/{total}] Documento {doc.id} indexado correctamente")
            else:
                fallidos += 1
                print(f"[{i}/{total}] Error al indexar documento {doc.id}")
                
        except Exception as e:
            fallidos += 1
            print(f"[{i}/{total}] Error procesando documento {doc.id}: {str(e)}")
    
    print("\nResumen de la reindexación:")
    print(f"- Documentos procesados: {total}")
    print(f"- Documentos indexados exitosamente: {exitosos}")
    print(f"- Documentos con errores: {fallidos}")

if __name__ == "__main__":
    reindexar_documentos()
