from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from digitalizacion.models import TipoDocumento, Departamento, Documento, HistorialDocumento
import random


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de digitalización'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba...'))

        # Crear tipos de documento
        tipos_documento = [
            ('Expediente Técnico', 'Documentación técnica del proyecto'),
            ('Oficio', 'Comunicaciones oficiales'),
            ('Cotización', 'Propuestas económicas de proveedores'),
            ('Contrato', 'Contratos y convenios'),
            ('Factura', 'Documentos fiscales'),
            ('Comprobante de Pago', 'Evidencias de pagos realizados'),
            ('Garantía', 'Documentos de garantías'),
            ('Acta', 'Actas de reuniones y eventos'),
        ]

        for nombre, desc in tipos_documento:
            obj, created = TipoDocumento.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            if created:
                self.stdout.write(f'  ✓ Tipo de documento: {nombre}')

        # Crear departamentos
        departamentos = [
            ('Compras', 'Departamento de adquisiciones y compras'),
            ('Contabilidad', 'Área contable y financiera'),
            ('Sistemas', 'Tecnologías de la información'),
            ('Recursos Humanos', 'Gestión del personal'),
            ('Obras Públicas', 'Infraestructura y construcción'),
            ('Servicios Generales', 'Servicios generales del municipio'),
            ('Secretaría', 'Secretaría municipal'),
            ('Tesorería', 'Administración de recursos financieros'),
        ]

        for nombre, desc in departamentos:
            obj, created = Departamento.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc}
            )
            if created:
                self.stdout.write(f'  ✓ Departamento: {nombre}')

        # Crear usuarios adicionales (opcional)
        usuarios_demo = [
            ('jperez', 'Juan', 'Pérez', 'juan.perez@municipio.com'),
            ('mlopez', 'María', 'López', 'maria.lopez@municipio.com'),
            ('cgarcia', 'Carlos', 'García', 'carlos.garcia@municipio.com'),
        ]

        for username, first_name, last_name, email in usuarios_demo:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(f'  ✓ Usuario: {username} (password: demo123)')

        # Crear documentos de ejemplo
        tipos = list(TipoDocumento.objects.all())
        deptos = list(Departamento.objects.all())
        usuarios = list(User.objects.all())

        documentos_ejemplo = [
            {
                'titulo': 'Expediente de Adquisición de Equipos de Cómputo',
                'descripcion': 'Compra de 15 computadoras para el área de sistemas',
                'giro': 'Tecnología',
                'fuente_financiamiento': 'propio_municipal',
                'tipo_adquisicion': 'bienes',
                'modalidad_monto': 'concurso_invitacion',
                'estado': 'digitalizado',
                'prioridad': 'alta',
            },
            {
                'titulo': 'Contratación de Servicio de Limpieza',
                'descripcion': 'Servicio de limpieza para todas las instalaciones municipales',
                'giro': 'Servicios',
                'fuente_financiamiento': 'propio_municipal',
                'tipo_adquisicion': 'servicios',
                'modalidad_monto': 'licitacion',
                'estado': 'en_proceso',
                'prioridad': 'media',
            },
            {
                'titulo': 'Compra de Material de Oficina',
                'descripcion': 'Adquisición de papelería y material de oficina',
                'giro': 'Papelería',
                'fuente_financiamiento': 'propio_municipal',
                'tipo_adquisicion': 'bienes',
                'modalidad_monto': 'compra_directa',
                'estado': 'verificado',
                'prioridad': 'baja',
            },
            {
                'titulo': 'Arrendamiento de Vehículos',
                'descripcion': 'Renta de 3 vehículos para el área operativa',
                'giro': 'Transporte',
                'fuente_financiamiento': 'estatal',
                'tipo_adquisicion': 'arrendamientos',
                'modalidad_monto': 'adjudicacion_directa',
                'estado': 'pendiente',
                'prioridad': 'alta',
            },
            {
                'titulo': 'Adquisición de Medicamentos',
                'descripcion': 'Compra de medicamentos para centro de salud',
                'giro': 'Salud',
                'fuente_financiamiento': 'federal',
                'tipo_adquisicion': 'bienes',
                'modalidad_monto': 'licitacion',
                'estado': 'digitalizado',
                'prioridad': 'urgente',
            },
            {
                'titulo': 'Mantenimiento de Alumbrado Público',
                'descripcion': 'Servicio de mantenimiento del sistema de alumbrado',
                'giro': 'Servicios',
                'fuente_financiamiento': 'propio_municipal',
                'tipo_adquisicion': 'servicios',
                'modalidad_monto': 'concurso_invitacion',
                'estado': 'archivado',
                'prioridad': 'media',
            },
        ]

        for i, doc_data in enumerate(documentos_ejemplo, 1):
            numero = f"EXP-{datetime.now().year}-{i:04d}"
            
            documento, created = Documento.objects.get_or_create(
                numero_documento=numero,
                defaults={
                    **doc_data,
                    'tipo_documento': random.choice(tipos),
                    'departamento': random.choice(deptos),
                    'creado_por': random.choice(usuarios),
                    'fecha_documento': timezone.now().date() - timedelta(days=random.randint(1, 30)),
                    'fecha_vencimiento': timezone.now().date() + timedelta(days=random.randint(30, 90)),
                    'palabras_clave': 'expediente, adquisición, municipal',
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Documento: {documento.nombre_documento}')
                
                # Crear historial
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=documento.creado_por,
                    accion='Creación',
                    descripcion='Documento creado en el sistema',
                    estado_nuevo=documento.estado
                )

        # Crear configuraciones del sistema
        configuraciones = [
            ('max_file_size', '52428800', 'Tamaño máximo de archivo en bytes (50MB)'),
            ('allowed_extensions', '.pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff,.xls,.xlsx', 'Extensiones de archivo permitidas'),
            ('auto_archive_days', '365', 'Días después de los cuales archivar automáticamente'),
            ('notification_email', 'notificaciones@municipio.com', 'Email para notificaciones del sistema'),
        ]

        from digitalizacion.models import ConfiguracionSistema
        for clave, valor, desc in configuraciones:
            obj, created = ConfiguracionSistema.objects.get_or_create(
                clave=clave,
                defaults={'valor': valor, 'descripcion': desc}
            )
            if created:
                self.stdout.write(f'  ✓ Configuración: {clave}')

        self.stdout.write(self.style.SUCCESS('\n¡Datos de prueba creados exitosamente!'))
        self.stdout.write(self.style.WARNING('\nUsuarios creados:'))
        self.stdout.write('  - admin (superusuario)')
        for username, first_name, last_name, email in usuarios_demo:
            self.stdout.write(f'  - {username} (password: demo123)')
        
        self.stdout.write(self.style.WARNING(f'\nDocumentos creados: {len(documentos_ejemplo)}'))
        self.stdout.write(self.style.WARNING(f'Tipos de documento: {len(tipos_documento)}'))
        self.stdout.write(self.style.WARNING(f'Departamentos: {len(departamentos)}'))
