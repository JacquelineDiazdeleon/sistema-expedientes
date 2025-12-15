import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.db import transaction
from digitalizacion.models import AreaTipoExpediente

def crear_area(nombre, titulo, tipo_expediente, subtipo_expediente=None, orden=0, tipo_area='mixto', obligatoria=True):
    """Crea o actualiza un área si no existe"""
    area, created = AreaTipoExpediente.objects.update_or_create(
        nombre=nombre,
        tipo_expediente=tipo_expediente,
        subtipo_expediente=subtipo_expediente,
        defaults={
            'titulo': titulo,
            'orden': orden,
            'tipo_area': tipo_area,
            'obligatoria': obligatoria,
            'activa': True,
            'es_default': True
        }
    )
    return area

def restaurar_areas_licitacion():
    """Restaura las áreas para licitaciones"""
    areas_licitacion = [
        # Áreas comunes para todos los subtipos de licitación
        ('solicitud_aprobacion_fondo', 'Solicitud de Aprobación de Fondo', 1),
        ('oficio_control_patrimonial', 'Oficio de Control Patrimonial', 2),
        ('solicitud_requisicion', 'Solicitud de Requisición', 3),
        ('estudio_mercado', 'Estudio de Mercado', 4),
        ('requisicion', 'Requisición', 5),
        ('cotizacion', 'Cotización', 6),
        
        # Áreas específicas por subtipo
        ('invitacion_licitacion', 'Invitación a Licitación', 7, 'licitacion_recurso_propio'),
        ('invitacion_licitacion', 'Invitación a Licitación', 7, 'licitacion_fondo_federal'),
        
        # Áreas comunes
        ('acta_junta_aclaraciones', 'Acta de Junta de Aclaraciones', 8),
        ('acta_recepcion_propuestas', 'Acta de Recepción de Propuestas', 9),
        ('dictamen_cuadro_comparativo', 'Dictamen de Cuadro Comparativo', 10),
        ('acta_elaboracion_fallo', 'Acta de Elaboración de Fallo', 11),
        ('acta_lectura_fallo', 'Acta de Lectura de Fallo', 12),
        ('contrato', 'Contrato', 13),
        ('solicitud_pago', 'Solicitud de Pago', 14),
        ('factura_xml_validacion', 'Factura XML y Validación', 15),
        ('orden_compra', 'Orden de Compra', 16),
        ('vale_entrada', 'Vale de Entrada', 17),
        ('acta_entrega_ine', 'Acta de Entrega INE', 18),
        ('acta_entrega_proveedor', 'Acta de Entrega al Proveedor', 19),
        ('oficio_conformidad_evidencia', 'Oficio de Conformidad y Evidencia', 20),
    ]
    
    for area_info in areas_licitacion:
        if len(area_info) == 3:
            nombre, titulo, orden = area_info
            subtipo = None
        else:
            nombre, titulo, orden, subtipo = area_info
            
        # Crear área para cada subtipo de licitación
        if subtipo is None:
            for subtipo_lic in ['licitacion_recurso_propio', 'licitacion_fondo_federal']:
                crear_area(nombre, titulo, 'licitacion', subtipo_lic, orden)
        else:
            crear_area(nombre, titulo, 'licitacion', subtipo, orden)

def restaurar_areas_concurso_invitacion():
    """Restaura las áreas para concurso por invitación"""
    areas_concurso = [
        ('solicitud_aprobacion_fondo', 'Solicitud de Aprobación de Fondo', 1),
        ('oficio_control_patrimonial', 'Oficio de Control Patrimonial', 2),
        ('solicitud_requisicion', 'Solicitud de Requisición', 3),
        ('estudio_mercado', 'Estudio de Mercado', 4),
        ('requisicion', 'Requisición', 5),
        ('cotizacion', 'Cotización', 6),
        ('invitacion_particulares', 'Invitación a Particulares', 7),
        ('acta_junta_aclaraciones', 'Acta de Junta de Aclaraciones', 8),
        ('acta_apertura_propuestas', 'Acta de Apertura de Propuestas', 9),
        ('dictamen_cuadro_comparativo', 'Dictamen de Cuadro Comparativo', 10),
        ('acta_elaboracion_fallo', 'Acta de Elaboración de Fallo', 11),
        ('acta_lectura_fallo', 'Acta de Lectura de Fallo', 12),
        ('contrato', 'Contrato', 13),
        ('solicitud_pago', 'Solicitud de Pago', 14),
        ('factura_xml_validacion', 'Factura XML y Validación', 15),
        ('orden_compra', 'Orden de Compra', 16),
        ('vale_entrada', 'Vale de Entrada', 17),
        ('acta_entrega_ine', 'Acta de Entrega INE', 18),
        ('acta_entrega_proveedor', 'Acta de Entrega al Proveedor', 19),
        ('oficio_conformidad_evidencia', 'Oficio de Conformidad y Evidencia', 20),
    ]
    
    for nombre, titulo, orden in areas_concurso:
        crear_area(nombre, titulo, 'concurso_invitacion', None, orden)

