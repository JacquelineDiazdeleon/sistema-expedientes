import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from digitalizacion.models import AreaTipoExpediente, CampoAreaPersonalizado

def crear_areas_por_defecto():
    """
    Crea las áreas por defecto para todos los tipos de expediente según la especificación
    """
    # Obtener el usuario administrador o crear uno si no existe
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Definición de áreas por tipo de expediente
    areas_config = {
        # 1. LICITACIÓN (RECURSO PROPIO)
        'licitacion_recurso_propio': [
            {
                'nombre': 'oficio_contraloria',
                'titulo': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'descripcion': 'Documentación de oficio y contestación de control patrimonial, TIC´s o capital humano',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_requisicion',
                'titulo': 'Solicitud de requisición del área',
                'descripcion': 'Documentación de solicitud de requisición del área',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion',
                'titulo': 'Requisición',
                'descripcion': 'Documentación de requisición',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion',
                'titulo': 'Cotización',
                'descripcion': 'Documentación de cotización',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': True
            },
            {
                'nombre': 'invitacion_licitacion',
                'titulo': 'Invitación a licitación',
                'descripcion': 'Documentación de invitación a licitación',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'acta_junta_aclaraciones',
                'titulo': 'Acta de junta de aclaraciones',
                'descripcion': 'Documentación de acta de junta de aclaraciones',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'acta_recepcion_propuestas',
                'titulo': 'Acta de recepción de propuestas técnicas',
                'descripcion': 'Documentación de acta de recepción de propuestas técnicas',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'dictamen_comparativo',
                'titulo': 'Dictamen y comparativo comparativo',
                'descripcion': 'Documentación de dictamen y comparativo comparativo',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'acta_elaboracion_fallo',
                'titulo': 'Acta de elaboración del fallo',
                'descripcion': 'Documentación de acta de elaboración del fallo',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            },
            {
                'nombre': 'acta_lectura_fallo',
                'titulo': 'Acta de lectura de fallo',
                'descripcion': 'Documentación de acta de lectura de fallo',
                'tipo_area': 'mixto',
                'orden': 10,
                'obligatoria': True
            },
            {
                'nombre': 'contrato',
                'titulo': 'Contrato',
                'descripcion': 'Documentación del contrato',
                'tipo_area': 'mixto',
                'orden': 11,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_pago',
                'titulo': 'Solicitud de pago',
                'descripcion': 'Documentación de solicitud de pago',
                'tipo_area': 'mixto',
                'orden': 12,
                'obligatoria': True
            },
            {
                'nombre': 'factura_xml',
                'titulo': 'Factura, XML y validación',
                'descripcion': 'Documentación de factura, XML y validación',
                'tipo_area': 'mixto',
                'orden': 13,
                'obligatoria': True
            },
            {
                'nombre': 'orden_compra',
                'titulo': 'Orden de compra',
                'descripcion': 'Documentación de orden de compra',
                'tipo_area': 'mixto',
                'orden': 14,
                'obligatoria': True
            },
            {
                'nombre': 'vale_entrada',
                'titulo': 'Vale de entrada',
                'descripcion': 'Documentación de vale de entrada',
                'tipo_area': 'mixto',
                'orden': 15,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_conformidad',
                'titulo': 'Oficio de conformidad y evidencia fotográfica',
                'descripcion': 'Documentación de oficio de conformidad y evidencia fotográfica',
                'tipo_area': 'mixto',
                'orden': 16,
                'obligatoria': True
            },
            {
                'nombre': 'anexos_licitacion',
                'titulo': 'Anexos de licitación',
                'descripcion': 'Documentación de anexos de licitación',
                'tipo_area': 'mixto',
                'orden': 17,
                'obligatoria': True
            }
        ],
        
        # 2. LICITACIÓN (FONDO FEDERAL)
        'licitacion_fondo_federal': [
            {
                'nombre': 'solicitud_aprobacion_fondo',
                'titulo': 'Solicitud y aprobación de fondo',
                'descripcion': 'Documentación de solicitud y aprobación de fondo',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_contraloria_federal',
                'titulo': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'descripcion': 'Documentación de oficio y contestación de control patrimonial, TIC´s o capital humano',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_requisicion_federal',
                'titulo': 'Solicitud de requisición del área',
                'descripcion': 'Documentación de solicitud de requisición del área',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'estudio_mercado',
                'titulo': 'Estudio de mercado',
                'descripcion': 'Documentación de estudio de mercado',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion_federal',
                'titulo': 'Requisición',
                'descripcion': 'Documentación de requisición',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion_federal',
                'titulo': 'Cotización',
                'descripcion': 'Documentación de cotización',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'invitacion_licitacion_federal',
                'titulo': 'Invitación a licitación',
                'descripcion': 'Documentación de invitación a licitación',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'acta_junta_aclaraciones_federal',
                'titulo': 'Acta de junta de aclaraciones',
                'descripcion': 'Documentación de acta de junta de aclaraciones',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'acta_recepcion_propuestas_federal',
                'titulo': 'Acta de recepción de propuestas técnicas',
                'descripcion': 'Documentación de acta de recepción de propuestas técnicas',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            },
            {
                'nombre': 'dictamen_comparativo_federal',
                'titulo': 'Dictamen y cuadro comparativo',
                'descripcion': 'Documentación de dictamen y cuadro comparativo',
                'tipo_area': 'mixto',
                'orden': 10,
                'obligatoria': True
            },
            {
                'nombre': 'acta_elaboracion_fallo_federal',
                'titulo': 'Acta de elaboración del fallo',
                'descripcion': 'Documentación de acta de elaboración del fallo',
                'tipo_area': 'mixto',
                'orden': 11,
                'obligatoria': True
            },
            {
                'nombre': 'acta_lectura_fallo_federal',
                'titulo': 'Acta de lectura de fallo',
                'descripcion': 'Documentación de acta de lectura de fallo',
                'tipo_area': 'mixto',
                'orden': 12,
                'obligatoria': True
            },
            {
                'nombre': 'contrato_federal',
                'titulo': 'Contrato',
                'descripcion': 'Documentación del contrato',
                'tipo_area': 'mixto',
                'orden': 13,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_pago_federal',
                'titulo': 'Solicitud de pago',
                'descripcion': 'Documentación de solicitud de pago',
                'tipo_area': 'mixto',
                'orden': 14,
                'obligatoria': True
            },
            {
                'nombre': 'factura_xml_federal',
                'titulo': 'Factura, XML y validación',
                'descripcion': 'Documentación de factura, XML y validación',
                'tipo_area': 'mixto',
                'orden': 15,
                'obligatoria': True
            },
            {
                'nombre': 'orden_compra_federal',
                'titulo': 'Orden de compra',
                'descripcion': 'Documentación de orden de compra',
                'tipo_area': 'mixto',
                'orden': 16,
                'obligatoria': True
            },
            {
                'nombre': 'vale_entrada_federal',
                'titulo': 'Vale de entrada',
                'descripcion': 'Documentación de vale de entrada',
                'tipo_area': 'mixto',
                'orden': 17,
                'obligatoria': True
            },
            {
                'nombre': 'acta_entrega_ine',
                'titulo': 'Acta de entrega con INE de proveedor y persona que recibe',
                'descripcion': 'Documentación de acta de entrega con INE de proveedor y persona que recibe',
                'tipo_area': 'mixto',
                'orden': 18,
                'obligatoria': True
            },
            {
                'nombre': 'acta_entrega_proveedor',
                'titulo': 'Acta de entrega de proveedor',
                'descripcion': 'Documentación de acta de entrega de proveedor',
                'tipo_area': 'mixto',
                'orden': 19,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_conformidad_federal',
                'titulo': 'Oficio de conformidad y evidencia fotográfica',
                'descripcion': 'Documentación de oficio de conformidad y evidencia fotográfica',
                'tipo_area': 'mixto',
                'orden': 20,
                'obligatoria': True
            },
            {
                'nombre': 'anexos_licitacion_federal',
                'titulo': 'Anexos de licitación',
                'descripcion': 'Documentación de anexos de licitación',
                'tipo_area': 'mixto',
                'orden': 21,
                'obligatoria': True
            }
        ],
        
        # 3. CONCURSO POR INVITACIÓN (RECURSO PROPIO / FEDERAL / ESTATAL)
        'concurso_invitacion': [
            {
                'nombre': 'oficio_contraloria_invitacion',
                'titulo': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'descripcion': 'Documentación de oficio y contestación de control patrimonial, TIC´s o capital humano',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_requisicion_invitacion',
                'titulo': 'Solicitud de requisición del área',
                'descripcion': 'Documentación de solicitud de requisición del área',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion_invitacion',
                'titulo': 'Requisición',
                'descripcion': 'Documentación de requisición',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion_invitacion',
                'titulo': 'Cotización',
                'descripcion': 'Documentación de cotización',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': True
            },
            {
                'nombre': 'invitacion_concurso',
                'titulo': 'Invitación a licitación',
                'descripcion': 'Documentación de invitación a licitación',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'acta_junta_aclaraciones_invitacion',
                'titulo': 'Acta de junta de aclaraciones',
                'descripcion': 'Documentación de acta de junta de aclaraciones',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'acta_recepcion_propuestas_invitacion',
                'titulo': 'Acta de recepción de propuestas técnicas',
                'descripcion': 'Documentación de acta de recepción de propuestas técnicas',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'dictamen_comparativo_invitacion',
                'titulo': 'Dictamen y cuadro comparativo',
                'descripcion': 'Documentación de dictamen y cuadro comparativo',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'acta_elaboracion_fallo_invitacion',
                'titulo': 'Acta de elaboración del fallo',
                'descripcion': 'Documentación de acta de elaboración del fallo',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            },
            {
                'nombre': 'acta_lectura_fallo_invitacion',
                'titulo': 'Acta de lectura de fallo',
                'descripcion': 'Documentación de acta de lectura de fallo',
                'tipo_area': 'mixto',
                'orden': 10,
                'obligatoria': True
            },
            {
                'nombre': 'contrato_invitacion',
                'titulo': 'Contrato',
                'descripcion': 'Documentación del contrato',
                'tipo_area': 'mixto',
                'orden': 11,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_pago_invitacion',
                'titulo': 'Solicitud de pago',
                'descripcion': 'Documentación de solicitud de pago',
                'tipo_area': 'mixto',
                'orden': 12,
                'obligatoria': True
            },
            {
                'nombre': 'factura_xml_invitacion',
                'titulo': 'Factura, XML y validación',
                'descripcion': 'Documentación de factura, XML y validación',
                'tipo_area': 'mixto',
                'orden': 13,
                'obligatoria': True
            },
            {
                'nombre': 'orden_compra_invitacion',
                'titulo': 'Orden de compra',
                'descripcion': 'Documentación de orden de compra',
                'tipo_area': 'mixto',
                'orden': 14,
                'obligatoria': True
            },
            {
                'nombre': 'vale_entrada_invitacion',
                'titulo': 'Vale de entrada',
                'descripcion': 'Documentación de vale de entrada',
                'tipo_area': 'mixto',
                'orden': 15,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_conformidad_invitacion',
                'titulo': 'Oficio de conformidad y evidencia fotográfica',
                'descripcion': 'Documentación de oficio de conformidad y evidencia fotográfica',
                'tipo_area': 'mixto',
                'orden': 16,
                'obligatoria': True
            },
            {
                'nombre': 'anexos_licitacion_invitacion',
                'titulo': 'Anexos de licitación',
                'descripcion': 'Documentación de anexos de licitación',
                'tipo_area': 'mixto',
                'orden': 17,
                'obligatoria': True
            }
        ],
        
        # 4. COMPRA DIRECTA (RECURSO PROPIO / FEDERAL / ESTATAL)
        'compra_directa': [
            {
                'nombre': 'oficio_contraloria_compra',
                'titulo': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'descripcion': 'Documentación de oficio y contestación de control patrimonial, TIC´s o capital humano',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_requisicion_compra',
                'titulo': 'Solicitud de requisición del área',
                'descripcion': 'Documentación de solicitud de requisición del área',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion_compra',
                'titulo': 'Requisición',
                'descripcion': 'Documentación de requisición',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion_compra',
                'titulo': 'Cotización',
                'descripcion': 'Documentación de cotización',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_pago_compra',
                'titulo': 'Solicitud de pago',
                'descripcion': 'Documentación de solicitud de pago',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'factura_xml_compra',
                'titulo': 'Factura, XML y validación',
                'descripcion': 'Documentación de factura, XML y validación',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'orden_compra_compra',
                'titulo': 'Orden de compra',
                'descripcion': 'Documentación de orden de compra',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'vale_entrada_compra',
                'titulo': 'Vale de entrada',
                'descripcion': 'Documentación de vale de entrada',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_conformidad_compra',
                'titulo': 'Oficio de conformidad y evidencia fotográfica',
                'descripcion': 'Documentación de oficio de conformidad y evidencia fotográfica',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            }
        ],
        
        # 5. ADJUDICACIÓN DIRECTA (RECURSO PROPIO / FEDERAL / ESTATAL)
        'adjudicacion_directa': [
            # Documentos iniciales
            {
                'nombre': 'solicitud_suficiencia',
                'titulo': 'Solicitud de suficiencia presupuestal y autorización de compromiso de pago',
                'descripcion': 'Documentación de solicitud de suficiencia presupuestal y autorización de compromiso de pago',
                'tipo_area': 'mixto',
                'orden': 1,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_compromiso_pago',
                'titulo': 'Solicitud y contestación de compromiso de pago',
                'descripcion': 'Documentación de solicitud y contestación de compromiso de pago',
                'tipo_area': 'mixto',
                'orden': 2,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_contraloria_adj',
                'titulo': 'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'descripcion': 'Documentación de oficio y contestación de control patrimonial, TIC´s o capital humano',
                'tipo_area': 'mixto',
                'orden': 3,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_avaluo',
                'titulo': 'Solicitud de avalúo en caso de ser renta de algún vehículo',
                'descripcion': 'Documentación de solicitud de avalúo en caso de ser renta de algún vehículo',
                'tipo_area': 'mixto',
                'orden': 4,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'solicitud_requisicion_adj',
                'titulo': 'Solicitud de requisición del área',
                'descripcion': 'Documentación de solicitud de requisición del área',
                'tipo_area': 'mixto',
                'orden': 5,
                'obligatoria': True
            },
            {
                'nombre': 'analisis_costo_beneficio',
                'titulo': 'Análisis costo beneficio',
                'descripcion': 'Documentación de análisis costo beneficio',
                'tipo_area': 'mixto',
                'orden': 6,
                'obligatoria': True
            },
            {
                'nombre': 'requisicion_adj',
                'titulo': 'Requisición',
                'descripcion': 'Documentación de requisición',
                'tipo_area': 'mixto',
                'orden': 7,
                'obligatoria': True
            },
            {
                'nombre': 'cotizacion_adj',
                'titulo': 'Cotización',
                'descripcion': 'Documentación de cotización',
                'tipo_area': 'mixto',
                'orden': 8,
                'obligatoria': True
            },
            {
                'nombre': 'tres_cotizaciones',
                'titulo': '3 o más cotizaciones',
                'descripcion': 'Documentación de 3 o más cotizaciones',
                'tipo_area': 'mixto',
                'orden': 9,
                'obligatoria': True
            },
            {
                'nombre': 'avaluo',
                'titulo': 'Avalúo en caso de ser requerido',
                'descripcion': 'Documentación de avalúo en caso de ser requerido',
                'tipo_area': 'mixto',
                'orden': 10,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'documentos_vehiculo',
                'titulo': 'En caso de ser vehículos: facturas, seguro, chofer responsable',
                'descripcion': 'Documentación de vehículos: facturas, seguro, chofer responsable',
                'tipo_area': 'mixto',
                'orden': 11,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'invitacion_comite',
                'titulo': 'Invitación al comité de adquisiciones',
                'descripcion': 'Documentación de invitación al comité de adquisiciones',
                'tipo_area': 'mixto',
                'orden': 12,
                'obligatoria': True
            },
            {
                'nombre': 'solicitud_dictamen_adjudicacion',
                'titulo': 'Solicitud y dictamen de la adjudicación',
                'descripcion': 'Documentación de solicitud y dictamen de la adjudicación',
                'tipo_area': 'mixto',
                'orden': 13,
                'obligatoria': True
            },
            {
                'nombre': 'acta_sesion_comite',
                'titulo': 'Acta de sesión de comité',
                'descripcion': 'Documentación de acta de sesión de comité',
                'tipo_area': 'mixto',
                'orden': 14,
                'obligatoria': True
            },
            {
                'nombre': 'contrato_adj',
                'titulo': 'Contrato',
                'descripcion': 'Documentación del contrato',
                'tipo_area': 'mixto',
                'orden': 15,
                'obligatoria': True
            },
            # Documentos del proveedor
            {
                'nombre': 'constancia_proveedor',
                'titulo': 'Constancia de proveedor',
                'descripcion': 'Documentación de constancia de proveedor',
                'tipo_area': 'mixto',
                'orden': 16,
                'obligatoria': True
            },
            {
                'nombre': 'constancia_situacion_fiscal',
                'titulo': 'Constancia de situación fiscal',
                'descripcion': 'Documentación de constancia de situación fiscal',
                'tipo_area': 'mixto',
                'orden': 17,
                'obligatoria': True
            },
            {
                'nombre': 'comprobante_domicilio_fiscal',
                'titulo': 'Comprobante de domicilio fiscal',
                'descripcion': 'Documentación de comprobante de domicilio fiscal',
                'tipo_area': 'mixto',
                'orden': 18,
                'obligatoria': True
            },
            {
                'nombre': 'apertura_establecimiento',
                'titulo': 'Apertura de establecimiento (si aplica)',
                'descripcion': 'Documentación de apertura de establecimiento (si aplica)',
                'tipo_area': 'mixto',
                'orden': 19,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'comprobante_domicilio_establecimiento',
                'titulo': 'Comprobante de domicilio de establecimiento comercial (si aplica)',
                'descripcion': 'Documentación de comprobante de domicilio de establecimiento comercial (si aplica)',
                'tipo_area': 'mixto',
                'orden': 20,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'opinion_sat',
                'titulo': 'Opinión de cumplimiento de SAT positiva',
                'descripcion': 'Documentación de opinión de cumplimiento de SAT positiva',
                'tipo_area': 'mixto',
                'orden': 21,
                'obligatoria': True
            },
            {
                'nombre': 'opinion_imss',
                'titulo': 'Opinión de cumplimiento de IMSS',
                'descripcion': 'Documentación de opinión de cumplimiento de IMSS',
                'tipo_area': 'mixto',
                'orden': 22,
                'obligatoria': True
            },
            {
                'nombre': 'opinion_infonavit',
                'titulo': 'Opinión de cumplimiento de INFONAVIT',
                'descripcion': 'Documentación de opinión de cumplimiento de INFONAVIT',
                'tipo_area': 'mixto',
                'orden': 23,
                'obligatoria': True
            },
            {
                'nombre': 'opinion_finanzas',
                'titulo': 'Opinión de cumplimiento finanzas del estado',
                'descripcion': 'Documentación de opinión de cumplimiento finanzas del estado',
                'tipo_area': 'mixto',
                'orden': 24,
                'obligatoria': True
            },
            {
                'nombre': 'acta_constitutiva',
                'titulo': 'Acta constitutiva (personas morales)',
                'descripcion': 'Documentación de acta constitutiva (personas morales)',
                'tipo_area': 'mixto',
                'orden': 25,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'poder_notarial',
                'titulo': 'Poder notarial (en caso de aplicar)',
                'descripcion': 'Documentación de poder notarial (en caso de aplicar)',
                'tipo_area': 'mixto',
                'orden': 26,
                'obligatoria': False  # Solo si aplica
            },
            {
                'nombre': 'ine',
                'titulo': 'Copia INE',
                'descripcion': 'Documentación de copia de INE',
                'tipo_area': 'mixto',
                'orden': 27,
                'obligatoria': True
            },
            {
                'nombre': 'carta_no_sancion',
                'titulo': 'Carta de no sanción',
                'descripcion': 'Documentación de carta de no sanción',
                'tipo_area': 'mixto',
                'orden': 28,
                'obligatoria': True
            },
            {
                'nombre': 'carta_no_cargo_publico',
                'titulo': 'Carta de no cargo público',
                'descripcion': 'Documentación de carta de no cargo público',
                'tipo_area': 'mixto',
                'orden': 29,
                'obligatoria': True
            },
            {
                'nombre': 'carta_compromiso',
                'titulo': 'Carta compromiso',
                'descripcion': 'Documentación de carta compromiso',
                'tipo_area': 'mixto',
                'orden': 30,
                'obligatoria': True
            },
            {
                'nombre': 'curriculum_empresarial',
                'titulo': 'Currículum empresarial',
                'descripcion': 'Documentación de currículum empresarial',
                'tipo_area': 'mixto',
                'orden': 31,
                'obligatoria': True
            },
            # Documentos de pago y entrega
            {
                'nombre': 'solicitud_pago_adj',
                'titulo': 'Solicitud de pago',
                'descripcion': 'Documentación de solicitud de pago',
                'tipo_area': 'mixto',
                'orden': 32,
                'obligatoria': True
            },
            {
                'nombre': 'factura_xml_adj',
                'titulo': 'Factura, XML y validación',
                'descripcion': 'Documentación de factura, XML y validación',
                'tipo_area': 'mixto',
                'orden': 33,
                'obligatoria': True
            },
            {
                'nombre': 'orden_compra_adj',
                'titulo': 'Orden de compra',
                'descripcion': 'Documentación de orden de compra',
                'tipo_area': 'mixto',
                'orden': 34,
                'obligatoria': True
            },
            {
                'nombre': 'vale_entrada_adj',
                'titulo': 'Vale de entrada',
                'descripcion': 'Documentación de vale de entrada',
                'tipo_area': 'mixto',
                'orden': 35,
                'obligatoria': True
            },
            {
                'nombre': 'acta_entrega_ine_adj',
                'titulo': 'Acta de entrega con INE de proveedor y persona que recibe',
                'descripcion': 'Documentación de acta de entrega con INE de proveedor y persona que recibe',
                'tipo_area': 'mixto',
                'orden': 36,
                'obligatoria': True
            },
            {
                'nombre': 'acta_entrega_proveedor_adj',
                'titulo': 'Acta de entrega de proveedor',
                'descripcion': 'Documentación de acta de entrega de proveedor',
                'tipo_area': 'mixto',
                'orden': 37,
                'obligatoria': True
            },
            {
                'nombre': 'oficio_conformidad_adj',
                'titulo': 'Oficio de conformidad y evidencia fotográfica',
                'descripcion': 'Documentación de oficio de conformidad y evidencia fotográfica',
                'tipo_area': 'mixto',
                'orden': 38,
                'obligatoria': True
            },
            {
                'nombre': 'anexos_adjudicacion',
                'titulo': 'Anexos de adjudicación',
                'descripcion': 'Documentación de anexos de adjudicación',
                'tipo_area': 'mixto',
                'orden': 39,
                'obligatoria': True
            }
        ]
    }
    
    # Mapeo de tipos de expediente a sus subtipos
    tipo_a_subtipo = {
        'licitacion': ['licitacion_recurso_propio', 'licitacion_fondo_federal'],
        'concurso_invitacion': ['concurso_invitacion'],
        'compra_directa': ['compra_directa'],
        'adjudicacion_directa': ['adjudicacion_directa']
    }
    
    # Crear las áreas para cada tipo y subtipo de expediente
    with transaction.atomic():
        for tipo_expediente, subtipos in tipo_a_subtipo.items():
            for subtipo in subtipos:
                if subtipo in areas_config:
                    print(f"\nCreando áreas para: {tipo_expediente} - {subtipo}")
                    
                    for area_data in areas_config[subtipo]:
                        # Determinar si el área es para un subtipo específico o genérico
                        es_especifico = '_' in subtipo  # Si tiene _ es un subtipo específico
                        
                        # Crear el área
                        area, created = AreaTipoExpediente.objects.update_or_create(
                            nombre=area_data['nombre'],
                            tipo_expediente=tipo_expediente,
                            subtipo_expediente=subtipo if es_especifico else None,
                            defaults={
                                'titulo': area_data['titulo'],
                                'descripcion': area_data['descripcion'],
                                'tipo_area': area_data['tipo_area'],
                                'orden': area_data['orden'],
                                'obligatoria': area_data['obligatoria'],
                                'es_default': True,
                                'activa': True,
                                'creada_por': admin_user
                            }
                        )
                        
                        status = "Creada" if created else "Actualizada"
                        subtipo_text = f" ({subtipo})" if es_especifico else ""
                        print(f"  - {status}: {area.titulo}{subtipo_text}")
    
    print("\n¡Proceso de creación de áreas completado con éxito!")

if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURACIÓN DE ÁREAS PARA TIPOS DE EXPEDIENTE")
    print("=" * 70)
    print("\nEste script creará o actualizará las áreas por defecto para cada tipo de expediente.")
    print("Las áreas existentes con los mismos nombres serán actualizadas.")
    
    confirmacion = input("\n¿Desea continuar? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        print("\nIniciando proceso de configuración...\n")
        crear_areas_por_defecto()
        print("\n¡Proceso completado con éxito!")
    else:
        print("\nOperación cancelada. No se realizaron cambios.")
        sys.exit(0)
