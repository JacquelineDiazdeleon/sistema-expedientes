import os
import django
from django.conf import settings

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente

def actualizar_tamanios():
    # Obtener todos los documentos con archivo
    documentos = DocumentoExpediente.objects.exclude(archivo='')
    print(f"Encontrados {documentos.count()} documentos con archivo")
    
    actualizados = 0
    
    for doc in documentos:
        try:
            # Obtener la ruta completa del archivo
            file_path = os.path.join(settings.MEDIA_ROOT, str(doc.archivo))
            
            # Verificar si el archivo existe
            if os.path.exists(file_path):
                # Obtener el tamaño real del archivo
                size = os.path.getsize(file_path)
                
                # Actualizar si el tamaño es diferente
                if doc.tamaño_archivo != size:
                    print(f"Actualizando documento {doc.id}: {doc.archivo.name} - {size} bytes")
                    doc.tamaño_archivo = size
                    doc.save(update_fields=['tamaño_archivo'])
                    actualizados += 1
            else:
                print(f"Archivo no encontrado: {file_path}")
                
        except Exception as e:
            print(f"Error al procesar documento {doc.id}: {str(e)}")
    
    print(f"\nProceso completado. {actualizados} documentos actualizados.")

if __name__ == "__main__":
    actualizar_tamanios()
