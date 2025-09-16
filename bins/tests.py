from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch


class CreateBinErrorTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.login(username="testuser", password="testpass")

    @patch("boto3.client")
    def test_create_bin_error_message(self, mock_boto):
        # Емуляція помилки при збереженні у Cloudflare (R2)
        mock_boto.return_value.put_object.side_effect = Exception("R2 error")
        response = self.client.post(reverse('bins:index'), {
            'content': 'test content',
            'title': 'testbin',
            'category': 'CODE',
            'language': 'python',
            'expiry': 'never',
            'access': 'public',
            'tags': '',
        }, follow=True)
        self.assertContains(response, "Не вдалося створити Bin")
