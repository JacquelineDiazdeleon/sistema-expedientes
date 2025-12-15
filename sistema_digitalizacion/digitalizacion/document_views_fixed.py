            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Documento subido exitosamente.',
                'documento': {
                    'id': documento.id,
                    'nombre': documento.nombre_documento,
                    'nombre_documento': documento.nombre_documento,  # Asegurar que el título esté en ambos campos
                    'fecha': ahora.strftime('%d/%m/%Y %H:%M'),
                    'usuario': request.user.get_full_name() or request.user.username,
                    'url': documento.archivo.url if documento.archivo else '',
                    'tamano': archivo.size,
                    'tipo': archivo.content_type,
                    'nombre_archivo': archivo.name  # Asegurar que el nombre del archivo esté disponible
                }
            })
