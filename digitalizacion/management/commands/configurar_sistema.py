from django.core.management.base import BaseCommand
from digitalizacion.models import ConfiguracionSistema


class Command(BaseCommand):
    help = 'Configura las configuraciones iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando sistema...')
        
        # Configuraciones del sistema
        configuraciones = [
            {
                'clave': 'nombre_sistema',
                'valor': 'Sistema de Digitalización - Secretaría de Servicios Públicos',
                'descripcion': 'Nombre oficial del sistema'
            },
            {
                'clave': 'version_sistema',
                'valor': '2.0.0',
                'descripcion': 'Versión actual del sistema'
            },
            {
                'clave': 'desarrollador',
                'valor': 'Jacqueline Díaz de León',
                'descripcion': 'Desarrolladora principal del sistema'
            },
            {
                'clave': 'email_soporte',
                'valor': 'soporte@serviciospublicos.gob.mx',
                'descripcion': 'Email de soporte técnico'
            },
            {
                'clave': 'max_file_size',
                'valor': '10485760',
                'descripcion': 'Tamaño máximo de archivo en bytes (10MB)'
            },
            {
                'clave': 'allowed_extensions',
                'valor': 'pdf,doc,docx,jpg,jpeg,png,xlsx,xls',
                'descripcion': 'Extensiones de archivo permitidas'
            },
            {
                'clave': 'auto_archive_days',
                'valor': '365',
                'descripcion': 'Días para archivado automático de expedientes'
            },
            {
                'clave': 'notification_email',
                'valor': 'notificaciones@serviciospublicos.gob.mx',
                'descripcion': 'Email para notificaciones del sistema'
            },
            {
                'clave': 'sistema_activo',
                'valor': 'true',
                'descripcion': 'Estado del sistema (true/false)'
            },
            {
                'clave': 'mantenimiento_mode',
                'valor': 'false',
                'descripcion': 'Modo mantenimiento (true/false)'
            }
        ]
        
        for config_data in configuraciones:
            config, created = ConfiguracionSistema.objects.get_or_create(
                clave=config_data['clave'],
                defaults={
                    'valor': config_data['valor'],
                    'descripcion': config_data['descripcion'],
                    'activo': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Configuración: {config_data["clave"]}')
            else:
                self.stdout.write(f'  - Configuración: {config_data["clave"]} ya existe')
        
        self.stdout.write(
            self.style.SUCCESS('¡Configuración del sistema completada exitosamente!')
        )
