@echo off
REM ============================================
REM Script para ejecutar el servicio de escaneo
REM ============================================

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Mostrar información
echo ============================================
echo Servicio de Escaneo - Sistema Digitalizacion
echo ============================================
echo.
echo Iniciando servicio...
echo Directorio: %CD%
echo.

REM Ejecutar el script Python
REM Ajusta la ruta de Python según tu instalación
python scan_service.py

REM Si hay error, pausar para ver el mensaje
if errorlevel 1 (
    echo.
    echo ============================================
    echo ERROR: El servicio se detuvo con errores
    echo ============================================
    pause
)

