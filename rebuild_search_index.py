import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.search_utils import index_document
from digitalizacion.models import DocumentoExpediente

def rebuild_search_index():
    print("Iniciando la reconstrucción del índice de búsqueda...")
    
    # Obtener todos los documentos
    documentos = DocumentoExpediente.objects.all()
    total = documentos.count()
    
    print(f"Se van a indexar {total} documentos...")
    
    # Indexar cada documento
    for i, doc in enumerate(documentos, 1):
        try:
            print(f"Indexando documento {i}/{total}: ID={doc.id}, Archivo={doc.archivo.name if doc.archivo else 'Ninguno'}")
            success = index_document(doc)
            if not success:
                print(f"  ¡Advertencia: No se pudo indexar el documento {doc.id}!")
        except Exception as e:
            print(f"  Error al indexar documento {doc.id}: {str(e)}")
    
    print("¡Reconstrucción del índice completada!")

if __name__ == "__main__":
    rebuild_search_index()
