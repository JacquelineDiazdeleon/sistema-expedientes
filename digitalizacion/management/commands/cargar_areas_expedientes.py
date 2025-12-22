from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from digitalizacion.models import AreaTipoExpediente

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga las áreas predefinidas para los diferentes tipos de expedientes'

    def handle(self, *args, **options):
        # Obtener o crear un usuario administrador para usar como creador
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado'))

        # Mapeo de tipos de expediente
        TIPOS_EXPEDIENTE = {
            'licitacion': 'licitacion',
            'concurso_invitacion': 'concurso_invitacion',
            'compra_directa': 'compra_directa',
            'adjudicacion_directa': 'adjudicacion_directa'
        }

        # Subtipos de licitación
        SUBTIPOS_LICITACION = {
            'recurso_propio': 'recurso_propio',
            'fondo_federal': 'fondo_federal'
        }

        # Definición de áreas por tipo y subtipo de expediente
        areas_config = [
            # LICITACIÓN (RECURSO PROPIO)
            {
                'tipo': 'licitacion',
                'subtipo': 'recurso_propio',
                'areas': [
                    'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                    'Solicitud de requisición del área',
                    'Requisición',
                    'Cotización',
                    'Invitación a licitación',
                    'Acta de junta de aclaraciones',
                    'Acta de recepción de propuestas técnicas',
                    'Dictamen y comparativo comparativo',
                    'Acta de elaboración del fallo',
                    'Acta de lectura de fallo',
                    'Contrato',
                    'Solicitud de pago',
                    'Factura, XML y validación',
                    'Orden de compra',
                    'Vale de entrada',
                    'Oficio de conformidad y evidencia fotográfica',
                    'Anexos de licitación'
                ]
            },
            # LICITACIÓN (FONDO FEDERAL)
            {
                'tipo': 'licitacion',
                'subtipo': 'fondo_federal',
                'areas': [
                    'Solicitud y aprobación de fondo',
                    'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                    'Solicitud de requisición del área',
                    'Estudio de mercado',
                    'Requisición',
                    'Cotización',
                    'Invitación a licitación',
                    'Acta de junta de aclaraciones',
                    'Acta de recepción de propuestas técnicas',
                    'Dictamen y cuadro comparativo',
                    'Acta de elaboración del fallo',
                    'Acta de lectura de fallo',
                    'Contrato',
                    'Solicitud de pago',
                    'Factura, XML y validación',
                    'Orden de compra',
                    'Vale de entrada',
                    'Acta de entrega con INE de proveedor y persona que recibe',
                    'Acta de entrega de proveedor',
                    'Oficio de conformidad y evidencia fotográfica',
                    'Anexos de licitación'
                ]
            },
            # CONCURSO POR INVITACIÓN
            {
                'tipo': 'concurso_invitacion',
                'subtipo': None,  # Aplica a todos los subtipos
                'areas': [
                    'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                    'Solicitud de requisición del área',
                    'Requisición',
                    'Cotización',
                    'Invitación a licitación',
                    'Acta de junta de aclaraciones',
                    'Acta de recepción de propuestas técnicas',
                    'Dictamen y cuadro comparativo',
                    'Acta de elaboración del fallo',
                    'Acta de lectura de fallo',
                    'Contrato',
                    'Solicitud de pago',
                    'Factura, XML y validación',
                    'Orden de compra',
                    'Vale de entrada',
                    'Oficio de conformidad y evidencia fotográfica',
                    'Anexos de licitación'
                ]
            },
            # COMPRA DIRECTA
            {
                'tipo': 'compra_directa',
                'subtipo': None,  # Aplica a todos los subtipos
                'areas': [
                    'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                    'Solicitud de requisición del área',
                    'Requisición',
                    'Cotización',
                    'Solicitud de pago',
                    'Factura, XML y validación',
                    'Orden de compra',
                    'Vale de entrada',
                    'Oficio de conformidad y evidencia fotográfica'
                ]
            },
            # ADJUDICACIÓN DIRECTA
            {
                'tipo': 'adjudicacion_directa',
                'subtipo': None,  # Aplica a todos los subtipos
                'areas': [
                    'Solicitud de suficiencia presupuestal y autorización de compromiso de pago',
                    'Solicitud y contestación de compromiso de pago',
                    'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                    'Solicitud de avaluo en caso de ser renta de algún vehículo',
                    'Solicitud de requisición del área',
                    'Análisis costo beneficio',
                    'Requisición',
                    'Cotización',
                    '3 o más cotizaciones',
                    'Avalúo en caso de ser requerido',
                    'En caso de ser vehículos: facturas, seguro, chofer responsable',
                    'Invitación al comité de adquisiciones',
                    'Solicitud y dictamen de la adjudicación',
                    'Acta de sesión de comité',
                    'Contrato',
                    'Constancia de proveedor',
                    'Constancia de situación fiscal',
                    'Comprobante de domicilio fiscal',
                    'Apertura de establecimiento (si aplica)',
                    'Comprobante de domicilio de establecimiento comercial (si aplica)',
                    'Opinión de cumplimiento de SAT positiva',
                    'Opinión de cumplimiento de IMSS',
                    'Opinión de cumplimiento de INFONAVIT',
                    'Opinión de cumplimiento finanzas del estado',
                    'Acta constitutiva (personas morales)',
                    'Poder notarial (en caso de aplicar)',
                    'Copia INE',
                    'Carta de no sanción',
                    'Carta de no cargo público',
                    'Carta compromiso',
                    'Currículum empresarial',
                    'Solicitud de pago',
                    'Factura, XML y validación',
                    'Orden de compra',
                    'Vale de entrada',
                    'Acta de entrega con INE de proveedor y persona que recibe',
                    'Acta de entrega de proveedor',
                    'Oficio de conformidad y evidencia fotográfica',
                    'Anexos de adjudicación'
                ]
            }
        ]

        # Crear las áreas
        total_creadas = 0
        total_actualizadas = 0

        for config in areas_config:
            tipo = TIPOS_EXPEDIENTE[config['tipo']]
            subtipo = config['subtipo']
            
            for i, nombre_area in enumerate(config['areas'], 1):
                # Generar un nombre interno único basado en el título
                nombre_interno = nombre_area.lower()\
                    .replace(' ', '_')\
                    .replace('á', 'a').replace('é', 'e').replace('í', 'i')\
                    .replace('ó', 'o').replace('ú', 'u')\
                    .replace('´', '').replace('`', '').replace("'", '')
                
                # Determinar el tipo de área basado en el nombre (esto es un ejemplo, puedes ajustarlo)
                if 'factura' in nombre_area.lower() or 'xml' in nombre_area.lower() or 'documento' in nombre_area.lower():
                    tipo_area = 'archivo'
                elif 'oficio' in nombre_area.lower() or 'solicitud' in nombre_area.lower() or 'carta' in nombre_area.lower():
                    tipo_area = 'mixto'
                else:
                    tipo_area = 'texto'
                
                # Configuración por defecto - Ninguna área es obligatoria
                defaults = {
                    'titulo': nombre_area,
                    'descripcion': f'Área para {nombre_area}',
                    'tipo_area': tipo_area,
                    'orden': i * 10,  # Multiplicar por 10 para permitir inserciones futuras
                    'obligatoria': False,
                    'activa': True,
                    'es_default': True,
                    'creada_por': admin_user
                }
                
                # Configuración específica para archivos
                if tipo_area in ['archivo', 'mixto']:
                    defaults.update({
                        'tipos_archivo_permitidos': 'pdf,doc,docx,xls,xlsx,jpg,jpeg,png',
                        'tamano_max_archivo': 10  # MB
                    })
                
                # Crear o actualizar el área
                area, created = AreaTipoExpediente.objects.update_or_create(
                    nombre=nombre_interno,
                    tipo_expediente=tipo,
                    subtipo_expediente=subtipo,
                    defaults=defaults
                )
                
                if created:
                    total_creadas += 1
                    self.stdout.write(self.style.SUCCESS(f'Creada área: {nombre_area}'))
                else:
                    total_actualizadas += 1
                    self.stdout.write(self.style.SUCCESS(f'Actualizada área: {nombre_area}'))

        self.stdout.write(self.style.SUCCESS(f'\nProceso completado. {total_creadas} áreas creadas, {total_actualizadas} actualizadas.'))
