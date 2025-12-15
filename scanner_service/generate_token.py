"""
Script para generar un token seguro aleatorio para el servicio de escaneo
"""

import secrets
import string

def generate_token(length=32):
    """
    Genera un token seguro aleatorio
    
    Args:
        length: Longitud del token (default: 32)
    
    Returns:
        Token aleatorio seguro
    """
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    return token

def main():
    print("=" * 60)
    print("GENERADOR DE TOKEN SEGURO")
    print("=" * 60)
    print()
    
    # Generar token
    token = generate_token(32)
    
    print("Token generado:")
    print("-" * 60)
    print(token)
    print("-" * 60)
    print()
    
    print("Instrucciones:")
    print("1. Copia este token")
    print("2. Configúralo en scan_service.py (variable AUTH_TOKEN)")
    print("3. Configúralo en Django (variable INTERNAL_UPLOAD_TOKEN)")
    print("4. O configúralo como variable de entorno SCANNER_UPLOAD_TOKEN")
    print()
    
    print("Ejemplo para scan_service.py:")
    print(f'AUTH_TOKEN = "{token}"')
    print()
    
    print("Ejemplo para Django (api_views.py):")
    print(f'INTERNAL_UPLOAD_TOKEN = "{token}"')
    print()
    
    print("Ejemplo para variable de entorno:")
    print(f'$env:SCANNER_UPLOAD_TOKEN = "{token}"')
    print()
    
    # Guardar en archivo opcional
    try:
        guardar = input("¿Guardar en archivo token.txt? (s/N): ").lower().strip()
        if guardar == 's':
            with open('token.txt', 'w') as f:
                f.write(token)
            print("✓ Token guardado en token.txt")
            print("⚠️  IMPORTANTE: Elimina token.txt después de configurarlo (no lo subas a git)")
    except:
        pass

if __name__ == "__main__":
    main()

