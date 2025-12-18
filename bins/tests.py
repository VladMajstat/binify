from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
from bins.models import Create_Bins, BinComment, BinLike
from bins.utils import cache_bin_meta_and_content, invalidate_bin_cache, get_redis_client
from django.utils import timezone
from datetime import timedelta
import json
import redis

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

redis_cache = redis.Redis(host="localhost", port=6379)


class BinCacheTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.bin = Create_Bins.objects.create(
            title="Test Bin",
            author=self.user,
            language="python",
            category="code",
            views_count=50,  # саме 50 переглядів
        )

    def test_bin_meta_cached(self):
        meta_key = f"bin_meta:{self.bin.hash}"
        # Імітуємо логіку кешування (як у view)
        meta = {
            "title": self.bin.title,
            "author": self.bin.author.username,
            "created_at": str(self.bin.created_at),
            "size_bin": getattr(self.bin, "size_bin", 0),
            "language": self.bin.language,
            "language_display": (
                self.bin.get_language_display()
                if hasattr(self.bin, "get_language_display")
                else self.bin.language
            ),
            "category": self.bin.category,
            "category_display": (
                self.bin.get_category_display()
                if hasattr(self.bin, "get_category_display")
                else self.bin.category
            ),
            "tags": getattr(self.bin, "tags", ""),
        }
        if self.bin.views_count >= 50:
            redis_cache.setex(meta_key, 3600, json.dumps(meta))

        # Тепер перевіряємо, чи зберігся кеш
        cached = redis_cache.get(meta_key)
        self.assertIsNotNone(cached, "Кеш для біна не зберігся!")
        cached_meta = json.loads(cached)
        self.assertEqual(cached_meta["title"], self.bin.title)
        self.assertEqual(cached_meta["author"], self.bin.author.username)


