from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Min
from digitalizacion.models import AreaTipoExpediente

class Command(BaseCommand):
    help = 'Elimina áreas duplicadas y asegura que solo existan las áreas correctas para cada tipo de expediente'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando limpieza de áreas duplicadas...")
        
        # Definir las áreas correctas para cada tipo de expediente
        areas_correctas = {
            'licitacion': [
                'solicitud_aprobacion_fondo',
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'estudio_mercado',
                'requisicion',
                'cotizacion',
                'invitacion_licitacion',
                'acta_junta_aclaraciones',
                'acta_recepcion_propuestas',
                'dictamen_cuadro_comparativo',
                'acta_elaboracion_fallo',
                'acta_lectura_fallo',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad_evidencia',
            ],
            'concurso_invitacion': [
                'solicitud_aprobacion_fondo',
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'estudio_mercado',
                'requisicion',
                'cotizacion',
                'invitacion_particulares',
                'acta_junta_aclaraciones',
                'acta_apertura_propuestas',
                'dictamen_cuadro_comparativo',
                'acta_elaboracion_fallo',
                'acta_lectura_fallo',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad_evidencia',
            ],
            'compra_directa': [
                'solicitud_aprobacion_fondo',
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'estudio_mercado',
                'requisicion',
                'cotizacion',
                'dictamen_justificacion',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad_evidencia',
            ],
            'adjudicacion_directa': [
                'solicitud_aprobacion_fondo',
                'oficio_control_patrimonial',
                'solicitud_requisicion',
                'estudio_mercado',
                'requisicion',
                'cotizacion',
                'dictamen_justificacion',
                'contrato',
                'solicitud_pago',
                'factura_xml_validacion',
                'orden_compra',
                'vale_entrada',
                'acta_entrega_ine',
                'acta_entrega_proveedor',
                'oficio_conformidad_evidencia',
            ]
        }

        with transaction.atomic():
            # Primero, marcar las áreas correctas
            for tipo_expediente, areas in areas_correctas.items():
                # Para cada área correcta, marcar como activa y actualizar
                for nombre_area in areas:
                    # Actualizar o crear el área correcta
                    AreaTipoExpediente.objects.update_or_create(
                        nombre=nombre_area,
                        tipo_expediente=tipo_expediente,
                        defaults={
                            'activa': True,
                            'es_default': True
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Área configurada: {tipo_expediente} - {nombre_area}'))
            
            # Marcar como inactivas las áreas que no están en la lista de correctas
            for area in AreaTipoExpediente.objects.all():
                if area.nombre not in areas_correctas.get(area.tipo_expediente, []):
                    area.activa = False
                    area.save()
                    self.stdout.write(self.style.WARNING(f'Área desactivada: {area.tipo_expediente} - {area.nombre}'))
            
            # Encontrar duplicados
            duplicates = AreaTipoExpediente.objects.values(
                'nombre', 'tipo_expediente'
            ).annotate(
                min_id=Min('id'),
                count_models=Count('id')
            ).filter(count_models__gt=1)

            for duplicate in duplicates:
                # Mantener el registro más antiguo
                AreaTipoExpediente.objects.filter(
                    nombre=duplicate['nombre'],
                    tipo_expediente=duplicate['tipo_expediente']
                ).exclude(
                    id=duplicate['min_id']
                ).delete()
                self.stdout.write(self.style.SUCCESS(f'Eliminados duplicados de: {duplicate["tipo_expediente"]} - {duplicate["nombre"]}'))

        self.stdout.write(self.style.SUCCESS('Limpieza de áreas completada exitosamente!'))

# No se necesita esta línea ya que importamos Count al inicio
