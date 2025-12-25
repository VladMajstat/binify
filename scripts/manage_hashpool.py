#!/usr/bin/env python3
"""
manage_hashpool.py
Простий скрипт для перевірки та наповнення пулу `my_unique_hash_pool` у Upstash.
Використання:
  python scripts/manage_hashpool.py status       # показати LLEN і перші 20 значень
  python scripts/manage_hashpool.py add 50      # додати 50 хешів в кінець пулу

Скрипт використовує змінні середовища `UPSTASH_REDIS_REST_URL` та `UPSTASH_REDIS_REST_TOKEN`.
"""
import os
import sys
import base64

try:
    from upstash_redis import Redis
except Exception as e:
    print("Пакет upstash_redis не знайдено. Встановіть його: pip install upstash-redis")
    sys.exit(2)


def get_client():
    url = os.getenv('UPSTASH_REDIS_REST_URL')
    token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    if not url or not token:
        print('Будь ласка, встановіть змінні середовища UPSTASH_REDIS_REST_URL та UPSTASH_REDIS_REST_TOKEN')
        sys.exit(2)
    return Redis(url=url, token=token)


def status(client):
    try:
        llen = client.llen('my_unique_hash_pool')
        print('LLEN my_unique_hash_pool ->', llen)
        if llen:
            sample = client.lrange('my_unique_hash_pool', 0, min(19, llen-1))
            print('First items (up to 20):')
            for i,v in enumerate(sample):
                if isinstance(v, (bytes, bytearray)):
                    try:
                        v = v.decode('utf-8')
                    except Exception:
                        v = str(v)
                print(f'{i}: {v}')
        else:
            print('(pool is empty)')
    except Exception as e:
        print('Error reading pool:', e)
        sys.exit(3)


def add_hashes(client, n):
    try:
        n = int(n)
    except Exception:
        print('Invalid number:', n)
        sys.exit(2)
    added = 0
    for i in range(n):
        # генеруємо простий унікальний хеш на основі часу/лічильника
        # використовується base64 urlsafe 8 символів
        h = base64.urlsafe_b64encode((os.urandom(6))).decode('utf-8')[:8]
        client.rpush('my_unique_hash_pool', h)
        added += 1
    print(f'Added {added} hashes to my_unique_hash_pool')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: manage_hashpool.py status | add <n>')
        sys.exit(1)
    cmd = sys.argv[1]
    client = get_client()
    if cmd == 'status':
        status(client)
    elif cmd == 'add':
        if len(sys.argv) < 3:
            print('Usage: manage_hashpool.py add <n>')
            sys.exit(1)
        add_hashes(client, sys.argv[2])
    else:
        print('Unknown command:', cmd)
        sys.exit(1)
