from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from digitalizacion.models import AreaTipoExpediente, Expediente


class Command(BaseCommand):
    help = 'Normaliza el orden de las áreas para que sean consecutivas (1, 2, 3, 4, 5...)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            help='Tipo de expediente específico a normalizar (opcional)',
        )
        parser.add_argument(
            '--subtipo',
            type=str,
            help='Subtipo específico a normalizar (opcional, solo para licitación)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin hacer cambios',
        )

    def handle(self, *args, **options):
        tipo = options.get('tipo')
        subtipo = options.get('subtipo')
        dry_run = options.get('dry_run', False)

        if tipo:
            tipos_a_procesar = [tipo]
        else:
            tipos_a_procesar = [t[0] for t in Expediente.TIPO_CHOICES]

        total_normalizadas = 0

        for tipo_exp in tipos_a_procesar:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Procesando tipo: {tipo_exp}')
            self.stdout.write(f'{"="*60}')

            if tipo_exp == 'licitacion':
                # Para licitación, procesar cada subtipo
                if subtipo:
                    subtipos_a_procesar = [subtipo]
                else:
                    subtipos_a_procesar = [s[0] for s in Expediente.SUBTIPO_LICITACION_CHOICES]

                for subtipo_exp in subtipos_a_procesar:
                    self._normalizar_subtipo(tipo_exp, subtipo_exp, dry_run)
                    total_normalizadas += self._contar_areas(tipo_exp, subtipo_exp)

                # También normalizar áreas genéricas (sin subtipo)
                self._normalizar_subtipo(tipo_exp, None, dry_run)
                total_normalizadas += self._contar_areas(tipo_exp, None)
            else:
                # Para otros tipos, solo áreas genéricas
                self._normalizar_subtipo(tipo_exp, None, dry_run)
                total_normalizadas += self._contar_areas(tipo_exp, None)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Normalización completada. Total de áreas procesadas: {total_normalizadas}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ Modo dry-run: No se realizaron cambios. Total de áreas que se normalizarían: {total_normalizadas}'
            ))

    def _normalizar_subtipo(self, tipo_exp, subtipo_exp, dry_run):
        """Normaliza el orden de las áreas para un tipo y subtipo específico"""
        # Obtener áreas según tipo y subtipo
        if tipo_exp == 'licitacion' and subtipo_exp:
            # Buscar áreas con ambos formatos posibles
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_exp,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_exp) | Q(subtipo_expediente=f'licitacion_{subtipo_exp}')
            ).order_by('orden', 'titulo')
            subtipo_label = subtipo_exp
        else:
            # Áreas genéricas (sin subtipo)
            areas = AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_exp,
                activa=True
            ).filter(
                Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
            ).order_by('orden', 'titulo')
            subtipo_label = 'genérico'

        areas_list = list(areas)
        if not areas_list:
            self.stdout.write(f'  No hay áreas para {tipo_exp} - {subtipo_label}')
            return

        self.stdout.write(f'\n  Normalizando {len(areas_list)} áreas para {tipo_exp} - {subtipo_label}')

        # Normalizar el orden
        areas_to_update = []
        cambios = []

        for index, area in enumerate(areas_list, start=1):
            orden_anterior = area.orden
            if area.orden != index:
                area.orden = index
                areas_to_update.append(area)
                cambios.append((area.id, area.titulo[:50], orden_anterior, index))

        if cambios:
            if dry_run:
                self.stdout.write(f'  Se normalizarían {len(cambios)} áreas:')
                for area_id, titulo, orden_ant, orden_nuevo in cambios:
                    self.stdout.write(
                        f'    - ID {area_id}: "{titulo}" - Orden {orden_ant} → {orden_nuevo}'
                    )
            else:
                with transaction.atomic():
                    AreaTipoExpediente.objects.bulk_update(areas_to_update, ['orden'])
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Normalizadas {len(cambios)} áreas'
                ))
                for area_id, titulo, orden_ant, orden_nuevo in cambios:
                    self.stdout.write(
                        f'    - ID {area_id}: "{titulo}" - Orden {orden_ant} → {orden_nuevo}'
                    )
        else:
            self.stdout.write(f'  ✓ Todas las áreas ya tienen orden consecutivo')

    def _contar_areas(self, tipo_exp, subtipo_exp):
        """Cuenta las áreas para un tipo y subtipo específico"""
        if tipo_exp == 'licitacion' and subtipo_exp:
            return AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_exp,
                activa=True
            ).filter(
                Q(subtipo_expediente=subtipo_exp) | Q(subtipo_expediente=f'licitacion_{subtipo_exp}')
            ).count()
        else:
            return AreaTipoExpediente.objects.filter(
                tipo_expediente=tipo_exp,
                activa=True
            ).filter(
                Q(subtipo_expediente__isnull=True) | Q(subtipo_expediente='')
            ).count()

