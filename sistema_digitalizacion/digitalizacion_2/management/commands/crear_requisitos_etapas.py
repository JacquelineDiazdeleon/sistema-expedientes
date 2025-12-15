from django.core.management.base import BaseCommand
from digitalizacion.models import RequisitoEtapa


class Command(BaseCommand):
    help = 'Crea los requisitos por etapa según el esquema exacto solicitado'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando requisitos por etapa según esquema actualizado...'))

        # Limpiar requisitos existentes
        RequisitoEtapa.objects.all().delete()

        # Requisitos generales para tipo Por Giro (sin documentos específicos adicionales)
        requisitos_giro = {
            'inicio': ['Documentación de inicio del proceso'],
            'solicitud_area': ['Solicitud del área (necesidad)'],
            'cotizacion': ['Cotización'],
            'requisicion_sima': ['Requisición SIMA (número guía)'],
            'suficiencia_presupuestal': ['Suficiencia presupuestal'],
            'aprobacion_director': ['Aprobación Director Administrativo'],
            'aprobacion_secretario': ['Aprobación Secretario'],
            'notificacion_compras': ['Notificación a Compras Municipales'],
            'valoracion_tipo': ['Valoración para tipo de adquisición'],
            'adjudicacion': ['Adjudicación'],
            'formalizacion': ['Formalización con orden de compra'],
            'contrato': ['Contrato'],
            'recepcion_bien': ['Recepción del bien o servicio'],
            'recepcion_facturacion': ['Recepción de facturación'],
            'generacion_evidencia': ['Generación de evidencia'],
            'envio_compras': ['Envío de expediente a compras'],
            'pago': ['Pago'],
        }

        # Requisitos específicos por Fuente de Financiamiento
        requisitos_fuente_base = requisitos_giro.copy()
        requisitos_fuente_especificos = {
            'inicio': ['Expediente técnico inicial'],
            'valoracion_tipo': ['Oficio de autorización'],
            'adjudicacion': ['Expediente técnico modificado'],
            'pago': ['Expediente técnico final'],
        }

        # Requisitos específicos por Tipo de Adquisición - Bienes
        requisitos_tipo_bienes = {
            'valoracion_tipo': ['Oficio de solicitud de control patrimonial'],
        }

        # Requisitos específicos por Tipo de Adquisición - Servicios
        requisitos_tipo_servicios = {
            'valoracion_tipo': ['Oficio de Recursos Humanos', 'Oficio de Tecnologías de la Información'],
        }

        # Documentos específicos para Por Monto - Compra directa
        documentos_compra_directa = {
            'solicitud_area': ['Requisición'],
            'cotizacion': ['Cotizaciones'],
            'valoracion_tipo': ['Cuadro comparativo'],
            'formalizacion': ['Orden de pedido'],
            'recepcion_bien': ['Documentación comprobatoria de entrega del bien o prestación del servicio'],
            'pago': ['Comprobantes de pago al proveedor (CFDI) (Anticipo y parcialidades conforme a orden de compra)'],
        }

        # Documentos específicos para Por Monto - Concurso por invitación
        documentos_concurso = {
            'solicitud_area': ['Requisición'],
            'cotizacion': [
                'Cotizaciones',
                'Cuadro comparativo',
                'Requisición',
                'Bases / Convocatoria',
                'Cartas de invitación a proveedores (correo electrónico)',
                'Acuse de recibo de la invitación entregada por el proveedor',
                'Planteamientos presentados por los proveedores derivados de las Bases/Convocatoria (Preguntas)',
                'Lista de asistencia de la Junta de Aclaraciones',
                'Acta de Junta de Aclaraciones',
                'Lista de asistencia al acto de presentación y apertura de propuestas',
                'Propuesta Técnica y Económica (desglose por requisitos de la convocatoria)',
                'Acta Circunstanciada de Inscripción y Apertura de Propuestas Técnicas',
                'Dictamen Técnico',
                'Fallo Técnico',
                'Acta de apertura de propuestas económicas',
                'Fallo económico',
            ],
            'adjudicacion': ['Fallo de adjudicación'],
            'formalizacion': ['Orden de compra'],
            'contrato': [
                'Contrato',
                'Garantías (seriedad, cumplimiento, calidad, etc.)',
                'Convenio modificatorio',
                'Documentación comprometida por el proveedor (oficios, cartas, certificados)',
            ],
            'recepcion_bien': ['Documentación comprobatoria de entrega'],
            'pago': ['Comprobantes de pago (CFDI)'],
        }

        # Documentos específicos para Por Monto - Licitación
        documentos_licitacion = {
            'solicitud_area': ['Requisición'],
            'cotizacion': [
                'Cotizaciones',
                'Cuadro comparativo',
                'Requisición',
                'Bases / Convocatoria',
                'Pago de Bases',
                'Planteamientos de proveedores',
                'Lista de asistencia a junta aclaraciones',
                'Acta de junta aclaraciones',
                'Lista de asistencia acto presentación propuestas',
                'Propuesta Técnica y Económica',
                'Acta inscripción y apertura propuestas técnicas',
                'Dictamen Técnico',
                'Fallo Técnico',
                'Acta apertura propuestas económicas',
                'Fallo económico',
            ],
            'adjudicacion': ['Fallo de adjudicación'],
            'formalizacion': ['Orden de compra'],
            'contrato': [
                'Contrato',
                'Garantías',
                'Convenio modificatorio',
                'Documentación comprometida',
            ],
            'recepcion_bien': ['Documentación comprobatoria de entrega'],
            'pago': ['Comprobantes de pago (CFDI)'],
        }

        # Documentos específicos para Por Monto - Adjudicación directa
        documentos_adjudicacion_directa = {
            'cotizacion': ['Cotizaciones', 'Cuadro comparativo'],
            'solicitud_area': ['Requisición'],
            'valoracion_tipo': ['Documento para dictamen sobre no procedencia de licitación o concurso'],
            'adjudicacion': ['Adjudicación por parte del comité'],
            'contrato': ['Contrato', 'Garantías', 'Convenio modificatorio'],
            'recepcion_bien': ['Documentación comprobatoria de entrega'],
            'pago': ['Comprobantes de pago (CFDI)'],
        }

        contador = 0

        # Crear requisitos para tipo Por Giro
        for etapa, requisitos in requisitos_giro.items():
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='giro',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento requerido para expediente por giro en etapa {etapa}',
                    obligatorio=True,
                    orden=i + 1
                )
                contador += 1

        # Crear requisitos para tipo Por Fuente de Financiamiento
        for etapa, requisitos in requisitos_fuente_base.items():
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='fuente',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento base para fuente de financiamiento en etapa {etapa}',
                    obligatorio=True,
                    orden=i + 1
                )
                contador += 1

        # Agregar documentos específicos para fuente de financiamiento
        for etapa, requisitos in requisitos_fuente_especificos.items():
            base_count = len(requisitos_fuente_base.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='fuente',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico de fuente de financiamiento en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Crear requisitos base para tipo Por Tipo de Adquisición
        for etapa, requisitos in requisitos_giro.items():
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='tipo_adquisicion',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento base para tipo de adquisición en etapa {etapa}',
                    obligatorio=True,
                    orden=i + 1
                )
                contador += 1

        # Agregar documentos específicos para Bienes
        for etapa, requisitos in requisitos_tipo_bienes.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='tipo_adquisicion',
                    subtipo='bienes',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para bienes en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Agregar documentos específicos para Servicios
        for etapa, requisitos in requisitos_tipo_servicios.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='tipo_adquisicion',
                    subtipo='servicios',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para servicios en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Crear requisitos base para tipo Por Monto
        for etapa, requisitos in requisitos_giro.items():
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='monto',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento base para expediente por monto en etapa {etapa}',
                    obligatorio=True,
                    orden=i + 1
                )
                contador += 1

        # Crear documentos específicos para Por Monto - Compra directa
        for etapa, requisitos in documentos_compra_directa.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='monto',
                    subtipo='compra_directa',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para compra directa en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Crear documentos específicos para Por Monto - Concurso por invitación
        for etapa, requisitos in documentos_concurso.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='monto',
                    subtipo='concurso_invitacion',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para concurso por invitación en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Crear documentos específicos para Por Monto - Licitación
        for etapa, requisitos in documentos_licitacion.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='monto',
                    subtipo='licitacion',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para licitación en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        # Crear documentos específicos para Por Monto - Adjudicación directa
        for etapa, requisitos in documentos_adjudicacion_directa.items():
            base_count = len(requisitos_giro.get(etapa, []))
            for i, requisito in enumerate(requisitos):
                RequisitoEtapa.objects.create(
                    tipo_expediente='monto',
                    subtipo='adjudicacion_directa',
                    etapa=etapa,
                    nombre_requisito=requisito,
                    descripcion=f'Documento específico para adjudicación directa en etapa {etapa}',
                    obligatorio=True,
                    orden=base_count + i + 1
                )
                contador += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ {contador} requisitos creados exitosamente según el esquema actualizado')
        )

        # Mostrar resumen
        tipos_expediente = ['giro', 'fuente', 'tipo_adquisicion', 'monto']
        resumen = {}
        for tipo in tipos_expediente:
            count = RequisitoEtapa.objects.filter(tipo_expediente=tipo).count()
            resumen[tipo] = count

        self.stdout.write('\nResumen por tipo:')
        for tipo, count in resumen.items():
            self.stdout.write(f'  - {tipo}: {count} requisitos')

        # Mostrar subtotales para los tipos con modalidades específicas
        self.stdout.write('\nSubtipos específicos:')
        subtipos = [
            ('compra_directa', 'Compra Directa'),
            ('concurso_invitacion', 'Concurso por Invitación'),
            ('licitacion', 'Licitación'),
            ('adjudicacion_directa', 'Adjudicación Directa'),
            ('bienes', 'Bienes'),
            ('servicios', 'Servicios'),
        ]
        
        for subtipo, nombre in subtipos:
            count = RequisitoEtapa.objects.filter(subtipo=subtipo).count()
            if count > 0:
                self.stdout.write(f'  - {nombre}: {count} documentos específicos')