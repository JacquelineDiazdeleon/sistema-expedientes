import os
import django
from django.conf import settings
from django.db import connection

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

def actualizar_tamanios_directo():
    with connection.cursor() as cursor:
        # Obtener todos los documentos con archivo
        cursor.execute("""
            SELECT id, archivo, tamaño_archivo 
            FROM digitalizacion_documentoexpediente 
            WHERE archivo != ''
        """)
        
        documentos = cursor.fetchall()
        print(f"Encontrados {len(documentos)} documentos con archivo")
        
        actualizados = 0
        
        for doc_id, archivo_path, tamano_actual in documentos:
            try:
                # Obtener la ruta completa del archivo
                file_path = os.path.join(settings.MEDIA_ROOT, str(archivo_path))
                
                # Verificar si el archivo existe
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    
                    # Actualizar solo si el tamaño es diferente
                    if tamano_actual != size:
                        # Actualizar el tamaño en la base de datos
                        cursor.execute("""
                            UPDATE digitalizacion_documentoexpediente 
                            SET tamaño_archivo = %s 
                            WHERE id = %s
                        """, (size, doc_id))
                        
                        actualizados += 1
                        print(f"Actualizado documento {doc_id}: {archivo_path} - {size} bytes")
                    else:
                        print(f"Documento {doc_id} ya tiene el tamaño correcto: {size} bytes")
                else:
                    print(f" Archivo no encontrado: {file_path}")
                    
            except Exception as e:
                print(f"Error al procesar documento {doc_id}: {str(e)}")
    
    print(f"\nProceso completado. {actualizados} documentos actualizados.")

if __name__ == "__main__":
    actualizar_tamanios_directo()
