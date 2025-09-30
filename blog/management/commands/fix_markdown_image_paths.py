# blog/management/commands/fix_markdown_image_paths.py
import re
import os
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from blog.models import BlogPost
from kazan import settings


class Command(BaseCommand):
    help = 'Перемещает markdown-изображения в структурированные папки и обновляет ссылки в content_markdown'

    def handle(self, *args, **options):
        posts_with_md_images = BlogPost.objects.filter(
            content_markdown__contains='markdown-images/'
        ).select_related('location', 'author')
        updated_count = 0

        # Регулярное выражение для поиска markdown-изображений с markdown-images/
        # Поддерживаем оба формата: ![alt](url) и <img src="url">
        markdown_img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]*markdown-images/[^)]+)\)')
        html_img_pattern = re.compile(r'<img[^>]*src="([^"]*markdown-images/[^"]+)"[^>]*>')

        for post in posts_with_md_images:
            original_content = post.content_markdown
            new_content = original_content
            has_changes = False

            # 1. Обработка Markdown-синтаксиса: ![alt](url)
            for match in markdown_img_pattern.finditer(original_content):
                old_url = match.group(2)
                if not self._is_valid_url(old_url):
                    continue

                new_url = self._move_image(post, old_url)
                if new_url:
                    new_content = new_content.replace(old_url, new_url)
                    has_changes = True

            # 2. Обработка HTML-тегов: <img src="...">
            for match in html_img_pattern.finditer(original_content):
                old_url = match.group(1)
                if not self._is_valid_url(old_url):
                    continue

                new_url = self._move_image(post, old_url)
                if new_url:
                    new_content = new_content.replace(old_url, new_url)
                    has_changes = True

            if has_changes:
                post.content_markdown = new_content
                post.save(update_fields=['content_markdown'])
                updated_count += 1
                self.stdout.write(f"✅ Обновлён пост: {post.title}")

        self.stdout.write(
            self.style.SUCCESS(f"Завершено. Обновлено постов: {updated_count}")
        )

    def _is_valid_url(self, url):
        """Проверяет, что URL ведёт на наш S3 и содержит markdown-images/"""
        if not url or 'markdown-images/' not in url:
            return False
        # Можно добавить проверку домена, если нужно
        return True

    def _move_image(self, post, old_url):
        try:
            # Убираем MEDIA_URL из начала URL, чтобы получить внутренний путь
            if not old_url.startswith(settings.MEDIA_URL):
                self.stdout.write(self.style.WARNING(f"URL не начинается с MEDIA_URL: {old_url}"))
                return None

            # Получаем внутренний путь (то, что хранится в FileField)
            old_name = old_url[len(settings.MEDIA_URL):].lstrip('/')

            # Теперь old_name — это то, что реально хранится: "markdown-images/..."
            if not old_name.startswith('markdown-images/'):
                return None

            filename = os.path.basename(old_name)
            location_path = post.location.get_path_slug()
            ext = filename.split('.')[-1]
            # new_name = f"markdown-images/{location_path}/{post.slug}/{filename}"
            new_name = f"post_images/{location_path}/{post.slug}/internal_picture.{ext}"

            # Скачиваем через storage
            if not default_storage.exists(old_name):
                self.stdout.write(self.style.WARNING(f"Файл не найден в storage: {old_name}"))
                return None

            with default_storage.open(old_name, 'rb') as f:
                file_content = f.read()

            # Сохраняем в новое место
            new_full_name = default_storage.save(new_name, ContentFile(file_content))

            # Удаляем старый
            default_storage.delete(old_name)

            # Новый URL
            new_url = default_storage.url(new_full_name)
            return new_url

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при перемещении {old_url}: {e}"))
            return None