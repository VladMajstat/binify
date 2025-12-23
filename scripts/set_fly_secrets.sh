#!/usr/bin/env bash
# set_fly_secrets.sh — заповни значення і виконай у терміналі після `fly auth login`

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <app-name>"
  echo "Example: $0 binify-app"
  exit 1
fi
APP="$1"

fly secrets set \
  DJANGO_SECRET_KEY="your_django_secret" \
  DATABASE_URL="postgresql://user:password@host:5432/dbname?sslmode=require" \
  REDIS_HOST="your-redis-host" \
  REDIS_PORT="your-redis-port" \
  REDIS_PASSWORD="your-redis-password" \
  AWS_ACCESS_KEY_ID="your_r2_key" \
  AWS_SECRET_ACCESS_KEY="your_r2_secret" \
  AWS_STORAGE_BUCKET_NAME="binify-bucket" \
  AWS_S3_ENDPOINT_URL="https://your-account.r2.cloudflarestorage.com" \
  AWS_S3_CUSTOM_DOMAIN="binify-bucket.your-account.r2.cloudflarestorage.com" \
  UPSTASH_REDIS_REST_URL="https://your-upstash-rest-url" \
  UPSTASH_REDIS_REST_TOKEN="your-upstash-rest-token" \
  ALLOWED_HOSTS="$APP.fly.dev" \
  CSRF_TRUSTED_ORIGINS="https://$APP.fly.dev"

echo "Secrets set for app: $APP"
