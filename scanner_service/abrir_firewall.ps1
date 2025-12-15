# Script para abrir el puerto 5001 en el Firewall de Windows
# Ejecutar como Administrador

Write-Host "Abriendo puerto 5001 para el servicio de escaneo..." -ForegroundColor Cyan

# Regla para conexiones entrantes
New-NetFirewallRule -DisplayName "Servicio de Escaneo (Puerto 5001)" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5001 `
    -Action Allow `
    -Profile Private,Domain

Write-Host "Puerto 5001 abierto exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora otros dispositivos en tu red pueden acceder al escaner." -ForegroundColor Yellow
Write-Host "Reinicia el servicio de escaneo para aplicar los cambios." -ForegroundColor Yellow

pause

