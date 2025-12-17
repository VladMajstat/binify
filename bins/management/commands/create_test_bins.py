"""
Команда Django для створення тестових бінів для розробки та тестування API.

Використання:
    python manage.py create_test_bins [--count=20]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid
import base64

from bins.models import Create_Bins
from bins.services import create_bin_service
from bins.utils import get_redis_client

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює тестові біни для розробки та тестування API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Кількість тестових бінів для створення (за замовчуванням: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистити старі тестові біни перед створенням'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        # Очистка старих бінів (опціонально)
        if clear:
            Create_Bins.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Старі біни видалені'))

        # Создаём або отримуємо тестових користувачів
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@test.local', 'is_staff': True, 'is_superuser': True}
        )
        
        test_user1, _ = User.objects.get_or_create(
            username='testuser1',
            defaults={'email': 'testuser1@test.local'}
        )
        
        test_user2, _ = User.objects.get_or_create(
            username='testuser2',
            defaults={'email': 'testuser2@test.local'}
        )

        self.stdout.write(f'✓ Користувачі готові: admin, testuser1, testuser2')

        # Заповняємо Redis пул хешів, якщо потрібно
        redis_client = get_redis_client()
        pool_size = redis_client.llen('my_unique_hash_pool')
        if pool_size < count:
            self.stdout.write(f'Заповнення Redis пулу хешів (поточно: {pool_size})...')
            for i in range(count):
                hash_value = base64.urlsafe_b64encode((1000 + i).to_bytes(6, "big")).decode("utf-8")[:8]
                redis_client.rpush('my_unique_hash_pool', hash_value)
            self.stdout.write(self.style.SUCCESS(f'✓ Redis пул заповнений'))

        # Тестові дані
        languages = ['python', 'javascript', 'none', 'c++', 'java', 'bash', 'ruby', 'swift']
        categories = ['DEV', 'CONFIG', 'LOG', 'NONE']
        accesses = ['public', 'private']
        expiries = ['never', '1h', '1d', '1w', '30d']
        
        test_snippets = [
            ('print("Hello World")', 'hello-world', 'python', 'DEV'),
            ('const x = 42;', 'javascript-const', 'javascript', 'DEV'),
            ('SELECT * FROM users;', 'sql-select', 'none', 'LOG'),
            ('docker run -d nginx', 'docker-command', 'bash', 'CONFIG'),
            ('for i in range(10): print(i)', 'python-loop', 'python', 'DEV'),
            ('function add(a, b) { return a + b; }', 'js-function', 'javascript', 'DEV'),
            ('curl https://api.example.com', 'curl-request', 'bash', 'NONE'),
            ('npm install express', 'npm-install', 'bash', 'CONFIG'),
            ('git clone https://github.com/user/repo', 'git-clone', 'bash', 'NONE'),
            ('mkdir -p project/src', 'mkdir-command', 'bash', 'CONFIG'),
            ('export API_KEY=secret123', 'env-variable', 'bash', 'CONFIG'),
            ('SELECT COUNT(*) FROM logs;', 'sql-count', 'none', 'LOG'),
            ('[program:myapp]\ncommand=/usr/bin/python app.py', 'supervisor-config', 'none', 'CONFIG'),
            ('version: "3"\nservices:\n  web:\n    image: nginx', 'docker-compose', 'none', 'CONFIG'),
            ('server { listen 80; server_name example.com; }', 'nginx-config', 'none', 'CONFIG'),
            ('.gitignore\nnode_modules/\n.env\nbuild/', 'gitignore', 'none', 'DEV'),
            ('TODO: fix memory leak', 'todo-comment', 'none', 'DEV'),
            ('WARNING: deprecated function', 'warning-log', 'none', 'LOG'),
            ('ERROR: connection timeout', 'error-log', 'none', 'LOG'),
            ('{"status": "ok", "data": []}', 'json-response', 'javascript', 'DEV'),
            ('class User:\n    def __init__(self, name):\n        self.name = name', 'python-class', 'python', 'DEV'),
            ('import React from "react";\nconst App = () => <div>Hello</div>;', 'react-component', 'javascript', 'DEV'),
            ('public class Main {\n    public static void main(String[] args) {}\n}', 'java-main', 'java', 'DEV'),
            ('#!/bin/bash\necho "Starting server..."\nnpm start', 'startup-script', 'bash', 'CONFIG'),
            ('def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)', 'fibonacci', 'python', 'DEV'),
        ]

        created_count = 0
        for i in range(count):
            snippet, title, lang, cat = test_snippets[i % len(test_snippets)]
            expiry = expiries[i % len(expiries)]
            access = accesses[i % len(accesses)]
            author = [admin_user, test_user1, test_user2][i % 3]
            tags = f'test,snippet-{i % 5},{lang}'

            # Готуємо дані для сервісу
            data = {
                'content': f'{snippet}\n# Test snippet #{i}',
                'title': f'{title}-{i}',
                'language': lang,
                'category': cat,
                'access': access,
                'expiry': expiry,
                'tags': tags,
            }

            try:
                bin_obj = create_bin_service(author, data)
                created_count += 1
                status_icon = '✓' if bin_obj else '✗'
                self.stdout.write(f'{status_icon} Created: {bin_obj.title} (lang: {lang}, cat: {cat}, access: {access})')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to create bin #{i}: {e}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Готово! Створено {created_count} із {count} тестових бінів')
        )
        self.stdout.write('\nТепер можеш тестувати у Postman:')
        self.stdout.write('  GET /bins/api/bins/ — всі публічні біни')
        self.stdout.write('  GET /bins/api/bins/?language=python — фільтр по мові')
        self.stdout.write('  GET /bins/api/bins/?category=DEV — фільтр по категорії')
        self.stdout.write('  GET /bins/api/search/?q=hello — пошук')
        self.stdout.write('  GET /bins/api/my-bins/ — мої біни (з JWT)')
