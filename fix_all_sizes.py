import os
import django
import sys
from pathlib import Path

# Configurar el entorno de Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.conf import settings
from digitalizacion.models import DocumentoExpediente

def fix_sizes():
    """Actualiza los tamaños de todos los documentos en la base de datos."""
    # Configurar MEDIA_ROOT si no está definido
    MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
    
    documentos = DocumentoExpediente.objects.all()
    total = documentos.count()
    actualizados = 0
    errores = 0
    
    print(f"Iniciando actualización de tamaños para {total} documentos...")
    
    for i, doc in enumerate(documentos, 1):
        try:
            if not doc.archivo:
                print(f"[{i}/{total}] Documento {doc.id}: Sin archivo")
                continue
                
            # Obtener la ruta completa del archivo
            file_path = os.path.join(MEDIA_ROOT, str(doc.archivo))
            
            if not os.path.exists(file_path):
                print(f"[{i}/{total}] Archivo no encontrado: {file_path}")
                continue
                
            # Obtener el tamaño del archivo
            try:
                size = os.path.getsize(file_path)
                if size > 0:
                    # Actualizar solo el campo tamaño_archivo
                    DocumentoExpediente.objects.filter(pk=doc.pk).update(tamaño_archivo=size)
                    actualizados += 1
                    print(f"[{i}/{total}] Actualizado documento {doc.id}: {size} bytes")
                else:
                    print(f"[{i}/{total}] Documento {doc.id} tiene tamaño 0: {file_path}")
            except Exception as e:
                print(f"[ERROR] Error al obtener tamaño de {file_path}: {str(e)}")
                errores += 1
                
        except Exception as e:
            print(f"[ERROR CRÍTICO] Error procesando documento {getattr(doc, 'id', 'N/A')}: {str(e)}")
            errores += 1
    
    print(f"\nResumen:")
    print(f"- Total de documentos procesados: {total}")
    print(f"- Documentos actualizados: {actualizados}")
    print(f"- Errores: {errores}")

if __name__ == "__main__":
    fix_sizes()
