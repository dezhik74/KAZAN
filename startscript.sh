#!/bin/sh
set -e

cd /code

echo "[KAZAN] Collect static files..."
python manage.py collectstatic --noinput

# Пока не используем
#echo "[KAZAN] Check migrations..."
#./check_migrations.sh

# echo "[KAZAN] Starting dev server..."
# echo "Django development server..."
# python manage.py runserver 0.0.0.0:8000

echo "[KAZAN] Gunicorn server"
exec gunicorn --config gunicorn.conf.py kazan.wsgi

