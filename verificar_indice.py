import os
import sys
import django
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

def verificar_indice():
    # Ruta al directorio del índice
    index_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoosh_index')
    
    try:
        # Abrir el índice
        ix = open_dir(index_dir)
        
        # Mostrar información del índice
        print("=== Información del Índice ===")
        print(f"Número de documentos en el índice: {ix.doc_count()}")
        
        # Buscar la palabra "Respuestas"
        print("\n=== Buscando la palabra 'Respuestas' ===")
        with ix.searcher() as searcher:
            query = QueryParser("contenido", ix.schema).parse("Respuestas")
            results = searcher.search(query, limit=10)
            
            if len(results) > 0:
                print(f"Se encontraron {len(results)} documentos que contienen 'Respuestas':")
                for hit in results:
                    print(f"\nDocumento ID: {hit['doc_id']}")
                    print(f"Título: {hit['titulo']}")
                    print(f"Tipo: {hit.get('tipo_archivo', 'No especificado')}")
                    print(f"Expediente ID: {hit.get('expediente_id', 'No especificado')}")
                    print("Fragmento:", hit.highlights('contenido', top=1) or "Sin fragmento disponible")
            else:
                print("No se encontraron documentos que contengan 'Respuestas'")
                
    except Exception as e:
        print(f"Error al verificar el índice: {str(e)}")

if __name__ == "__main__":
    verificar_indice()
