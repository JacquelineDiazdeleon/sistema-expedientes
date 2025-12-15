from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import (
    Expediente, DocumentoExpediente, EtapaExpediente, 
    NotaExpediente, Notificacion, ComentarioArea, 
    SolicitudRegistro, Documento, TipoDocumento, Departamento
)

class Command(BaseCommand):
    help = 'Limpia todos los datos de la base de datos excepto la cuenta de administrador principal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar la limpieza de datos',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  ADVERTENCIA: Este comando eliminará TODOS los datos del sistema.\n'
                    'Solo se mantendrá la cuenta de administrador principal.\n\n'
                    'Para confirmar, ejecuta: python manage.py limpiar_base_datos --confirm'
                )
            )
            return

        self.stdout.write('🧹 Iniciando limpieza de la base de datos...')

        # Contar registros antes de eliminar
        expedientes_count = Expediente.objects.count()
        documentos_count = DocumentoExpediente.objects.count()
        notificaciones_count = Notificacion.objects.count()
        solicitudes_count = SolicitudRegistro.objects.count()
        usuarios_count = User.objects.count()

        self.stdout.write(f'📊 Registros encontrados:')
        self.stdout.write(f'   - Expedientes: {expedientes_count}')
        self.stdout.write(f'   - Documentos: {documentos_count}')
        self.stdout.write(f'   - Notificaciones: {notificaciones_count}')
        self.stdout.write(f'   - Solicitudes: {solicitudes_count}')
        self.stdout.write(f'   - Usuarios: {usuarios_count}')

        # Identificar la cuenta de administrador principal
        admin_user = None
        try:
            admin_user = User.objects.get(username='jacqueline.diaz')
            self.stdout.write(f'👤 Manteniendo cuenta de administrador: {admin_user.get_full_name()}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ No se encontró la cuenta de administrador principal'))
            return

        # Eliminar datos en orden para evitar problemas de integridad referencial
        self.stdout.write('🗑️  Eliminando datos...')

        # 1. Eliminar notificaciones
        Notificacion.objects.all().delete()
        self.stdout.write('   ✅ Notificaciones eliminadas')

        # 2. Eliminar comentarios de área
        ComentarioArea.objects.all().delete()
        self.stdout.write('   ✅ Comentarios de área eliminados')

        # 3. Eliminar notas de expedientes
        NotaExpediente.objects.all().delete()
        self.stdout.write('   ✅ Notas de expedientes eliminadas')

        # 4. Eliminar documentos de expedientes
        DocumentoExpediente.objects.all().delete()
        self.stdout.write('   ✅ Documentos de expedientes eliminados')

        # 5. Eliminar etapas de expedientes
        EtapaExpediente.objects.all().delete()
        self.stdout.write('   ✅ Etapas de expedientes eliminadas')

        # 6. Eliminar expedientes
        Expediente.objects.all().delete()
        self.stdout.write('   ✅ Expedientes eliminados')

        # 7. Eliminar documentos
        Documento.objects.all().delete()
        self.stdout.write('   ✅ Documentos eliminados')

        # 8. Eliminar solicitudes de registro
        SolicitudRegistro.objects.all().delete()
        self.stdout.write('   ✅ Solicitudes de registro eliminadas')

        # 9. Eliminar usuarios excepto el administrador principal
        usuarios_a_eliminar = User.objects.exclude(pk=admin_user.pk)
        usuarios_eliminados = usuarios_a_eliminar.count()
        usuarios_a_eliminar.delete()
        self.stdout.write(f'   ✅ {usuarios_eliminados} usuarios eliminados')

        # 10. Limpiar tipos de documento y departamentos (opcional)
        # Comentado para mantener la configuración base
        # TipoDocumento.objects.all().delete()
        # Departamento.objects.all().delete()
        # self.stdout.write('   ✅ Tipos de documento y departamentos eliminados')

        # Verificar resultados
        expedientes_final = Expediente.objects.count()
        documentos_final = DocumentoExpediente.objects.count()
        notificaciones_final = Notificacion.objects.count()
        solicitudes_final = SolicitudRegistro.objects.count()
        usuarios_final = User.objects.count()

        self.stdout.write('\n📊 Resultados finales:')
        self.stdout.write(f'   - Expedientes: {expedientes_final}')
        self.stdout.write(f'   - Documentos: {documentos_final}')
        self.stdout.write(f'   - Notificaciones: {notificaciones_final}')
        self.stdout.write(f'   - Solicitudes: {solicitudes_final}')
        self.stdout.write(f'   - Usuarios: {usuarios_final}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 ¡Limpieza completada exitosamente!\n'
                f'✅ Solo se mantiene la cuenta de administrador: {admin_user.get_full_name()}'
            )
        )
