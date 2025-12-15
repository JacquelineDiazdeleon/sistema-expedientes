$filePath = "c:\Users\jacqu\Downloads\Documentos_secretaría\Sistema_Digitalizacion\digitalizacion\urls_expedientes.py"

# Leer el contenido actual
$content = Get-Content -Path $filePath -Raw

# Agregar la importación de escanear_documento_expediente
$importStatement = "from .views_expedientes import ("
$newImportStatement = "from .views_escanear import escanear_documento_expediente`n$importStatement"
$content = $content.Replace($importStatement, $newImportStatement)

# Agregar la ruta de escaneo
$documentosSection = "    # Documentos"
$newDocumentosSection = "    # Escaneo de documentos`n    path('<int:expediente_id>/escanear-documento/', `n         escanear_documento_expediente, name='escanear_documento'),`n`n$documentosSection"
$content = $content.Replace($documentosSection, $newDocumentosSection)

# Guardar los cambios
$content | Set-Content -Path $filePath -NoNewline

Write-Host "Archivo actualizado exitosamente."
