from rest_framework import serializers

from .models import Create_Bins
from users.models import User


class UserShortSerializer(serializers.ModelSerializer):
	"""Короткий серіалізатор користувача, щоб не віддавати всю модель."""

	class Meta:
		model = User
		fields = ("id", "username", "email")



class CreateBinsSerializer(serializers.ModelSerializer):
	"""Серіалізатор для моделі `Create_Bins` — лише валідація полів."""

	class Meta:
		model = Create_Bins
		# Включаємо лише набір полів, які клієнт повинен надавати при створенні
		fields = ("content", "title", "language", "expiry", "access", "tags")

	def validate_content(self, value):
		"""Переконатися, що content не порожній або тільки пробіли."""
		if value is None or not str(value).strip():
			raise serializers.ValidationError("Поле 'content' не може бути порожнім.")
		return value


class BinListSerializer(serializers.ModelSerializer):
	"""Read-only серіалізатор для відображення списків бінів."""
	
	author = UserShortSerializer(read_only=True)
	language_display = serializers.CharField(source='get_language_display', read_only=True)
	category_display = serializers.CharField(source='get_category_display', read_only=True)
	is_active = serializers.SerializerMethodField()
	
	class Meta:
		model = Create_Bins
		fields = (
			"id", "hash", "title", "author", "language", "language_display",
			"category", "category_display", "access", "expiry", "expiry_at",
			"tags", "size_bin", "likes_count", "dislikes_count", "views_count",
			"created_at", "updated_at", "is_active"
		)
		read_only_fields = fields
	
	def get_is_active(self, obj):
		"""Перевіряє, чи не протух бін."""
		return obj.is_active()

