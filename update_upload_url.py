file_path = r'c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\sistema_digitalizacion\digitalizacion_2\templates\digitalizacion\expedientes\detalle_expediente.html'

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Definir el patrón a buscar y el reemplazo
pattern = r'// Enviar archivo\n\s+const response = await fetch\(`/expedientes/\{\{ expediente\.id \}\}/subir-documento/`,\s*\{\s*method: \'POST\',\s*headers: \{\s*\'X-Requested-With\': \'XMLHttpRequest\',\s*\'X-CSRFToken\': csrftoken\s*\},\s*body: formData\s*\}\);'

replacement = '''// Obtener la etapa del área actual
                const areaElement = document.querySelector(`[data-area-id="${areaActual}"]`);
                const etapa = areaElement ? areaElement.dataset.etapa : '';
                
                // Construir la URL con la etapa
                const url = etapa 
                    ? `/expedientes/{{ expediente.id }}/etapa/${etapa}/subir-documento/`
                    : `/expedientes/{{ expediente.id }}/subir-documento/`;
                
                console.log('Enviando documento a:', url);
                
                // Enviar archivo
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    },
                    body: formData
                });'''

# Realizar el reemplazo
import re
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Escribir el archivo actualizado
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print("Archivo actualizado exitosamente.")
