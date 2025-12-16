import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente
from digitalizacion.search_utils import extract_text, index_document, get_or_create_index
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnosticar_documento(documento_id=None):
    """
    Diagnostica un documento específico para ver por qué no se encuentra en la búsqueda
    """
    if documento_id:
        try:
            documento = DocumentoExpediente.objects.get(id=documento_id)
        except DocumentoExpediente.DoesNotExist:
            print(f"❌ Documento {documento_id} no encontrado")
            return
    else:
        # Obtener el último documento subido
        documento = DocumentoExpediente.objects.filter(archivo__isnull=False).exclude(archivo='').order_by('-fecha_subida').first()
        if not documento:
            print("❌ No se encontraron documentos en la base de datos")
            return
    
    print("=" * 70)
    print(f"DIAGNÓSTICO DEL DOCUMENTO ID: {documento.id}")
    print("=" * 70)
    print(f"Nombre: {documento.nombre_documento}")
    print(f"Expediente ID: {documento.expediente_id}")
    print(f"Fecha subida: {documento.fecha_subida}")
    print(f"Tipo archivo: {documento.tipo_archivo}")
    print()
    
    # Verificar archivo
    print("1. VERIFICANDO ARCHIVO...")
    if not documento.archivo:
        print("   ❌ El documento no tiene archivo asociado")
        return
    
    file_path = None
    if hasattr(documento.archivo, 'path'):
        file_path = documento.archivo.path
    else:
        from django.conf import settings
        file_path = os.path.join(settings.MEDIA_ROOT, documento.archivo.name)
    
    print(f"   Ruta del archivo: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"   ❌ El archivo no existe en: {file_path}")
        return
    else:
        print(f"   ✓ Archivo existe")
        file_size = os.path.getsize(file_path)
        print(f"   Tamaño: {file_size} bytes ({file_size / 1024:.2f} KB)")
    
    # Extraer texto
    print()
    print("2. EXTRAYENDO TEXTO...")
    texto_extraido = extract_text(file_path)
    print(f"   Longitud del texto extraído: {len(texto_extraido)} caracteres")
    
    if texto_extraido:
        print(f"   ✓ Texto extraído exitosamente")
        print(f"   Primeros 300 caracteres:")
        print(f"   {'-' * 70}")
        print(f"   {texto_extraido[:300]}")
        print(f"   {'-' * 70}")
    else:
        print(f"   ⚠️ No se pudo extraer texto del archivo")
        print(f"   Esto puede ser normal si es una imagen escaneada sin OCR")
    
    # Verificar índice
    print()
    print("3. VERIFICANDO ÍNDICE...")
    try:
        ix = get_or_create_index()
        with ix.searcher() as searcher:
            doc_id = f"doc_{documento.id}"
            stored_doc = searcher.document(doc_id=doc_id)
            
            if stored_doc:
                print(f"   ✓ Documento encontrado en el índice")
                print(f"   doc_id: {stored_doc.get('doc_id')}")
                print(f"   expediente_id: {stored_doc.get('expediente_id')}")
                print(f"   título: {stored_doc.get('titulo', '')[:50]}")
                contenido_almacenado = stored_doc.get('contenido', '')
                print(f"   contenido almacenado: {len(contenido_almacenado)} caracteres")
                
                if contenido_almacenado:
                    print(f"   Primeros 300 caracteres del contenido indexado:")
                    print(f"   {'-' * 70}")
                    print(f"   {contenido_almacenado[:300]}")
                    print(f"   {'-' * 70}")
                else:
                    print(f"   ⚠️ El contenido indexado está vacío")
                
                # Probar búsqueda
                print()
                print("4. PROBANDO BÚSQUEDA...")
                if texto_extraido:
                    # Buscar una palabra del texto extraído
                    palabras = texto_extraido.split()[:5]  # Primeras 5 palabras
                    for palabra in palabras:
                        if len(palabra) > 3:  # Solo palabras de más de 3 caracteres
                            print(f"   Buscando: '{palabra}'")
                            from whoosh.qparser import QueryParser
                            parser = QueryParser("contenido", ix.schema)
                            query = parser.parse(palabra.lower())
                            results = searcher.search(query, limit=5)
                            encontrado = any(hit.get('doc_id') == doc_id for hit in results)
                            if encontrado:
                                print(f"      ✓ Encontrado en búsqueda")
                            else:
                                print(f"      ❌ NO encontrado en búsqueda")
                            break
            else:
                print(f"   ❌ Documento NO encontrado en el índice")
                print(f"   Intentando indexar ahora...")
                if index_document(documento):
                    print(f"   ✓ Documento indexado exitosamente")
                else:
                    print(f"   ❌ Error al indexar el documento")
                    
    except Exception as e:
        print(f"   ❌ Error al verificar índice: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 70)

if __name__ == "__main__":
    documento_id = None
    if len(sys.argv) > 1:
        try:
            documento_id = int(sys.argv[1])
        except ValueError:
            print("Uso: python diagnosticar_documento.py [documento_id]")
            sys.exit(1)
    
    diagnosticar_documento(documento_id)

