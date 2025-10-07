from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="oldpassword"
        )
        self.client.login(username="testuser", password="oldpassword")

    def test_password_change_success(self):
        url = reverse("users:password_change")
        response = self.client.post(
            url,
            {
                "old_password": "oldpassword",
                "new_password1": "NewStrongPassword123",
                "new_password2": "NewStrongPassword123",
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123"))
        self.assertEqual(response.status_code, 302)

    def test_password_change_error(self):
        url = reverse("users:password_change")
        response = self.client.post(
            url,
            {
                "old_password": "wrongpassword",
                "new_password1": "NewStrongPassword123",
                "new_password2": "NewStrongPassword123",
            },
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("NewStrongPassword123"))
        self.assertContains(response, "старий пароль")  # або текст помилки з шаблону
