# Блог на тему "Путешествия по России"

При разработке запустить, если надо менять верстку 
```bash
npm run dev
```
Перед деплоем запустить uv pip freeze > requirements.txt в терминале, находясь в активированной виртуальной среде проекта

После создания новых постов с картинками внутри надо запускать команду 
```bash
uv run python manage.py  fix_markdown_image_paths.py
```
Или посадить ее на cron

## Для корректной работы sitemap

Запусти в админке (/admin/Сайты/Сайты/):
Измени домен на свой (например, travelblog.ru)
Имя — любое (например, TravelBlog)

Для отложенной публикации на сервере должен быть сконфигурирован cron
```
01 23 * * * root docker exec kazan1 python manage.py publish_post >> /var/log/publish_post.log 2>&1
```
