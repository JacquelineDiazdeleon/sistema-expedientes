import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_digitalizacion.settings')
django.setup()

# Import the view after Django is set up
from digitalizacion.views_expedientes import lista_expedientes

# Create a simple request object
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Create a test user
User = get_user_model()
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='testpass123')

factory = RequestFactory()
request = factory.get('/expedientes/lista/')
request.user = user  # Set the user on the request

# Call the view
try:
    response = lista_expedientes(request)
    print("View executed successfully!")
    print(f"Response status code: {response.status_code}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
