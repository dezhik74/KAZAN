FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=kazan.settings

# Установка системных зависимостей — от root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создаём пользователя
RUN adduser --disabled-password --gecos '' appuser
WORKDIR /code
USER appuser

# Копируем только необходимое
COPY --chown=appuser:appuser requirements.txt /code/
COPY --chown=appuser:appuser . /code/

# Установка зависимостей
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

ENV PATH="/home/appuser/.local/bin:$PATH"

# Проверяем наличие миграций (не применяем!)
COPY --chown=appuser:appuser check_migrations.sh /code/check_migrations.sh
RUN chmod +x /code/check_migrations.sh

EXPOSE 8000
CMD ["/code/startscript.sh"]
