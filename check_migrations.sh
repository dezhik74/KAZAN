#!/bin/sh
set -e

cd /code

# Проверяем, есть ли неприменённые миграции
if [ "$(python manage.py showmigrations | grep -v '\[X\]')" ]; then
    echo "⚠️ Есть неприменённые миграции. Выполни 'python manage.py migrate' вручную."
    exit 1
fi