class CreateBinSuccessTest(TestCase):
    """Тест успішного створення біна"""
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    @patch("bins.utils.upload_to_r2")
    @patch("bins.utils.get_redis_client")
    def test_create_bin_success(self, mock_redis, mock_upload):
        # Мокаємо R2 та Redis
        mock_upload.return_value = "https://fake-url.com/bin.txt"
        mock_redis_instance = MagicMock()
        mock_redis_instance.lpop.return_value = b"testhash"
        mock_redis.return_value = mock_redis_instance

        response = self.client.post(reverse("bins:index"), {
            "content": "Test content",
            "title": "Test Bin",
            "category": "NONE",
            "language": "python",
            "expiry": "never",
            "access": "public",
            "tags": "test,demo"
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Create_Bins.objects.filter(title__icontains="Test Bin").exists())


class ViewBinTest(TestCase):
    """Тест перегляду біна"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.bin = Create_Bins.objects.create(
            title="Public Bin",
            content="Test content",
            author=self.user,
            access="public",
            hash="publichash123"
        )
        self.private_bin = Create_Bins.objects.create(
            title="Private Bin",
            content="Secret content",
            author=self.user,
            access="private",
            hash="privatehash456"
        )

    @patch("bins.utils.get_bin_content")
    def test_view_public_bin(self, mock_content):
        mock_content.return_value = "Test content"
        response = self.client.get(reverse("bins:view_bin", args=[self.bin.hash]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Bin")

    def test_view_count_increments(self):
        initial_count = self.bin.views_count
        self.client.get(reverse("bins:view_bin", args=[self.bin.hash]))
        self.bin.refresh_from_db()
        self.assertEqual(self.bin.views_count, initial_count + 1)


class EditBinTest(TestCase):
    """Тест редагування біна"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.bin = Create_Bins.objects.create(
            title="Original Title",
            content="Original content",
            author=self.user,
            hash="edithash123",
            file_key="bins/test.txt"
        )

    @patch("bins.utils.upload_to_r2")
    @patch("bins.utils.get_bin_content")
    def test_edit_bin_as_owner(self, mock_get, mock_upload):
        mock_get.return_value = "Original content"
        mock_upload.return_value = "https://fake-url.com/updated.txt"
        
        self.client.login(username="owner", password="pass")
        response = self.client.post(reverse("bins:edit_bin", args=[self.bin.hash]), {
            "content": "Updated content",
            "title": "Updated Title",
            "category": "NONE",
            "language": "python",
            "expiry": "never",
            "access": "public",
            "tags": ""
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.bin.refresh_from_db()
        self.assertEqual(self.bin.title, "Updated Title")

    def test_edit_bin_as_non_owner(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(reverse("bins:edit_bin", args=[self.bin.hash]))
        self.assertEqual(response.status_code, 404)


class DeleteBinTest(TestCase):
    """Тест видалення біна"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.bin = Create_Bins.objects.create(
            title="To Delete",
            author=self.user,
            hash="delhash123",
            file_key="bins/del.txt"
        )

    @patch("bins.utils.delete_from_r2")
    def test_delete_bin_as_owner(self, mock_delete):
        mock_delete.return_value = True
        self.client.login(username="owner", password="pass")
        response = self.client.post(reverse("bins:delete_bin", args=[self.bin.hash]), follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Create_Bins.objects.filter(hash="delhash123").exists())

    def test_delete_bin_as_non_owner(self):
        self.client.login(username="other", password="pass")
        response = self.client.post(reverse("bins:delete_bin", args=[self.bin.hash]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Create_Bins.objects.filter(hash="delhash123").exists())


class LikeDislikeTest(TestCase):
    """Тест лайків/дизлайків"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bin = Create_Bins.objects.create(
            title="Test",
            author=self.user,
            hash="likehash",
            likes_count=0,
            dislikes_count=0
        )

    def test_like_bin(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("bins:bin_likes_dislikes", args=[self.bin.hash]),
            {"action": "like"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["likes"], 1)
        self.assertEqual(data["dislikes"], 0)

    def test_dislike_bin(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("bins:bin_likes_dislikes", args=[self.bin.hash]),
            {"action": "dislike"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["likes"], 0)
        self.assertEqual(data["dislikes"], 1)

    def test_toggle_like_to_dislike(self):
        self.client.login(username="testuser", password="pass")
        # Спочатку лайк
        self.client.post(
            reverse("bins:bin_likes_dislikes", args=[self.bin.hash]),
            {"action": "like"}
        )
        # Потім дизлайк
        response = self.client.post(
            reverse("bins:bin_likes_dislikes", args=[self.bin.hash]),
            {"action": "dislike"}
        )
        
        data = response.json()
        self.assertEqual(data["likes"], 0)
        self.assertEqual(data["dislikes"], 1)


class UserBinsListTest(TestCase):
    """Тест списку бінів користувача"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bin1 = Create_Bins.objects.create(
            title="Bin 1",
            author=self.user,
            hash="hash1"
        )
        self.bin2 = Create_Bins.objects.create(
            title="Bin 2",
            author=self.user,
            hash="hash2"
        )

    def test_user_bins_list(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse("bins:user_bins"))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bin 1")
        self.assertContains(response, "Bin 2")


class CommentTest(TestCase):
    """Тест коментарів"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bin = Create_Bins.objects.create(
            title="Test",
            author=self.user,
            hash="comhash"
        )

    def test_add_comment(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("bins:bin_comment", args=[self.bin.hash]),
            {"text": "Great bin!"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BinComment.objects.filter(bin=self.bin, text="Great bin!").exists())

    def test_comment_requires_auth(self):
        response = self.client.post(
            reverse("bins:bin_comment", args=[self.bin.hash]),
            {"text": "Anonymous comment"}
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertFalse(BinComment.objects.filter(text="Anonymous comment").exists())


class ExpiredBinTest(TestCase):
    """Тест прострочених бінів"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_expired_bin_is_inactive(self):
        expired_bin = Create_Bins.objects.create(
            title="Expired",
            author=self.user,
            hash="exphash",
            expiry_at=timezone.now() - timedelta(hours=1)
        )
        self.assertFalse(expired_bin.is_active())

    def test_active_bin_is_active(self):
        active_bin = Create_Bins.objects.create(
            title="Active",
            author=self.user,
            hash="acthash",
            expiry_at=timezone.now() + timedelta(hours=1)
        )
        self.assertTrue(active_bin.is_active())

    def test_never_expire_bin_is_active(self):
        never_bin = Create_Bins.objects.create(
            title="Never Expires",
            author=self.user,
            hash="nevhash",
            expiry_at=None
        )
        self.assertTrue(never_bin.is_active())


class CacheInvalidationTest(TestCase):
    """Тест інвалідації кешу"""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bin = Create_Bins.objects.create(
            title="Cache Test",
            author=self.user,
            hash="cachehash"
        )

    def test_cache_invalidation(self):
        # Кешуємо бін
        cache_bin_meta_and_content(self.bin, "Test content")
        redis_client = get_redis_client()
        meta_key = f"bin_meta:{self.bin.hash}"
        
        # Перевіряємо наявність кешу
        self.assertIsNotNone(redis_client.get(meta_key))
        
        # Інвалідуємо кеш
        invalidate_bin_cache(self.bin.hash)
        
        # Перевіряємо відсутність кешу
        self.assertIsNone(redis_client.get(meta_key))

