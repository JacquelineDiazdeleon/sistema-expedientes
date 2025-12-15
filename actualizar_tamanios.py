import os
from django.conf import settings
from digitalizacion.models import DocumentoExpediente

def actualizar_tamanios():
    documentos = DocumentoExpediente.objects.all()
    actualizados = 0
    
    for doc in documentos:
        try:
            if doc.archivo:
                # Verificar si el archivo existe físicamente
                file_path = os.path.join(settings.MEDIA_ROOT, str(doc.archivo))
                if os.path.exists(file_path):
                    # Obtener el tamaño real del archivo
                    size = os.path.getsize(file_path)
                    if doc.tamaño_archivo != size:
                        doc.tamaño_archivo = size
                        doc.save()
                        actualizados += 1
                        print(f"Actualizado: {doc.id} - {doc.archivo.name} - {size} bytes")
                else:
                    print(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print(f"Error al procesar documento {doc.id}: {str(e)}")
    
    print(f"\nProceso completado. {actualizados} documentos actualizados.")

if __name__ == "__main__":
    import os
    import django
    import sys
    
    # Asegurarse de que el directorio raíz esté en el path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    django.setup()
    
    # Ahora que Django está configurado, importamos los modelos
    from digitalizacion.models import DocumentoExpediente
    from django.conf import settings
    
    actualizar_tamanios()
