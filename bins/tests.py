from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from bins.models import Create_Bins, BinComment


# class CreateBinErrorTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = get_user_model().objects.create_user(
#             username="testuser", password="testpass"
#         )
#         self.client.login(username="testuser", password="testpass")

#     @patch("boto3.client")
#     def test_create_bin_error_message(self, mock_boto):
#         # Емуляція помилки при збереженні у Cloudflare (R2)
#         mock_boto.return_value.put_object.side_effect = Exception("R2 error")
#         response = self.client.post(reverse('bins:index'), {
#             'content': 'test content',
#             'title': 'testbin',
#             'category': 'CODE',
#             'language': 'python',
#             'expiry': 'never',
#             'access': 'public',
#             'tags': '',
#         }, follow=True)
#         self.assertContains(response, "Не вдалося створити Bin")


class AjaxCommentTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.bin = Create_Bins.objects.create(
            content="Тестовий контент",
            category="NONE",
            language="none",
            expiry="never",
            access="public",
            title="Тест",
            tags="",
            author=self.user,
        )

    def test_ajax_comment(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("bins:bin_comment", args=[self.bin.id])
        # Симулюємо AJAX-запит (як це робить JS)
        response = self.client.post(
            url,
            {"text": "Тест AJAX коментар"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_X_CSRFTOKEN="test"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())
        self.assertTrue(response.json()["success"])
        self.assertIn("comment_html", response.json())
        # Перевіряємо, що коментар реально створено
        self.assertTrue(
            BinComment.objects.filter(bin=self.bin, text="Тест AJAX коментар").exists()
        )
