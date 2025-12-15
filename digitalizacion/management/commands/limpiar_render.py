"""
Comando Django para eliminar archivos antiguos de Render.
Mantiene el espacio de MEDIA_ROOT dentro de límites razonables.
"""

import os
import time
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Configuración (se puede cambiar)
TIEMPO_MAX_HORAS = 24  # Eliminar archivos más antiguos que 24 horas
TAM_MAX_MB = 100  # Máximo 100 MB en MEDIA_ROOT (ajusta según tu plan de Render)


class Command(BaseCommand):
    help = 'Elimina archivos antiguos de MEDIA_ROOT en Render para liberar espacio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--horas',
            type=int,
            default=TIEMPO_MAX_HORAS,
            help=f'Tiempo máximo en horas antes de eliminar archivos (default: {TIEMPO_MAX_HORAS})'
        )
        parser.add_argument(
            '--tamano-max',
            type=int,
            default=TAM_MAX_MB,
            help=f'Tamaño máximo en MB para MEDIA_ROOT (default: {TAM_MAX_MB})'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué archivos se eliminarían sin eliminarlos realmente'
        )

    def handle(self, *args, **options):
        horas_max = options['horas']
        tamano_max_mb = options['tamano_max']
        dry_run = options['dry_run']
        
        tiempo_max_segundos = horas_max * 3600
        tamano_max_bytes = tamano_max_mb * 1024 * 1024
        
        media_root = Path(settings.MEDIA_ROOT)
        
        if not media_root.exists():
            self.stdout.write(self.style.WARNING(f'MEDIA_ROOT no existe: {media_root}'))
            return
        
        self.stdout.write(f'Limpiando archivos en: {media_root}')
        self.stdout.write(f'Tiempo máximo: {horas_max} horas')
        self.stdout.write(f'Tamaño máximo: {tamano_max_mb} MB')
        self.stdout.write('-' * 50)
        
        # Obtener todos los archivos con su información
        archivos_info = []
        tamano_total = 0
        
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = Path(root) / file
                try:
                    stat_info = file_path.stat()
                    tamano = stat_info.st_size
                    mtime = stat_info.st_mtime
                    edad_segundos = time.time() - mtime
                    
                    archivos_info.append({
                        'path': file_path,
                        'tamano': tamano,
                        'mtime': mtime,
                        'edad_segundos': edad_segundos,
                        'edad_horas': edad_segundos / 3600
                    })
                    tamano_total += tamano
                except Exception as e:
                    logger.warning(f"Error al obtener info de {file_path}: {e}")
        
        tamano_total_mb = tamano_total / (1024 * 1024)
        self.stdout.write(f'Tamaño total actual: {tamano_total_mb:.2f} MB')
        self.stdout.write(f'Total de archivos: {len(archivos_info)}')
        self.stdout.write('-' * 50)
        
        # Ordenar por antigüedad (más antiguos primero)
        archivos_info.sort(key=lambda x: x['mtime'])
        
        archivos_eliminados = []
        tamano_eliminado = 0
        
        # 1. Eliminar archivos más antiguos que el tiempo máximo
        for archivo in archivos_info:
            if archivo['edad_segundos'] > tiempo_max_segundos:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Se eliminaría: {archivo['path'].name} "
                            f"({archivo['edad_horas']:.1f} horas, {archivo['tamano'] / 1024:.1f} KB)"
                        )
                    )
                else:
                    try:
                        archivo['path'].unlink()
                        archivos_eliminados.append(archivo)
                        tamano_eliminado += archivo['tamano']
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Eliminado: {archivo['path'].name} "
                                f"({archivo['edad_horas']:.1f} horas)"
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error al eliminar {archivo['path']}: {e}")
                        )
        
        # 2. Si aún supera el tamaño máximo, eliminar archivos más antiguos
        tamano_restante = tamano_total - tamano_eliminado
        
        if tamano_restante > tamano_max_bytes:
            self.stdout.write(
                self.style.WARNING(
                    f'\nTamaño restante ({tamano_restante / (1024*1024):.2f} MB) '
                    f'supera el máximo ({tamano_max_mb} MB)'
                )
            )
            self.stdout.write('Eliminando archivos más antiguos hasta alcanzar el límite...')
            
            # Filtrar archivos que no fueron eliminados
            archivos_restantes = [
                a for a in archivos_info
                if a not in archivos_eliminados
            ]
            archivos_restantes.sort(key=lambda x: x['mtime'])
            
            for archivo in archivos_restantes:
                if tamano_restante <= tamano_max_bytes:
                    break
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Se eliminaría por tamaño: {archivo['path'].name} "
                            f"({archivo['tamano'] / 1024:.1f} KB)"
                        )
                    )
                else:
                    try:
                        archivo['path'].unlink()
                        archivos_eliminados.append(archivo)
                        tamano_eliminado += archivo['tamano']
                        tamano_restante -= archivo['tamano']
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Eliminado por tamaño: {archivo['path'].name}"
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error al eliminar {archivo['path']}: {e}")
                        )
        
        # Resumen
        self.stdout.write('-' * 50)
        tamano_eliminado_mb = tamano_eliminado / (1024 * 1024)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Se eliminarían {len(archivos_eliminados)} archivos "
                    f"({tamano_eliminado_mb:.2f} MB)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Eliminados {len(archivos_eliminados)} archivos '
                    f'({tamano_eliminado_mb:.2f} MB)'
                )
            )
            tamano_final_mb = (tamano_total - tamano_eliminado) / (1024 * 1024)
            self.stdout.write(f'Tamaño final: {tamano_final_mb:.2f} MB')

