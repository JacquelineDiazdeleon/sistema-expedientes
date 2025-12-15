# clean_database.py
import os
import django
from django.db import connection

def limpiar_datos_problematicos():
    print("Iniciando limpieza de datos problemáticos...")
    
    # Usar una conexión directa para evitar problemas con el ORM
    with connection.cursor() as cursor:
        # 1. Deshabilitar temporalmente las restricciones de clave foránea (solo para SQLite)
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        try:
            # 2. Eliminar registros problemáticos
            # a) HistorialExpediente sin expediente
            cursor.execute("DELETE FROM digitalizacion_historialexpediente WHERE expediente_id IS NULL")
            print(f"Eliminados {cursor.rowcount} registros de HistorialExpediente sin expediente")
            
            # b) Documentos sin expediente
            cursor.execute("DELETE FROM digitalizacion_documentoexpediente WHERE expediente_id IS NULL")
            print(f"Eliminados {cursor.rowcount} documentos sin expediente")
            
            # c) Limpiar sesiones de usuario (opcional, descomenta si es necesario)
            # cursor.execute("DELETE FROM digitalizacion_usersession")
            # print(f"Eliminadas todas las sesiones de usuario")
            
            # 3. Si hay otras tablas problemáticas, agrégalas aquí
            
            # Confirmar los cambios
            connection.commit()
            print("Limpieza completada exitosamente.")
            
        except Exception as e:
            # En caso de error, hacer rollback
            connection.rollback()
            print(f"Error durante la limpieza: {str(e)}")
            raise
            
        finally:
            # 4. Reactivar las restricciones
            cursor.execute("PRAGMA foreign_keys = ON")

if __name__ == "__main__":
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
    django.setup()
    
    # Mostrar advertencia
    print("¡ADVERTENCIA! Este script eliminará datos de la base de datos.")
    print("Asegúrate de tener una copia de seguridad antes de continuar.")
    
    confirmacion = input("¿Estás seguro de que deseas continuar? (s/n): ")
    if confirmacion.lower() == 's':
        try:
            limpiar_datos_problematicos()
        except Exception as e:
            print(f"Ocurrió un error: {str(e)}")
    else:
        print("Operación cancelada.")
    
    input("Presiona Enter para salir...")
