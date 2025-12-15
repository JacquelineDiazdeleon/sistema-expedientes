import os
import sys
import django
import PyPDF2
from pathlib import Path

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente

def verificar_extraccion_pdf():
    """Verifica la extracción de texto de los PDFs en la base de datos"""
    # Obtener todos los documentos PDF
    documentos = DocumentoExpediente.objects.filter(tipo_archivo__iexact='pdf')[:5]  # Revisar solo los primeros 5 para no sobrecargar
    
    print(f"=== VERIFICACIÓN DE EXTRACCIÓN DE TEXTO DE PDFs ===\n")
    
    if not documentos.exists():
        print("No se encontraron documentos PDF en la base de datos.")
        return
    
    for i, doc in enumerate(documentos, 1):
        try:
            file_path = doc.archivo.path
            print(f"\n--- Documento {i} ---")
            print(f"ID: {doc.id}")
            print(f"Nombre: {doc.nombre_documento}")
            print(f"Ruta: {file_path}")
            
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                print("  ❌ Error: El archivo no existe en la ruta especificada.")
                continue
                
            # Intentar extraer texto
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    num_paginas = len(reader.pages)
                    print(f"  Páginas: {num_paginas}")
                    
                    # Extraer texto de la primera página
                    if num_paginas > 0:
                        primera_pagina = reader.pages[0]
                        texto = primera_pagina.extract_text() or ""
                        
                        print(f"  Texto extraído (primeros 200 caracteres):")
                        print(f"  {'-'*50}")
                        print(f"  {texto[:200]}..." if texto else "  No se pudo extraer texto")
                        print(f"  {'-'*50}")
                        
                        # Verificar si el texto parece ser un PDF escaneado (imagen)
                        if len(texto.strip()) < 50:  # Si hay menos de 50 caracteres, podría ser un PDF escaneado
                            print("  ⚠️ Advertencia: El texto extraído es muy corto. El PDF podría ser una imagen escaneada.")
                    else:
                        print("  ❌ Error: El PDF no contiene páginas.")
                        
            except Exception as e:
                print(f"  ❌ Error al procesar el PDF: {str(e)}")
                
        except Exception as e:
            print(f"  ❌ Error general con el documento {doc.id}: {str(e)}")

if __name__ == "__main__":
    verificar_extraccion_pdf()
