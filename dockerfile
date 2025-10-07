# Используем официальный образ Python 3.13 (т.к. requires-python = ">=3.13")
FROM python:3.13-slim-bookworm

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=kazan.settings \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# === УСТАНОВКА UV ГЛОБАЛЬНО ===
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

# Создание непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser

# Создаём рабочую директорию и даём права appuser
RUN mkdir -p /code && chown appuser:appuser /code

WORKDIR /code

# Переключаемся на пользователя
USER appuser

# Копируем только pyproject.toml для кэширования зависимостей
COPY pyproject.toml README.md ./

# Установка зависимостей через uv
# --system — использует системный Python (в контейнере это нормально)
# --no-cache — экономим место
RUN uv pip install --system --no-cache-dir .

# Копируем остальной код
COPY . .

# Проверка миграций (если нужно)
COPY check_migrations.sh ./
RUN chmod +x /code/check_migrations.sh

EXPOSE 8000

CMD ["/code/startscript.sh"]