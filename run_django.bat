@echo off
REM Activar entorno virtual
C:\servidor\Sistema_Digitalizacion\venv\Scripts\activate.bat

REM Cambiar al directorio del proyecto
cd C:\servidor\Sistema_Digitalizacion

REM Ejecutar Django con Waitress
waitress-serve --listen=10.2.17.30:8000 sistema_digitalizacion.wsgi:application

pause
