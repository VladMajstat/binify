from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class CreateBinErrorTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.login(username="testuser", password="testpass")

    def test_create_bin_error_message(self):
        # Викликаємо create_bin з некоректними даними, щоб викликати помилку (наприклад, порожній content)
        response = self.client.post(reverse('bins:index'), {
            'content': '',
            'title': 'testbin',
            'category': 'code',  # додайте значення за замовчуванням
            'language': 'text',
            'expiry': 'forever',
            'access': 'public',
            'tags': '',
        }, follow=True)
        # Перевіряємо, що повідомлення про помилку присутнє у відповіді
        self.assertContains(response, "Не вдалося створити Bin")
