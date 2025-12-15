import re
import os

def update_views_expedientes():
    # Ruta al archivo original
    file_path = os.path.join(os.path.dirname(__file__), 'views_expedientes.py')
    
    # Leer el contenido actual
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Añadir la función get_demo_user si no existe
    if 'def get_demo_user(' not in content:
        # Buscar la primera importación para insertar después
        import_match = re.search(r'^from\s+django\..*?import', content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            content = (
                content[:insert_pos] + 
                'from django.contrib.auth import get_user_model\n\n' +
                'def get_demo_user():\n' +
                '    """Obtener o crear un usuario demo para operaciones sin autenticación"""\n' +
                '    User = get_user_model()\n' +
                '    return User.objects.get_or_create(\n' +
                '        username=\'usuario_demo\',\n' +
                '        defaults={\'is_active\': False, \'is_staff\': False, \'is_superuser\': False}\n' +
                '    )[0]\n\n' +
                content[insert_pos:]
            )
    
    # Actualizar la función subir_documento_temporal
    pattern = r'@login_required\s+def subir_documento_temporal\(request, expediente_id\):.*?return JsonResponse\(\{\'success\': False, \'error\': str\(e\)\}, status=500\)\s+'
    replacement = (
        '@login_required\ndef subir_documento_temporal(request, expediente_id):\n    """\n    Vista temporal para manejar la subida de documentos sin la etapa en la URL.\n    Obtiene la etapa directamente del formulario.\n    """\n    try:\n        if request.method == \'POST\':\n            # Obtener la etapa directamente del formulario\n            etapa = request.POST.get(\'etapa\')\n            if not etapa:\n                return JsonResponse({\'success\': False, \'error\': \'No se especificó la etapa del documento\'}, status=400)\n                \n            # Llamar a la vista principal de subida de documentos con la etapa\n            return subir_documento(request, expediente_id, etapa)\n    \n    except Exception as e:\n        import logging\n        logger = logging.getLogger(__name__)\n        logger.error(f\'Error en subir_documento_temporal: {str(e)}\')\n        return JsonResponse({\'success\': False, \'error\': \'Error al procesar la solicitud\'}, status=500)\n\n'
    )
    
    content = re.sub(
        pattern=pattern,
        repl=replacement,
        string=content,
        flags=re.DOTALL
    )
    
    # Añadir la función subir_documento si no existe
    if 'def subir_documento(' not in content:
        # Buscar un buen lugar para insertar (después de la última función)
        func_matches = list(re.finditer(r'^@login_required\s+def\s+\w+', content, re.MULTILINE))
        if func_matches:
            last_func = func_matches[-1]
            insert_pos = content.find('\n', last_func.end()) + 1
            
            subir_doc_func = (
                '\n@login_required\n' +
                'def subir_documento(request, expediente_id, etapa):\n' +
                '    """Vista para subir documentos a una etapa específica"""\n' +
                '    from django.core.cache import cache\n' +
                '    \n' +
                '    expediente = get_object_or_404(Expediente, pk=expediente_id)\n' +
                '    \n' +
                '    if request.method == \'POST\':\n' +
                '        archivo = request.FILES.get(\'archivo\')\n' +
                '        nombre_documento = request.POST.get(\'nombre_documento\')\n' +
                '        descripcion = request.POST.get(\'descripcion\', \'\')\n' +
                '        \n' +
                '        if archivo and nombre_documento:\n' +
                '            # Obtener usuario (autenticado o demo)\n' +
                '            usuario = request.user if request.user.is_authenticated else get_demo_user()\n' +
                '            \n' +
                '            # Crear el documento\n' +
                '            DocumentoExpediente.objects.create(\n' +
                '                expediente=expediente,\n' +
                '                etapa=etapa,\n' +
                '                nombre_documento=nombre_documento,\n' +
                '                archivo=archivo,\n' +
                '                descripcion=descripcion,\n' +
                '                subido_por=usuario\n' +
                '            )\n' +
                '            \n' +
                '            # Limpiar la caché de última actualización\n' +
                '            cache_key = f\'expediente_{expediente.id}_ultima_actualizacion\'\n' +
                '            cache.delete(cache_key)\n' +
                '            \n' +
                '            # Actualizar manualmente la fecha de actualización del expediente\n' +
                '            ahora = timezone.now()\n' +
                '            expediente.fecha_actualizacion = ahora\n' +
                '            expediente.save(update_fields=[\'fecha_actualizacion\'])\n' +
                '            \n' +
                '            # Crear entrada en el historial\n' +
                '            HistorialExpediente.objects.create(\n' +
                '                expediente=expediente,\n' +
                '                usuario=usuario,\n' +
                '                accion=\'Documento subido\',\n' +
                '                descripcion=f\'Documento \"{nombre_documento}\" subido en etapa {etapa}\',\n' +
                '                etapa_nueva=etapa\n' +
                '            )\n' +
                '            \n' +
                '            return JsonResponse({\n' +
                '                \'success\': True,\n' +
                '                \'message\': \'Documento subido exitosamente\',\n' +
                '                \'documento\': {\n' +
                '                    \'nombre\': nombre_documento,\n' +
                '                    \'fecha\': ahora.strftime(\'%d/%m/%Y %H:%M\'),\n' +
                '                    \'usuario\': usuario.get_full_name() or usuario.username\n' +
                '                }\n' +
                '            })\n' +
                '        else:\n' +
                '            return JsonResponse({\n' +
                '                \'success\': False,\n' +
                '                \'error\': \'Faltan campos requeridos: archivo y nombre_documento son obligatorios\'\n' +
                '            }, status=400)\n' +
                '    \n' +
                '    return JsonResponse({\'success\': False, \'error\': \'Método no permitido\'}, status=405)\n\n'
            )
            
            content = content[:insert_pos] + subir_doc_func + content[insert_pos:]
    
    # Escribir los cambios
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_views_expedientes()
