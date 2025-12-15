#!/usr/bin/env python
"""
Script para actualizar los tamaños de los archivos en la base de datos.
Este script actualiza el campo 'tamaño_archivo' para todos los documentos
existentes en la base de datos basándose en el tamaño real del archivo en disco.
"""

import os
import sys
import django
from django.conf import settings

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from digitalizacion.models import DocumentoExpediente
from django.db import transaction

def actualizar_tamanios_documentos():
    """Actualiza el tamaño de todos los documentos en la base de datos."""
    # Obtener todos los documentos que tienen un archivo
    documentos = DocumentoExpediente.objects.exclude(archivo='')
    total = documentos.count()
    actualizados = 0
    errores = 0
    
    print(f"Iniciando actualización de tamaños para {total} documentos...")
    
    with transaction.atomic():
        for i, doc in enumerate(documentos, 1):
            try:
                # Forzar la actualización del tamaño del archivo
                doc.save(force_update_size=True)
                
                # Verificar si el tamaño se actualizó correctamente
                doc.refresh_from_db()
                if hasattr(doc, 'tamaño_archivo') and doc.tamaño_archivo and doc.tamaño_archivo > 0:
                    actualizados += 1
                    if i % 10 == 0 or i == total:
                        print(f"Procesados {i}/{total} documentos. Actualizados: {actualizados}, Errores: {errores}")
                else:
                    errores += 1
                    print(f"Error: No se pudo actualizar el tamaño para el documento ID {doc.id}")
            except Exception as e:
                errores += 1
                print(f"Error al procesar documento ID {doc.id}: {str(e)}")
    
    print("\nResumen de la actualización:")
    print(f"- Documentos procesados: {total}")
    print(f"- Documentos actualizados: {actualizados}")
    print(f"- Errores: {errores}")
    print(f"- Documentos sin cambios: {total - actualizados - errores}")

if __name__ == "__main__":
    actualizar_tamanios_documentos()
