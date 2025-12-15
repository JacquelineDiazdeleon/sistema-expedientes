import os
import sys
import django
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import scoring

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.search_utils import get_index_dir, schema

def depurar_busqueda(termino_busqueda):
    """Depura la búsqueda de un término específico"""
    try:
        # Abrir el índice
        ix = open_dir(get_index_dir())
        
        # Crear un searcher con más información de depuración
        with ix.searcher(weighting=scoring.TF_IDF()) as searcher:
            # Crear un parser de consulta para múltiples campos
            query_parser = MultifieldParser(["titulo", "contenido"], schema=schema)
            
            # Parsear la consulta
            query = query_parser.parse(termino_busqueda)
            
            print(f"=== DEPURACIÓN DE BÚSQUEDA ===")
            print(f"Término de búsqueda: {termino_busqueda}")
            print(f"Consulta parseada: {query}")
            
            # Realizar la búsqueda sin filtros
            results = searcher.search(query, limit=20)
            
            print(f"\n=== RESULTADOS ENCONTRADOS ===")
            print(f"Total de resultados: {len(results)}")
            
            # Mostrar información detallada de los primeros 5 resultados
            for i, hit in enumerate(results[:5], 1):
                print(f"\n--- Resultado {i} ---")
                print(f"ID del documento: {hit['doc_id']}")
                print(f"Título: {hit['titulo']}")
                print(f"Tipo de archivo: {hit.get('tipo_archivo', 'No especificado')}")
                print(f"Expediente ID: {hit.get('expediente_id', 'No especificado')}")
                print(f"Puntuación: {hit.score:.4f}")
                
                # Mostrar fragmento con resaltado
                fragmento = hit.highlights('contenido', top=1) or hit.get('contenido', '')[:200] + '...'
                print(f"Fragmento: {fragmento}")
            
            # Si no hay resultados, mostrar términos similares
            if len(results) == 0:
                print("\nNo se encontraron resultados. Términos similares:")
                try:
                    corrector = searcher.corrector("contenido")
                    sugerencias = corrector.suggest(termino_busqueda, limit=3)
                    print(f"¿Quizás quisiste decir?: {', '.join(sugerencias) if sugerencias else 'No hay sugerencias'}")
                except Exception as e:
                    print(f"No se pudieron obtener sugerencias: {str(e)}")
            
    except Exception as e:
        print(f"Error al realizar la búsqueda: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ejecutar con el término de búsqueda "Respuestas"
    depurar_busqueda("Respuestas")
