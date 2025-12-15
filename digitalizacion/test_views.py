from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserSession

class UserSessionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Create a test session
        self.session = UserSession.objects.create(
            user=self.user,
            session_key='testsession123',
            last_activity=timezone.now(),
            is_online=True
        )

    def test_api_usuarios_conectados(self):
        """Test that the API returns connected users"""
        response = self.client.get('/api/usuarios-conectados/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(len(data['usuarios']), 1)
