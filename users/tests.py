from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from bins.models import Create_Bins, BinLike
from users.models import User


class UserRegistrationTest(TestCase):
    """Тест реєстрації нового користувача"""
    
    def test_registration_success(self):
        response = self.client.post(reverse("users:registration"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPassword123",
            "password2": "StrongPassword123",
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        # Перевіряємо, що користувач залогінений
        self.assertTrue(response.context["user"].is_authenticated)

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse("users:registration"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPassword123",
            "password2": "DifferentPassword123",
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertFormError(response, "form", "password2", None)

    def test_registration_duplicate_username(self):
        User.objects.create_user(username="existing", password="pass")
        response = self.client.post(reverse("users:registration"), {
            "username": "existing",
            "email": "new@example.com",
            "password1": "StrongPassword123",
            "password2": "StrongPassword123",
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="existing").count(), 1)


class UserLoginTest(TestCase):
    """Тест логіну користувача"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_login_success(self):
        response = self.client.post(reverse("users:login"), {
            "username": "testuser",
            "password": "testpass123",
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

    def test_login_wrong_password(self):
        response = self.client.post(reverse("users:login"), {
            "username": "testuser",
            "password": "wrongpass",
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertFormError(response, "form", None, "Невірний логін або пароль")

    def test_login_nonexistent_user(self):
        response = self.client.post(reverse("users:login"), {
            "username": "nonexistent",
            "password": "testpass123",
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


class UserLogoutTest(TestCase):
    """Тест виходу з системи"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_logout(self):
        response = self.client.get(reverse("users:logout"), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


class ProfileViewTest(TestCase):
    """Тест сторінки профілю"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass"
        )
        self.client.login(username="testuser", password="pass")

    def test_profile_view_authenticated(self):
        response = self.client.get(reverse("users:profile"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")

    def test_profile_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("users:profile"))
        
        # Має редіректити на логін
        self.assertEqual(response.status_code, 302)
        self.assertIn("/user/login/", response.url)

    def test_profile_shows_liked_bins(self):
        # Створюємо бін та лайк
        bin = Create_Bins.objects.create(
            title="Liked Bin",
            author=self.user,
            hash="likedhash"
        )
        BinLike.objects.create(bin=bin, user=self.user, is_like=True)
        
        response = self.client.get(reverse("users:profile"))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("liked_bins", response.context)
        self.assertEqual(len(response.context["liked_bins"]), 1)


class ProfileUpdateTest(TestCase):
    """Тест оновлення профілю"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="old@example.com",
            password="pass"
        )
        self.client.login(username="testuser", password="pass")

    def test_update_email(self):
        response = self.client.post(reverse("users:profile"), {
            "username": "testuser",
            "email": "new@example.com",
        }, follow=True)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")


class PasswordChangeTest(TestCase):
    """Тест зміни паролю"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="oldpassword"
        )
        self.client.login(username="testuser", password="oldpassword")

    def test_password_change_success(self):
        url = reverse("users:password_change")
        response = self.client.post(url, {
            "old_password": "oldpassword",
            "new_password1": "NewStrongPassword123",
            "new_password2": "NewStrongPassword123",
        }, follow=True)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123"))
        self.assertEqual(response.status_code, 200)

    def test_password_change_wrong_old_password(self):
        url = reverse("users:password_change")
        response = self.client.post(url, {
            "old_password": "wrongpassword",
            "new_password1": "NewStrongPassword123",
            "new_password2": "NewStrongPassword123",
        })
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("NewStrongPassword123"))
        self.assertTrue(self.user.check_password("oldpassword"))

    def test_password_change_mismatch(self):
        url = reverse("users:password_change")
        response = self.client.post(url, {
            "old_password": "oldpassword",
            "new_password1": "NewStrongPassword123",
            "new_password2": "DifferentPassword123",
        })
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpassword"))


class PendingBinCreationTest(TestCase):
    """Тест створення відкладеного біна після логіну/реєстрації"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    @patch("bins.utils.upload_to_r2")
    @patch("bins.utils.get_redis_client")
    def test_create_bin_after_login(self, mock_redis, mock_upload):
        mock_upload.return_value = "https://fake-url.com/bin.txt"
        mock_redis_instance = patch("bins.utils.get_redis_client").start()
        mock_redis_instance.lpop.return_value = b"testhash"
        
        # Симулюємо сесію з відкладеним біном
        session = self.client.session
        session["pending_bin_data"] = {
            "content": "Pending content",
            "title": "Pending Bin",
            "category": "NONE",
            "language": "python",
            "expiry": "never",
            "access": "public",
            "tags": ""
        }
        session.save()
        
        # Логінимось
        response = self.client.post(reverse("users:login"), {
            "username": "testuser",
            "password": "pass",
        }, follow=True)
        
        # Перевіряємо, що pending_bin_data видалено з сесії
        self.assertNotIn("pending_bin_data", self.client.session)


class JWTAuthTest(TestCase):
    """Тест JWT аутентифікації"""

    def setUp(self):
        self.username = "apitest"
        self.password = "testpassword123"
        self.user = User.objects.create_user(
            username=self.username,
            email="apitest@example.com",
            password=self.password
        )
        self.client = APIClient()

    def test_obtain_token_success(self):
        resp = self.client.post("/api/token/", {
            "username": self.username,
            "password": self.password
        }, format="json")
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_obtain_token_wrong_credentials(self):
        resp = self.client.post("/api/token/", {
            "username": self.username,
            "password": "wrongpassword"
        }, format="json")
        
        self.assertEqual(resp.status_code, 401)

    def test_refresh_token(self):
        # Спочатку отримуємо токени
        resp = self.client.post("/api/token/", {
            "username": self.username,
            "password": self.password
        }, format="json")
        
        refresh_token = resp.data.get("refresh")
        
        # Оновлюємо access через refresh
        refresh_resp = self.client.post("/api/token/refresh/", {
            "refresh": refresh_token
        }, format="json")
        
        self.assertEqual(refresh_resp.status_code, 200)
        self.assertIn("access", refresh_resp.data)

    def test_refresh_token_invalid(self):
        refresh_resp = self.client.post("/api/token/refresh/", {
            "refresh": "invalid_token"
        }, format="json")
        
        self.assertEqual(refresh_resp.status_code, 401)