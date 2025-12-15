"""
Script helper para verificar la configuración del servicio de escaneo
Ejecuta este script para verificar que todo esté configurado correctamente.
"""

import os
import sys
import subprocess
import requests

def check_mark():
    return "✅"
def cross_mark():
    return "❌"
def warning_mark():
    return "⚠️"

def verificar_naps2():
    """Verifica que NAPS2 esté instalado"""
    print("\n[1] Verificando NAPS2...")
    
    rutas_posibles = [
        r"C:\Program Files\NAPS2\NAPS2.Console.exe",
        r"C:\Program Files (x86)\NAPS2\NAPS2.Console.exe",
    ]
    
    # También verificar variable de entorno
    naps2_cli = os.environ.get('NAPS2_CLI')
    if naps2_cli:
        rutas_posibles.insert(0, naps2_cli)
    
    naps2_encontrado = None
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            naps2_encontrado = ruta
            break
    
    if naps2_encontrado:
        print(f"  {check_mark()} NAPS2 encontrado en: {naps2_encontrado}")
        
        # Intentar verificar versión
        try:
            result = subprocess.run(
                [naps2_encontrado, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  {check_mark()} Versión: {version}")
        except:
            print(f"  {warning_mark()} No se pudo verificar la versión")
        
        return naps2_encontrado
    else:
        print(f"  {cross_mark()} NAPS2 no encontrado")
        print(f"  Rutas verificadas: {', '.join(rutas_posibles)}")
        return None


def verificar_perfil_naps2(perfil="HP_ADF_300"):
    """Verifica que el perfil de NAPS2 exista"""
    print(f"\n[2] Verificando perfil NAPS2 '{perfil}'...")
    
    # No hay forma directa de verificar perfiles desde CLI sin escanear
    # Solo podemos informar al usuario
    print(f"  {warning_mark()} Verifica manualmente en NAPS2 GUI que el perfil '{perfil}' existe")
    print(f"    1. Abre NAPS2")
    print(f"    2. Ve a Profiles → Verifica que '{perfil}' esté listado")
    print(f"    3. Asegúrate de que esté configurado con ADF activado")


def verificar_python_deps():
    """Verifica que las dependencias de Python estén instaladas"""
    print("\n[3] Verificando dependencias Python...")
    
    dependencias = ['flask', 'requests']
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"  {check_mark()} {dep} instalado")
        except ImportError:
            print(f"  {cross_mark()} {dep} NO instalado")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\n  Instala las dependencias faltantes:")
        print(f"  pip install {' '.join(faltantes)}")
        return False
    
    return True


def verificar_servicio_corriendo():
    """Verifica si el servicio está corriendo"""
    print("\n[4] Verificando servicio de escaneo...")
    
    try:
        resp = requests.get("http://127.0.0.1:5001/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {check_mark()} Servicio corriendo")
            print(f"  - Status: {data.get('status')}")
            print(f"  - NAPS2 instalado: {data.get('naps2_installed')}")
            print(f"  - Perfil: {data.get('profile')}")
            return True
        else:
            print(f"  {cross_mark()} Servicio respondió con código: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {cross_mark()} Servicio no está corriendo")
        print(f"  Ejecuta: python scan_service.py")
        return False
    except Exception as e:
        print(f"  {cross_mark()} Error al verificar servicio: {e}")
        return False


def verificar_django_endpoint(url="http://127.0.0.1:8000/expedientes/api/documentos/escaneado/"):
    """Verifica que el endpoint de Django esté disponible"""
    print(f"\n[5] Verificando endpoint Django...")
    
    try:
        # Intentar un GET (debería fallar pero confirmar que el endpoint existe)
        resp = requests.get(url, timeout=2)
        # El endpoint solo acepta POST, así que 405 es esperado
        if resp.status_code == 405:
            print(f"  {check_mark()} Endpoint Django disponible (solo acepta POST)")
            return True
        elif resp.status_code == 401:
            print(f"  {check_mark()} Endpoint Django disponible (requiere autenticación)")
            return True
        else:
            print(f"  {warning_mark()} Endpoint respondió con código: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  {cross_mark()} Django no está corriendo o el endpoint no existe")
        print(f"  Verifica que Django esté corriendo en http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"  {warning_mark()} Error al verificar: {e}")
        return False


def verificar_token_config():
    """Verifica que el token esté configurado"""
    print(f"\n[6] Verificando configuración de token...")
    
    # Leer scan_service.py para ver si el token fue cambiado
    try:
        with open('scan_service.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
            if 'CAMBIA_POR_TU_TOKEN_SECRETO_AQUI' in contenido:
                print(f"  {cross_mark()} Token no ha sido configurado")
                print(f"  Abre scan_service.py y cambia AUTH_TOKEN")
                return False
            else:
                print(f"  {check_mark()} Token configurado (verifica que coincida con Django)")
                return True
    except FileNotFoundError:
        print(f"  {cross_mark()} No se encontró scan_service.py")
        print(f"  Asegúrate de estar en el directorio correcto")
        return False


def verificar_escanner():
    """Verifica que el escáner esté conectado (solo informativo)"""
    print(f"\n[7] Verificando escáner...")
    print(f"  {warning_mark()} Verificación manual requerida")
    print(f"  1. Verifica que el HP ScanJet Pro 2600 f1 esté encendido")
    print(f"  2. Verifica que esté conectado por USB o red")
    print(f"  3. Abre NAPS2 y verifica que detecte el escáner")
    print(f"  4. Prueba hacer un escaneo manual desde NAPS2")


def main():
    print("=" * 60)
    print("VERIFICADOR DE CONFIGURACIÓN - SERVICIO DE ESCANEO")
    print("=" * 60)
    
    resultados = []
    
    # Verificaciones
    resultados.append(("NAPS2 instalado", verificar_naps2() is not None))
    verificar_perfil_naps2()
    resultados.append(("Dependencias Python", verificar_python_deps()))
    resultados.append(("Servicio corriendo", verificar_servicio_corriendo()))
    resultados.append(("Endpoint Django", verificar_django_endpoint()))
    resultados.append(("Token configurado", verificar_token_config()))
    verificar_escanner()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for nombre, resultado in resultados:
        icono = check_mark() if resultado else cross_mark()
        print(f"{icono} {nombre}")
    
    exitos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    print(f"\n{exitos}/{total} verificaciones exitosas")
    
    if exitos == total:
        print(f"\n{check_mark()} ¡Todo está configurado correctamente!")
    else:
        print(f"\n{warning_mark()} Revisa los problemas arriba antes de usar el servicio")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificación cancelada por el usuario")
        sys.exit(1)

