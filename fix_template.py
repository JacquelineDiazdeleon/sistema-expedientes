# Ruta al archivo de plantilla
template_path = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templates\digitalizacion\expedientes\detalle_expediente.html"

# Leer el contenido actual del archivo
with open(template_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Definir el bloque a buscar y su reemplazo
old_block = '''                                    <div class="p-3 bg-light rounded">
                                        {% with valor=valores_areas|get_item:area.id %}
                                            {% if valor and valor.valor_texto %}
                                                {{ valor.valor_texto|linebreaks }}
                                            {% else %}
                                                <p class="text-muted">No hay contenido de texto disponible.</p>
                                            {% endif %}
                                        {% endwith %}
                                    </div>'''

new_block = '''                                    <div class="p-3 bg-light rounded">
                                        {% if valores_areas %}
                                            {% with valor=valores_areas|get_item:area.id %}
                                                {% if valor and valor.valor_texto %}
                                                    {{ valor.valor_texto|linebreaks }}
                                                {% else %}
                                                    <p class="text-muted">No hay contenido de texto disponible.</p>
                                                {% endif %}
                                            {% endwith %}
                                        {% else %}
                                            <p class="text-muted">No hay contenido de texto disponible.</p>
                                        {% endif %}
                                    </div>'''

# Reemplazar el bloque
if old_block in content:
    content = content.replace(old_block, new_block)
    # Escribir el contenido actualizado
    with open(template_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print("Plantilla actualizada correctamente.")
else:
    print("No se encontró el bloque a reemplazar en la plantilla.")
    print("El archivo podría tener un formato diferente al esperado.")
