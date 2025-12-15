import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

from django.contrib.auth.models import User
from digitalizacion.models import AreaTipoExpediente

def crear_areas_por_tipo():
    """Crea las áreas para cada tipo de expediente según la estructura proporcionada"""
    # Obtener o crear un usuario administrador
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Mapeo de tipos de expediente
    TIPOS_EXPEDIENTE = [
        {
            'codigo': 'licitacion_recurso_propio',
            'nombre': 'LICITACIÓN (RECURSO PROPIO)',
            'areas': [
                'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'Solicitud de requisición del área',
                'Requisición',
                'Cotización',
                'Invitación a licitación',
                'Acta de junta de aclaraciones',
                'Acta de recepción de propuestas técnicas',
                'Dictamen y comparativo comparativo',
                'Acta de elaboración del fallo',
                'Acta de lectura de fallo',
                'Contrato',
                'Solicitud de pago',
                'Factura, XML y validación',
                'Orden de compra',
                'Vale de entrada',
                'Oficio de conformidad y evidencia fotográfica',
                'Anexos de licitación'
            ]
        },
        {
            'codigo': 'licitacion_fondo_federal',
            'nombre': 'LICITACIÓN (FONDO FEDERAL)',
            'areas': [
                'Solicitud y aprobación de fondo',
                'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'Solicitud de requisición del área',
                'Estudio de mercado',
                'Requisición',
                'Cotización',
                'Invitación a licitación',
                'Acta de junta de aclaraciones',
                'Acta de recepción de propuestas técnicas',
                'Dictamen y cuadro comparativo',
                'Acta de elaboración del fallo',
                'Acta de lectura de fallo',
                'Contrato',
                'Solicitud de pago',
                'Factura, XML y validación',
                'Orden de compra',
                'Vale de entrada',
                'Acta de entrega con INE de proveedor y persona que recibe',
                'Acta de entrega de proveedor',
                'Oficio de conformidad y evidencia fotográfica',
                'Anexos de licitación'
            ]
        },
        {
            'codigo': 'concurso_invitacion',
            'nombre': 'CONCURSO POR INVITACIÓN',
            'areas': [
                'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'Solicitud de requisición del área',
                'Requisición',
                'Cotización',
                'Invitación a licitación',
                'Acta de junta de aclaraciones',
                'Acta de recepción de propuestas técnicas',
                'Dictamen y cuadro comparativo',
                'Acta de elaboración del fallo',
                'Acta de lectura de fallo',
                'Contrato',
                'Solicitud de pago',
                'Factura, XML y validación',
                'Orden de compra',
                'Vale de entrada',
                'Oficio de conformidad y evidencia fotográfica',
                'Anexos de licitación'
            ]
        },
        {
            'codigo': 'compra_directa',
            'nombre': 'COMPRA DIRECTA',
            'areas': [
                'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'Solicitud de requisición del área',
                'Requisición',
                'Cotización',
                'Solicitud de pago',
                'Factura, XML y validación',
                'Orden de compra',
                'Vale de entrada',
                'Oficio de conformidad y evidencia fotográfica'
            ]
        },
        {
            'codigo': 'adjudicacion_directa',
            'nombre': 'ADJUDICACIÓN DIRECTA',
            'areas': [
                'Solicitud de suficiencia presupuestal y autorización de compromiso de pago',
                'Solicitud y contestación de compromiso de pago',
                'Oficio y contestación de control patrimonial, TIC´s o capital humano',
                'Solicitud de avaluo en caso de ser renta de algún vehículo',
                'Solicitud de requisición del área',
                'Análisis costo beneficio',
                'Requisición',
                'Cotización',
                '3 o más cotizaciones',
                'Avalúo en caso de ser requerido',
                'En caso de ser vehículos: facturas, seguro, chofer responsable',
                'Invitación al comité de adquisiciones',
                'Solicitud y dictamen de la adjudicación',
                'Acta de sesión de comité',
                'Contrato',
                'Constancia de proveedor',
                'Constancia de situación fiscal',
                'Comprobante de domicilio fiscal',
                'Apertura de establecimiento (si aplica)',
                'Comprobante de domicilio de establecimiento comercial (si aplica)',
                'Opion de cumplimiento de SAT positiva',
                'Opion de cumplimiento de IMSS',
                'Opion de cumplimiento de INFONAVIT',
                'Opion de cumplimiento finanzas del estado',
                'Acta constitutiva (personas morales)',
                'Poder notarial (en caso de aplicar)',
                'Copia INE',
                'Carta de no sanción',
                'Carta de no cargo público',
                'Carta compromiso',
                'Currículum empresarial',
                'Solicitud de pago',
                'Factura, XML y validación',
                'Orden de compra',
                'Vale de entrada',
                'Acta de entrega con INE de proveedor y persona que recibe',
                'Acta de entrega de proveedor',
                'Oficio de conformidad y evidencia fotográfica',
                'Anexos de adjudicación'
            ]
        }
    ]

    # Crear las áreas para cada tipo de expediente
    for tipo in TIPOS_EXPEDIENTE:
        print(f"\nConfigurando áreas para: {tipo['nombre']}")
        
        # Crear cada área para este tipo de expediente
        for orden, nombre_area in enumerate(tipo['areas'], 1):
            # Crear un nombre interno único (sin espacios, en minúsculas)
            nombre_interno = f"{tipo['codigo']}_{nombre_area.lower().replace(' ', '_').replace(',', '').replace('´', '').replace(')', '').replace('(', '')}"
            
            # Crear o actualizar el área
            area, created = AreaTipoExpediente.objects.update_or_create(
                nombre=nombre_interno[:100],  # Asegurar que no exceda el límite de caracteres
                defaults={
                    'titulo': nombre_area,
                    'descripcion': f"Área para {nombre_area} en {tipo['nombre']}",
                    'tipo_expediente': tipo['codigo'],
                    'tipo_area': 'mixto',  # Por defecto tipo mixto (permite texto y archivos)
                    'orden': orden,
                    'obligatoria': False,  # Según lo indicado, ninguna es obligatoria
                    'es_default': True,
                    'creada_por': admin_user
                }
            )
            
            if created:
                print(f"  - Creada: {nombre_area}")
            else:
                print(f"  - Actualizada: {nombre_area}")
    
    print("\n¡Configuración de áreas completada exitosamente!")

if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURACIÓN DE ÁREAS PARA TIPOS DE EXPEDIENTE")
    print("=" * 70)
    print("Este script configurará las áreas para cada tipo de expediente.")
    print("Se crearán o actualizarán las áreas según sea necesario.\n")
    
    confirmacion = input("¿Desea continuar? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        crear_areas_por_tipo()
    else:
        print("\nOperación cancelada. No se realizaron cambios.")
