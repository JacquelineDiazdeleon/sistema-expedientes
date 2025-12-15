from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from digitalizacion.models import AreaTipoExpediente, Expediente


class Command(BaseCommand):
    help = 'Pobla las áreas por defecto para todos los tipos y subtipos de expediente'

    def handle(self, *args, **options):
        self.stdout.write('Poblando áreas por defecto para todos los subtipos...')
        
        # Definir las 17 áreas por defecto
        areas_defecto = [
            {
                'nombre': 'inicio',
                'titulo': 'INICIO',
                'descripcion': 'Área inicial para comenzar el expediente',
                'orden': 1,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'solicitud_area',
                'titulo': 'SOLICITUD DEL ÁREA',
                'descripcion': 'Solicitud formal del área solicitante',
                'orden': 2,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'cotizacion',
                'titulo': 'COTIZACIÓN',
                'descripcion': 'Documentos y información de cotización',
                'orden': 3,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'requisicion_sima',
                'titulo': 'REQUISICIÓN SIMA',
                'descripcion': 'Requisición en el sistema SIMA',
                'orden': 4,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'suficiencia_presupuestal',
                'titulo': 'SUFICIENCIA PRESUPUESTAL',
                'descripcion': 'Verificación de suficiencia presupuestal',
                'orden': 5,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'aprobacion_director',
                'titulo': 'APROBACIÓN DIRECTOR ADMINISTRATIVO',
                'descripcion': 'Aprobación del Director Administrativo',
                'orden': 6,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'aprobacion_secretario',
                'titulo': 'APROBACIÓN SECRETARIO',
                'descripcion': 'Aprobación del Secretario',
                'orden': 7,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'notificacion_compras',
                'titulo': 'NOTIFICACIÓN A COMPRAS MUNICIPALES',
                'descripcion': 'Notificación al área de compras municipales',
                'orden': 8,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'valoracion_tipo',
                'titulo': 'VALORACIÓN PARA TIPO DE ADQUISICIÓN',
                'descripcion': 'Valoración del tipo de adquisición correspondiente',
                'orden': 9,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'adjudicacion',
                'titulo': 'ADJUDICACIÓN',
                'descripcion': 'Proceso de adjudicación del expediente',
                'orden': 10,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'formalizacion',
                'titulo': 'FORMALIZACIÓN CON ORDEN DE COMPRA',
                'descripcion': 'Formalización mediante orden de compra',
                'orden': 11,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'contrato',
                'titulo': 'CONTRATO',
                'descripcion': 'Documentación del contrato',
                'orden': 12,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'recepcion_bien',
                'titulo': 'RECEPCIÓN DEL BIEN O SERVICIO',
                'descripcion': 'Recepción y verificación del bien o servicio',
                'orden': 13,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'recepcion_facturacion',
                'titulo': 'RECEPCIÓN DE FACTURACIÓN',
                'descripcion': 'Recepción de documentos de facturación',
                'orden': 14,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'generacion_evidencia',
                'titulo': 'GENERACIÓN DE EVIDENCIA',
                'descripcion': 'Generación de evidencia documental',
                'orden': 15,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'envio_compras',
                'titulo': 'ENVÍO DE EXPEDIENTE A COMPRAS',
                'descripcion': 'Envío del expediente completo al área de compras',
                'orden': 16,
                'tipo_area': 'mixto'
            },
            {
                'nombre': 'pago',
                'titulo': 'PAGO',
                'descripcion': 'Proceso de pago final',
                'orden': 17,
                'tipo_area': 'mixto'
            },
        ]
        
        # Obtener el usuario sistema
        usuario_sistema = User.objects.filter(is_superuser=True).first()
        
        total_creadas = 0
        total_existentes = 0
        
        # Para cada tipo de expediente
        tipos_expediente = ['giro', 'fuente', 'tipo_adquisicion', 'monto']
        
        for tipo in tipos_expediente:
            self.stdout.write(f'\nProcesando tipo: {tipo}')
            
            # Obtener subtipos para este tipo
            subtipos = AreaTipoExpediente.get_subtipos_por_tipo(tipo)
            
            for subtipo, subtipo_display in subtipos:
                self.stdout.write(f'  Subtipo: {subtipo} ({subtipo_display})')
                
                for area_data in areas_defecto:
                    # Verificar si ya existe para este tipo y subtipo
                    area_existente = AreaTipoExpediente.objects.filter(
                        tipo_expediente=tipo,
                        subtipo_expediente=subtipo,
                        nombre=area_data['nombre']
                    ).first()
                    
                    if area_existente:
                        total_existentes += 1
                        self.stdout.write(f'    - {area_data["titulo"]} ya existe')
                    else:
                        # Crear el área
                        area = AreaTipoExpediente.objects.create(
                            nombre=area_data['nombre'],
                            titulo=area_data['titulo'],
                            descripcion=area_data['descripcion'],
                            tipo_expediente=tipo,
                            subtipo_expediente=subtipo,
                            tipo_area=area_data['tipo_area'],
                            orden=area_data['orden'],
                            obligatoria=True,
                            activa=True,
                            es_default=True,
                            tipos_archivo_permitidos='pdf,docx,xlsx,doc,xls,jpg,jpeg,png',
                            tamaño_max_archivo=10,
                            creada_por=usuario_sistema
                        )
                        total_creadas += 1
                        self.stdout.write(f'    + Creada: {area_data["titulo"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado:\n'
                f'  - Áreas creadas: {total_creadas}\n'
                f'  - Áreas existentes: {total_existentes}\n'
                f'  - Total áreas por tipo/subtipo: {len(areas_defecto)}'
            )
        )
        
        # Mostrar resumen por tipo y subtipo
        self.stdout.write('\nResumen por tipo y subtipo:')
        for tipo in tipos_expediente:
            tipo_display = dict(Expediente.TIPO_CHOICES)[tipo]
            self.stdout.write(f'\n{tipo_display}:')
            subtipos = AreaTipoExpediente.get_subtipos_por_tipo(tipo)
            for subtipo, subtipo_display in subtipos:
                count = AreaTipoExpediente.objects.filter(
                    tipo_expediente=tipo, 
                    subtipo_expediente=subtipo
                ).count()
                self.stdout.write(f'  - {subtipo_display}: {count} áreas')
