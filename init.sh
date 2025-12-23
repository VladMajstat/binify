#!/bin/bash
# Скрипт для ініціалізації Django (міграції + superuser)
# Використовуй: docker-compose exec web bash /app/init.sh

echo "🔄 Запуск міграцій..."
python manage.py migrate --noinput

echo "📦 Збір статичних файлів..."
python manage.py collectstatic --noinput --clear

echo "👤 Створення superuser..."
python manage.py shell << EOF
from users.models import User

username = "admin"
email = "admin@binify.local"
password = "admin123"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' створений (пароль: {password})")
else:
    print(f"⚠️  Superuser '{username}' уже існує")
EOF

echo "✅ Ініціалізація завершена!"
