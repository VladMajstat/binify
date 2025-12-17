from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Create_Bins

User = get_user_model()


class UserShortSerializer(serializers.ModelSerializer):
	"""Короткий серіалізатор користувача, щоб не віддавати всю модель."""

	class Meta:
		model = User
		fields = ("id", "username", "email")



class CreateBinsSerializer(serializers.ModelSerializer):
	"""Серіалізатор для моделі `Create_Bins` — лише валідація полів."""

	# author = UserShortSerializer(read_only=True)
	# likes_count = serializers.IntegerField(read_only=True)
	# dislikes_count = serializers.IntegerField(read_only=True)
	# views_count = serializers.IntegerField(read_only=True)

	class Meta:
		model = Create_Bins
		# Включаємо лише набір полів, які клієнт повинен надавати при створенні
		fields = ("content", "title", "language", "expiry", "access", "tags")

	def validate_content(self, value):
		"""Переконатися, що content не порожній або тільки пробіли."""
		if value is None or not str(value).strip():
			raise serializers.ValidationError("Поле 'content' не може бути порожнім.")
		return value

