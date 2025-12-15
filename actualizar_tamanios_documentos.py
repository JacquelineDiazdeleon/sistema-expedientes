import os
import sys
import django
from django.conf import settings

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente

def actualizar_tamanios():
    """
    Actualiza los tamaños de todos los documentos en la base de datos.
    """
    documentos = DocumentoExpediente.objects.all()
    total = documentos.count()
    actualizados = 0
    errores = 0
    
    print(f"Iniciando actualización de tamaños para {total} documentos...")
    
    for i, doc in enumerate(documentos, 1):
        try:
            if doc.archivo:
                # Verificar si el archivo existe físicamente
                if hasattr(doc.archivo.storage, 'exists') and doc.archivo.storage.exists(doc.archivo.name):
                    try:
                        # Obtener el tamaño real del archivo
                        tamaño = doc.archivo.size
                        if tamaño != doc.tamaño_archivo:
                            doc.tamaño_archivo = tamaño
                            doc.save(update_fields=['tamaño_archivo'])
                            actualizados += 1
                            print(f"[{i}/{total}] Actualizado documento {doc.id}: {tamaño} bytes")
                        else:
                            print(f"[{i}/{total}] Documento {doc.id} ya tiene el tamaño correcto")
                    except Exception as e:
                        print(f"[ERROR] Error al procesar documento {doc.id}: {str(e)}")
                        errores += 1
                else:
                    print(f"[ADVERTENCIA] Archivo no encontrado para documento {doc.id}: {doc.archivo.name}")
                    
            else:
                print(f"[INFO] Documento {doc.id} no tiene archivo asociado")
                
        except Exception as e:
            print(f"[ERROR CRÍTICO] Error procesando documento {getattr(doc, 'id', 'N/A')}: {str(e)}")
            errores += 1
    
    print(f"\nResumen:")
    print(f"- Total de documentos procesados: {total}")
    print(f"- Documentos actualizados: {actualizados}")
    print(f"- Errores: {errores}")

if __name__ == "__main__":
    actualizar_tamanios()
