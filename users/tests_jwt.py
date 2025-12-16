from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()


class JWTAuthTest(TestCase):
    """Тест: створення користувача та отримання JWT токенів"""

    def setUp(self):
        # створюємо тестового користувача
        self.username = "apitest"
        self.password = "testpassword123"
        self.user = User.objects.create_user(
            username=self.username, email="apitest@example.com", password=self.password
        )
        # DRF test client
        self.client = APIClient()

    def test_obtain_and_refresh_token(self):
        # Отримуємо access та refresh
        resp = self.client.post(
            "/api/token/",
            {"username": self.username, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

        # Оновлюємо access через refresh
        refresh_token = resp.data.get("refresh")
        refresh_resp = self.client.post(
            "/api/token/refresh/", {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(refresh_resp.status_code, 200)
        self.assertIn("access", refresh_resp.data)
