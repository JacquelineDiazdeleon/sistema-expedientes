from django.core.management.base import BaseCommand
from django.db import connection
from digitalizacion.models import Expediente, DocumentoExpediente, EtapaExpediente


class Command(BaseCommand):
    help = 'Diagnostica expedientes específicos que pueden estar causando problemas'

    def add_arguments(self, parser):
        parser.add_argument('--expediente-id', type=int, help='ID específico del expediente a diagnosticar')
        parser.add_argument('--todos', action='store_true', help='Diagnosticar todos los expedientes')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Iniciando diagnóstico de expedientes problemáticos...'))
        
        if options['expediente_id']:
            # Diagnosticar un expediente específico
            expedientes = Expediente.objects.filter(id=options['expediente_id'])
        elif options['todos']:
            # Diagnosticar todos los expedientes
            expedientes = Expediente.objects.all()
        else:
            # Diagnosticar solo los últimos 10 expedientes
            expedientes = Expediente.objects.order_by('-id')[:10]
        
        for expediente in expedientes:
            self.stdout.write(f'\n📋 Expediente ID: {expediente.id}')
            self.stdout.write(f'   Número: {expediente.numero_expediente}')
            self.stdout.write(f'   Título: {expediente.titulo}')
            self.stdout.write(f'   Tipo: {expediente.tipo_expediente}')
            self.stdout.write(f'   Subtipo: {expediente.subtipo_expediente}')
            self.stdout.write(f'   Estado: {expediente.estado_actual}')
            
            # Verificar documentos
            documentos = DocumentoExpediente.objects.filter(expediente=expediente)
            self.stdout.write(f'   📄 Documentos: {documentos.count()}')
            
            # Verificar etapas
            etapas = EtapaExpediente.objects.filter(expediente=expediente)
            self.stdout.write(f'   🎯 Etapas: {etapas.count()}')
            
            # Verificar relaciones problemáticas
            try:
                # Verificar departamento
                if expediente.departamento:
                    self.stdout.write(f'   🏢 Departamento: {expediente.departamento.nombre} ✅')
                else:
                    self.stdout.write(f'   🏢 Departamento: NO ASIGNADO ❌')
                
                # Verificar usuario creador
                if expediente.creado_por:
                    self.stdout.write(f'   👤 Creado por: {expediente.creado_por.get_full_name()} ✅')
                else:
                    self.stdout.write(f'   👤 Creado por: NO ASIGNADO ❌')
                
                # Verificar si hay campos nulos problemáticos
                campos_problematicos = []
                if not expediente.titulo:
                    campos_problematicos.append('titulo')
                if not expediente.tipo_expediente:
                    campos_problematicos.append('tipo_expediente')
                if not expediente.estado_actual:
                    campos_problematicos.append('estado_actual')
                
                if campos_problematicos:
                    self.stdout.write(f'   ⚠️  Campos problemáticos: {", ".join(campos_problematicos)}')
                else:
                    self.stdout.write(f'   ✅ Campos básicos: OK')
                
                # Verificar documentos problemáticos
                docs_problematicos = []
                for doc in documentos[:5]:  # Solo los primeros 5
                    try:
                        if doc.archivo and not doc.archivo.storage.exists(doc.archivo.name):
                            docs_problematicos.append(f'Doc {doc.id}: archivo no existe')
                    except Exception as e:
                        docs_problematicos.append(f'Doc {doc.id}: error - {e}')
                
                if docs_problematicos:
                    self.stdout.write(f'   ⚠️  Documentos problemáticos: {len(docs_problematicos)}')
                    for prob in docs_problematicos[:3]:  # Solo mostrar 3
                        self.stdout.write(f'      - {prob}')
                else:
                    self.stdout.write(f'   ✅ Documentos: OK')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error al diagnosticar: {e}'))
            
            # Verificar tamaño de datos
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_docs,
                            SUM(CASE WHEN archivo IS NOT NULL THEN 1 ELSE 0 END) as docs_con_archivo,
                            SUM(CASE WHEN archivo IS NULL THEN 1 ELSE 0 END) as docs_sin_archivo
                        FROM digitalizacion_documentoexpediente 
                        WHERE expediente_id = %s
                    """, [expediente.id])
                    
                    result = cursor.fetchone()
                    if result:
                        self.stdout.write(f'   📊 Estadísticas BD: {result[0]} docs total, {result[1]} con archivo, {result[2]} sin archivo')
            except Exception as e:
                self.stdout.write(f'   📊 Estadísticas BD: Error - {e}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Diagnóstico completado'))
        
        # Resumen de problemas comunes
        self.stdout.write(f'\n🔍 Resumen de problemas comunes:')
        self.stdout.write(f'   1. Expedientes sin departamento asignado')
        self.stdout.write(f'   2. Expedientes sin usuario creador')
        self.stdout.write(f'   3. Documentos con archivos faltantes')
        self.stdout.write(f'   4. Campos obligatorios nulos')
        self.stdout.write(f'   5. Relaciones rotas en la base de datos')
