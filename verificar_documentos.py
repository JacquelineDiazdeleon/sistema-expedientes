import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente

def verificar_documentos():
    # Contar documentos totales
    total = DocumentoExpediente.objects.count()
    print(f"Documentos totales en la base de datos: {total}")
    
    # Contar documentos con tamaño 0 o nulo
    con_tamanio_cero = DocumentoExpediente.objects.filter(tamaño_archivo__isnull=True) | DocumentoExpediente.objects.filter(tamaño_archivo=0)
    print(f"Documentos con tamaño 0 o nulo: {con_tamanio_cero.count()}")
    
    # Mostrar algunos ejemplos
    print("\nPrimeros 5 documentos con tamaño 0 o nulo:")
    for doc in con_tamanio_cero[:5]:
        print(f"ID: {doc.id}, Nombre: {doc.nombre_documento}, Tamaño: {doc.tamaño_archivo}, Archivo: {doc.archivo}")
    
    # Verificar si los archivos existen físicamente
    print("\nVerificando archivos físicos...")
    documentos_con_archivo = DocumentoExpediente.objects.exclude(archivo='')
    print(f"Documentos con ruta de archivo: {documentos_con_archivo.count()}")
    
    # Verificar archivos que no existen
    print("\nVerificando archivos que no existen en el sistema de archivos:")
    for doc in documentos_con_archivo[:10]:  # Revisar solo los primeros 10 para no saturar
        file_path = os.path.join('media', str(doc.archivo))
        if not os.path.exists(file_path):
            print(f"No encontrado: {file_path}")
        else:
            print(f"Encontrado: {file_path} - Tamaño: {os.path.getsize(file_path)} bytes")

if __name__ == "__main__":
    verificar_documentos()
