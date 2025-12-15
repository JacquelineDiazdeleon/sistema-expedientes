#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db import connection

def fix_encoding():
    """
    Corrige la codificación de los textos en la base de datos.
    """
    print("Iniciando corrección de codificación...")
    
    # Ejemplo para un modelo específico, ajusta según tus modelos
    from digitalizacion.models import TuModelo  # Reemplaza con tus modelos
    
    # Obtener todos los registros
    registros = TuModelo.objects.all()
    
    for registro in registros:
        # Aquí iría la lógica para corregir la codificación
        # Por ejemplo, si tienes un campo 'nombre':
        if hasattr(registro, 'nombre'):
            try:
                # Intenta decodificar como latin1 y luego codificar a utf-8
                if isinstance(registro.nombre, str):
                    registro.nombre = registro.nombre.encode('latin1').decode('utf-8')
                    registro.save()
            except Exception as e:
                print(f"Error al procesar registro {registro.id}: {str(e)}")
    
    print("Corrección de codificación completada.")

if __name__ == "__main__":
    fix_encoding()
