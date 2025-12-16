from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from digitalizacion.models import AreaTipoExpediente, Expediente

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula las áreas por tipo de expediente en la base de datos'

    def handle(self, *args, **options):
        # Obtener el usuario administrador o crear uno si no existe
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado'))

        # Diccionario con las áreas por tipo y subtipo de expediente
        areas_por_tipo = {
            # LICITACIÓN (RECURSO PROPIO)
            ('licitacion', 'recurso_propio'): [
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'requisicion',
                'cotizacion',
                'invitacion_licitacion',
                'acta_junta_aclaraciones',
                'acta_recepcion_propuestas',
                'dictamen_comparativo',
                'acta_elaboracion_fallo',
                'acta_lectura_fallo',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'oficio_conformidad',
                'anexos_licitacion',
            ],
            
            # LICITACIÓN (FONDO FEDERAL)
            ('licitacion', 'fondo_federal'): [
                'solicitud_aprobacion_fondo',
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'estudio_mercado',
                'requisicion',
                'cotizacion',
                'invitacion_licitacion',
                'acta_junta_aclaraciones',
                'acta_recepcion_propuestas',
                'dictamen_comparativo',
                'acta_elaboracion_fallo',
                'acta_lectura_fallo',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad',
                'anexos_licitacion',
            ],
            
            # CONCURSO POR INVITACIÓN
            ('concurso_invitacion', None): [
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'requisicion',
                'cotizacion',
                'invitacion_concurso',
                'acta_junta_aclaraciones',
                'acta_recepcion_propuestas',
                'dictamen_comparativo',
                'acta_elaboracion_fallo',
                'acta_lectura_fallo',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'oficio_conformidad',
                'anexos_concurso',
            ],
            
            # COMPRA DIRECTA
            ('compra_directa', None): [
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'requisicion',
                'cotizacion',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'oficio_conformidad',
            ],
            
            # ADJUDICACIÓN DIRECTA
            ('adjudicacion_directa', None): [
                'solicitud_suficiencia_presupuestal',
                'solicitud_compromiso_pago',
                'oficio_control_patrimonial',
                'solicitud_avaluo_vehiculo',
                'solicitud_requisicion',
                'analisis_costo_beneficio',
                'requisicion',
                'cotizacion',
                'tres_cotizaciones',
                'avaluo',
                'documentacion_vehiculo',
                'invitacion_comite',
                'dictamen_adjudicacion',
                'acta_sesion_comite',
                'contrato',
                'constancia_proveedor',
                'constancia_situacion_fiscal',
                'comprobante_domicilio_fiscal',
                'apertura_establecimiento',
                'comprobante_domicilio_comercial',
                'opinion_sat',
                'opinion_imss',
                'opinion_infonavit',
                'opinion_finanzas_estado',
                'acta_constitutiva',
                'poder_notarial',
                'copia_ine',
                'carta_no_sancion',
                'carta_no_cargo_publico',
                'carta_compromiso',
                'curriculum_empresarial',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad',
                'anexos_adjudicacion',
            ],
        }

        # Mapeo de códigos a títulos descriptivos
        titulos_areas = {
            # Comunes
            'oficio_control_patrimonial': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
            'solicitud_requisicion': 'Solicitud de requisición del área',
            'requisicion': 'Requisición',
            'cotizacion': 'Cotización',
            'solicitud_pago': 'Solicitud de pago',
            'factura_xml_validacion': 'Factura, XML y validación',
            'orden_compra': 'Orden de compra',
            'vale_entrada': 'Vale de entrada',
            'oficio_conformidad': 'Oficio de conformidad y evidencia fotográfica',
            
            # Licitación/Concurso
            'invitacion_licitacion': 'Invitación a licitación',
            'invitacion_concurso': 'Invitación a concurso',
            'acta_junta_aclaraciones': 'Acta de junta de aclaraciones',
            'acta_recepcion_propuestas': 'Acta de recepción de propuestas técnicas',
            'dictamen_comparativo': 'Dictamen y cuadro comparativo',
            'acta_elaboracion_fallo': 'Acta de elaboración del fallo',
            'acta_lectura_fallo': 'Acta de lectura de fallo',
            'anexos_licitacion': 'Anexos de licitación',
            'anexos_concurso': 'Anexos de concurso',
            'anexos_adjudicacion': 'Anexos de adjudicación',
            
            # Fondo Federal
            'solicitud_aprobacion_fondo': 'Solicitud y aprobación de fondo',
            'estudio_mercado': 'Estudio de mercado',
            'acta_entrega_ine': 'Acta de entrega con INE de proveedor y persona que recibe',
            'acta_entrega_proveedor': 'Acta de entrega de proveedor',
            
            # Adjudicación Directa
            'solicitud_suficiencia_presupuestal': 'Solicitud de suficiencia presupuestal y autorización de compromiso de pago',
            'solicitud_compromiso_pago': 'Solicitud y contestación de compromiso de pago',
            'solicitud_avaluo_vehiculo': 'Solicitud de avalúo en caso de ser renta de vehículo',
            'analisis_costo_beneficio': 'Análisis costo beneficio',
            'tres_cotizaciones': '3 o más cotizaciones',
            'avaluo': 'Avalúo en caso de ser requerido',
            'documentacion_vehiculo': 'En caso de ser vehículos: facturas, seguro, chofer responsable',
            'invitacion_comite': 'Invitación al comité de adquisiciones',
            'dictamen_adjudicacion': 'Solicitud y dictamen de la adjudicación',
            'acta_sesion_comite': 'Acta de sesión de comité',
            'constancia_proveedor': 'Constancia de proveedor',
            'constancia_situacion_fiscal': 'Constancia de situación fiscal',
            'comprobante_domicilio_fiscal': 'Comprobante de domicilio fiscal',
            'apertura_establecimiento': 'Apertura de establecimiento (si aplica)',
            'comprobante_domicilio_comercial': 'Comprobante de domicilio de establecimiento comercial (si aplica)',
            'opinion_sat': 'Opinión de cumplimiento de SAT positiva',
            'opinion_imss': 'Opinión de cumplimiento de IMSS',
            'opinion_infonavit': 'Opinión de cumplimiento de INFONAVIT',
            'opinion_finanzas_estado': 'Opinión de cumplimiento de finanzas del estado',
            'acta_constitutiva': 'Acta constitutiva (personas morales)',
            'poder_notarial': 'Poder notarial (en caso de aplicar)',
            'copia_ine': 'Copia INE',
            'carta_no_sancion': 'Carta de no sanción',
            'carta_no_cargo_publico': 'Carta de no cargo público',
            'carta_compromiso': 'Carta compromiso',
            'curriculum_empresarial': 'Currículum empresarial',
        }

        # Primero, desactivar todas las áreas existentes
        AreaTipoExpediente.objects.update(activa=False)

        # Contadores para estadísticas
        creadas = 0
        actualizadas = 0
        
        # Procesar cada tipo y subtipo de expediente
        for (tipo_expediente, subtipo_expediente), areas in areas_por_tipo.items():
            for orden, codigo_area in enumerate(areas, 1):
                # Obtener el título descriptivo del área
                titulo = titulos_areas.get(codigo_area, codigo_area.replace('_', ' ').title())
                
                # Crear o actualizar el área
                area, created = AreaTipoExpediente.objects.update_or_create(
                    tipo_expediente=tipo_expediente,
                    subtipo_expediente=subtipo_expediente,
                    nombre=codigo_area,
                    defaults={
                        'titulo': titulo,
                        'tipo_area': 'mixto',
                        'orden': orden * 10,  # Multiplicar por 10 para permitir inserciones futuras
                        'obligatoria': True,
                        'activa': True,
                        'es_default': True,
                        'creada_por': admin_user,
                    }
                )
                
                if created:
                    creadas += 1
                else:
                    actualizadas += 1
        
        # Desactivar áreas que ya no están en la lista
        AreaTipoExpediente.objects.filter(es_default=True, activa=True).exclude(
            nombre__in=[area for areas in areas_por_tipo.values() for area in areas]
        ).update(activa=False)
        
        self.stdout.write(self.style.SUCCESS(
            f'Se han actualizado las áreas para los tipos de expediente. '
            f'Creadas: {creadas}, Actualizadas: {actualizadas}'
        ))
