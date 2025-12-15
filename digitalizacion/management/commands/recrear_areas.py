from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import AreaTipoExpediente, ValorAreaExpediente, CampoAreaPersonalizado, ValorCampoPersonalizadoArea

class Command(BaseCommand):
    help = 'Elimina todas las áreas existentes y las recrea con la configuración por defecto'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando proceso de recreación de áreas...')
        
        # 1. Eliminar registros relacionados primero
        self.stdout.write('Eliminando valores de campos personalizados...')
        ValorCampoPersonalizadoArea.objects.all().delete()
        
        self.stdout.write('Eliminando valores de áreas...')
        ValorAreaExpediente.objects.all().delete()
        
        self.stdout.write('Eliminando campos personalizados...')
        CampoAreaPersonalizado.objects.all().delete()
        
        self.stdout.write('Eliminando áreas existentes...')
        AreaTipoExpediente.objects.all().delete()
        
        # 2. Crear áreas por defecto
        self.crear_areas_por_defecto()
        
        self.stdout.write(self.style.SUCCESS('Proceso completado. Las áreas han sido recreadas correctamente.'))
    
    def crear_areas_por_defecto(self):
        """Crea las áreas por defecto para todos los tipos de expediente"""
        # Obtener el usuario administrador o crear uno si no existe
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        
        # Áreas por defecto para todos los tipos de expediente
        areas_defecto = [
            {
                'nombre': 'solicitud_area',
                'titulo': 'Solicitud del Área',
                'descripcion': 'Documentación inicial de la solicitud del área',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion',
                'titulo': 'Cotización',
                'descripcion': 'Documentos de cotización',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion_sima',
                'titulo': 'Requisición SIMA',
                'descripcion': 'Documentos de la requisición en SIMA',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'suficiencia_presupuestal',
                'titulo': 'Suficiencia Presupuestal',
                'descripcion': 'Documentos de suficiencia presupuestal',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': True
            },
            {
                'nombre': 'aprobacion_director',
                'titulo': 'Aprobación Director',
                'descripcion': 'Documentos de aprobación del director',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'aprobacion_secretario',
                'titulo': 'Aprobación Secretario',
                'descripcion': 'Documentos de aprobación del secretario',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'notificacion_compras',
                'titulo': 'Notificación a Compras',
                'descripcion': 'Documentos de notificación a compras',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'valoracion_tipo',
                'titulo': 'Valoración para Tipo de Adquisición',
                'descripcion': 'Documentos de valoración para el tipo de adquisición',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'adjudicacion',
                'titulo': 'Adjudicación',
                'descripcion': 'Documentos de adjudicación',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            },
            {
                'nombre': 'formalizacion',
                'titulo': 'Formalización',
                'descripcion': 'Documentos de formalización',
                'tipo_area': 'mixto',
                'orden': 10,
                'obligatoria': True
            },
            {
                'nombre': 'contrato',
                'titulo': 'Contrato',
                'descripcion': 'Documentos del contrato',
                'tipo_area': 'mixto',
                'orden': 11,
                'obligatoria': True
            },
            {
                'nombre': 'recepcion_bien',
                'titulo': 'Recepción del Bien/Servicio',
                'descripcion': 'Documentos de recepción del bien o servicio',
                'tipo_area': 'mixto',
                'orden': 12,
                'obligatoria': True
            },
            {
                'nombre': 'recepcion_facturacion',
                'titulo': 'Recepción de Facturación',
                'descripcion': 'Documentos de facturación',
                'tipo_area': 'mixto',
                'orden': 13,
                'obligatoria': True
            },
            {
                'nombre': 'generacion_evidencia',
                'titulo': 'Generación de Evidencia',
                'descripcion': 'Documentos de evidencia',
                'tipo_area': 'mixto',
                'orden': 14,
                'obligatoria': True
            },
            {
                'nombre': 'envio_compras',
                'titulo': 'Envío a Compras',
                'descripcion': 'Documentos de envío a compras',
                'tipo_area': 'mixto',
                'orden': 15,
                'obligatoria': True
            },
            {
                'nombre': 'pago',
                'titulo': 'Pago',
                'descripcion': 'Documentos de pago',
                'tipo_area': 'mixto',
                'orden': 16,
                'obligatoria': True
            },
            {
                'nombre': 'completado',
                'titulo': 'Expediente Completado',
                'descripcion': 'Documentos finales del expediente completado',
                'tipo_area': 'mixto',
                'orden': 17,
                'obligatoria': True
            },
            {
                'nombre': 'rechazado',
                'titulo': 'Expediente Rechazado',
                'descripcion': 'Documentos del expediente rechazado',
                'tipo_area': 'mixto',
                'orden': 18,
                'obligatoria': True
            }
        ]
        
        # Tipos de expediente disponibles
        TIPOS_EXPEDIENTE = [
            'licitacion',
            'concurso_invitacion',
            'compra_directa',
            'adjudicacion_directa'
        ]
        
        # Crear áreas para cada tipo de expediente
        for tipo in TIPOS_EXPEDIENTE:
            for area_data in areas_defecto:
                # Crear el área
                area = AreaTipoExpediente.objects.create(
                    nombre=area_data['nombre'],
                    titulo=area_data['titulo'],
                    descripcion=area_data['descripcion'],
                    tipo_expediente=tipo,
                    tipo_area=area_data['tipo_area'],
                    orden=area_data['orden'],
                    obligatoria=area_data['obligatoria'],
                    es_default=True,
                    creada_por=admin_user
                )
                
                self.stdout.write(self.style.SUCCESS(f'Área creada: {tipo} - {area.titulo}'))
        
        self.stdout.write(self.style.SUCCESS('Todas las áreas han sido creadas exitosamente.'))
