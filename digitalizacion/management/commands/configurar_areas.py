from django.core.management.base import BaseCommand
import os
import sys

class Command(BaseCommand):
    help = 'Configura las áreas por defecto para todos los tipos de expediente'

    def handle(self, *args, **options):
        # Obtener la ruta del script configurar_areas.py
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        script_path = os.path.join(project_root, 'configurar_areas.py')
        
        if not os.path.exists(script_path):
            self.stdout.write(self.style.ERROR(f'No se encontró el script: {script_path}'))
            return
        
        self.stdout.write('Configurando áreas por defecto...')
        
        # Ejecutar el script directamente usando exec
        # Leer el script y ejecutarlo en el contexto actual
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Reemplazar la parte interactiva para que se ejecute automáticamente
        # Buscar la función crear_areas_por_defecto y ejecutarla
        import django
        from django.contrib.auth.models import User
        from django.db import transaction
        from digitalizacion.models import AreaTipoExpediente
        
        # Ejecutar la función directamente
        # Importar el módulo del script
        sys.path.insert(0, project_root)
        import importlib.util
        spec = importlib.util.spec_from_file_location("configurar_areas", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Llamar a la función sin confirmación
        try:
            module.crear_areas_por_defecto()
            self.stdout.write(self.style.SUCCESS('\n¡Proceso de creación de áreas completado con éxito!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al configurar áreas: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

