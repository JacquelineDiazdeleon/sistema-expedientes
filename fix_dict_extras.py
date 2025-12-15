import shutil
import os

# Ruta de los archivos
src = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templatetags\dict_extras_fixed.py"
dst = r"c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\templatetags\dict_extras.py"

# Copiar el archivo corregido sobre el original
shutil.copy2(src, dst)

# Verificar que el archivo se copió correctamente
if os.path.exists(dst):
    print("Archivo dict_extras.py actualizado correctamente.")
else:
    print("Error al actualizar el archivo dict_extras.py")
