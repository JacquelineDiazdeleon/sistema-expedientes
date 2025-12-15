# ✅ Checklist de Instalación - Sistema de Escaneo

Usa este checklist para asegurarte de que todo esté configurado correctamente.

## 📋 Preparación

- [ ] HP ScanJet Pro 2600 f1 encendido y conectado
- [ ] Python 3.10+ instalado
- [ ] Django corriendo en `http://127.0.0.1:8000`
- [ ] Acceso de administrador a Windows

## 🔧 Instalación de Software

- [ ] Drivers HP instalados (Full Feature, TWAIN)
- [ ] NAPS2 instalado (`C:\Program Files\NAPS2\`)
- [ ] NAPS2 detecta el escáner HP
- [ ] Perfil `HP_ADF_300` creado en NAPS2
- [ ] Perfil `HP_ADF_300` configurado con ADF
- [ ] Perfil `HP_ADF_300` probado manualmente (escaneo funciona)

## 📦 Servicio de Escaneo

- [ ] Directorio `C:\scanner_service\` creado
- [ ] Archivo `scan_service.py` copiado
- [ ] Dependencias instaladas: `pip install flask requests`
- [ ] Token generado (usando `generate_token.py`)
- [ ] Token configurado en `scan_service.py` (variable `AUTH_TOKEN`)
- [ ] Ruta de NAPS2 verificada en `scan_service.py`
- [ ] URL de Django verificada en `scan_service.py`
- [ ] Servicio probado manualmente: `python scan_service.py`
- [ ] Health check funciona: `curl http://127.0.0.1:5001/health`

## 🐍 Django

- [ ] Endpoint agregado en `urls_expedientes.py`
- [ ] Vista `subir_documento_escaneado_api` en `api_views.py`
- [ ] Token configurado en Django (igual que en `scan_service.py`)
- [ ] Usuario `servicio_local` existe (se crea automáticamente)
- [ ] Django corriendo y accesible

## 🖥️ Frontend

- [ ] Botón "Escanear" visible en modal de subir documento
- [ ] JavaScript cargado correctamente
- [ ] Sin errores en consola del navegador

## 🧪 Pruebas

- [ ] Verificación de configuración: `python config_helper.py`
- [ ] Prueba de escaneo desde Django (documento real)
- [ ] Documento aparece en la lista después del escaneo
- [ ] Documento se puede descargar y ver
- [ ] Archivos temporales NO quedan en el sistema
- [ ] Logs se guardan correctamente

## 🔄 Servicio Windows (Opcional)

- [ ] NSSM descargado e instalado
- [ ] Servicio creado con NSSM
- [ ] Servicio configurado para arrancar automáticamente
- [ ] Servicio iniciado: `nssm start scanner_service`
- [ ] Servicio funciona después de reiniciar Windows

## 🔒 Seguridad

- [ ] Token seguro (32+ caracteres aleatorios)
- [ ] Token NO está en repositorios públicos
- [ ] Servicio solo escucha en localhost (127.0.0.1)
- [ ] Firewall no bloquea puerto 5001 (o está permitido)

## 📝 Documentación

- [ ] Leída `INSTALACION.md` completa
- [ ] Revisado `README.md`
- [ ] Entendido el flujo de funcionamiento

---

## 🚀 Cuando Todo Esté Listo

1. Reinicia el servicio: `nssm restart scanner_service` (si usas servicio)
2. Reinicia Django si hiciste cambios
3. Prueba un escaneo completo desde Django
4. Verifica que todo funcione correctamente

---

## ❓ Si Algo No Funciona

1. Revisa los logs: `scanner_service.log`
2. Ejecuta: `python config_helper.py`
3. Verifica servicio: `curl http://127.0.0.1:5001/health`
4. Revisa sección "Solución de Problemas" en `INSTALACION.md`

---

**¡Éxito con tu sistema de escaneo!** 🎉