def restaurar_areas_compra_directa():
    """Restaura las áreas para compra directa"""
    areas_compra_directa = [
        ('solicitud_aprobacion_fondo', 'Solicitud de Aprobación de Fondo', 1),
        ('oficio_control_patrimonial', 'Oficio de Control Patrimonial', 2),
        ('solicitud_requisicion', 'Solicitud de Requisición', 3),
        ('estudio_mercado', 'Estudio de Mercado', 4),
        ('requisicion', 'Requisición', 5),
        ('cotizacion', 'Cotización', 6),
        ('dictamen_justificacion', 'Dictamen de Justificación', 7),
        ('contrato', 'Contrato', 8),
        ('solicitud_pago', 'Solicitud de Pago', 9),
        ('factura_xml_validacion', 'Factura XML y Validación', 10),
        ('orden_compra', 'Orden de Compra', 11),
        ('vale_entrada', 'Vale de Entrada', 12),
        ('acta_entrega_ine', 'Acta de Entrega INE', 13),
        ('acta_entrega_proveedor', 'Acta de Entrega al Proveedor', 14),
        ('oficio_conformidad_evidencia', 'Oficio de Conformidad y Evidencia', 15),
    ]
    
    for nombre, titulo, orden in areas_compra_directa:
        crear_area(nombre, titulo, 'compra_directa', None, orden)

def restaurar_areas_adjudicacion_directa():
    """Restaura las áreas para adjudicación directa"""
    areas_adjudicacion = [
        ('solicitud_aprobacion_fondo', 'Solicitud de Aprobación de Fondo', 1),
        ('oficio_control_patrimonial', 'Oficio de Control Patrimonial', 2),
        ('solicitud_requisicion', 'Solicitud de Requisición', 3),
        ('estudio_mercado', 'Estudio de Mercado', 4),
        ('requisicion', 'Requisición', 5),
        ('cotizacion', 'Cotización', 6),
        ('dictamen_justificacion', 'Dictamen de Justificación', 7),
        ('contrato', 'Contrato', 8),
        ('solicitud_pago', 'Solicitud de Pago', 9),
        ('factura_xml_validacion', 'Factura XML y Validación', 10),
        ('orden_compra', 'Orden de Compra', 11),
        ('vale_entrada', 'Vale de Entrada', 12),
        ('acta_entrega_ine', 'Acta de Entrega INE', 13),
        ('acta_entrega_proveedor', 'Acta de Entrega al Proveedor', 14),
        ('oficio_conformidad_evidencia', 'Oficio de Conformidad y Evidencia', 15),
    ]
    
    for nombre, titulo, orden in areas_adjudicacion:
        crear_area(nombre, titulo, 'adjudicacion_directa', None, orden)

def main():
    print("Iniciando restauración de áreas...")
    
    with transaction.atomic():
        # Primero, desactivar todas las áreas existentes
        AreaTipoExpediente.objects.all().update(activa=False)
        
        # Restaurar áreas para cada tipo de expediente
        restaurar_areas_licitacion()
        restaurar_areas_concurso_invitacion()
        restaurar_areas_compra_directa()
        restaurar_areas_adjudicacion_directa()
        
        # Contar áreas restauradas
        total_areas = AreaTipoExpediente.objects.filter(activa=True).count()
        
        print(f"\n¡Restauración completada!")
        print(f"Total de áreas activas: {total_areas}")
        print("\nTipos de expediente y sus áreas:")
        
        # Mostrar resumen
        for tipo in AreaTipoExpediente.objects.values_list('tipo_expediente', flat=True).distinct():
            print(f"\n--- {tipo.upper()} ---")
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo,
                activa=True
            ).order_by('orden')
            
            for area in areas:
                subtipo = f" ({area.subtipo_expediente})" if area.subtipo_expediente else ""
                print(f"  {area.orden:2d}. {area.titulo}{subtipo}")

if __name__ == "__main__":
    main()
