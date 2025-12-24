from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Define los permisos
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.install']

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Guarda el token
with open('token_final.json', 'w') as token:
    token.write(creds.to_json())

print("¡Listo! Se ha creado token_final.json. Copia su contenido.")

