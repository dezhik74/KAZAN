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

# Установка uv (официальный способ)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Создание непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser
WORKDIR /code

# Копируем pyproject.toml и (опционально) README и т.п.
COPY --chown=appuser:appuser pyproject.toml README.md /code/

# Переключаемся на пользователя
USER appuser

# Установка зависимостей через uv
# --system — использует системный Python (в контейнере это нормально)
# --no-cache — экономим место
RUN uv pip install --system --no-cache-dir .

# Копируем всё приложение
COPY --chown=appuser:appuser . /code/

# Проверка миграций (если нужно)
COPY --chown=appuser:appuser check_migrations.sh /code/check_migrations.sh
RUN chmod +x /code/check_migrations.sh

EXPOSE 8000

CMD ["/code/startscript.sh"]