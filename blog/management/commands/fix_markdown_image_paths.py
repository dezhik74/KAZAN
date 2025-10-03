# blog/management/commands/fix_markdown_image_paths.py
import re
import os
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from blog.models import BlogPost, AboutPage
from kazan import settings

class Command(BaseCommand):
    help = 'Перемещает markdown-изображения в структурированные папки и обновляет ссылки в content_markdown'

    def handle(self, *args, **options):
        updated_count = 0

        # Обработка BlogPost
        posts_with_md_images = BlogPost.objects.filter(
            content_markdown__contains='markdown-images/'
        ).select_related('location', 'author')
        updated_count += self._process_posts(posts_with_md_images, is_about=False)

        # Обработка AboutPage
        about_pages_with_md_images = AboutPage.objects.filter(
            content_markdown__contains='markdown-images/'
        )
        updated_count += self._process_posts(about_pages_with_md_images, is_about=True)

        self.stdout.write(
            self.style.SUCCESS(f"Завершено. Обновлено записей: {updated_count}")
        )

    def _process_posts(self, queryset, is_about=False):
        updated_count = 0
        # Регулярные выражения
        markdown_img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]*markdown-images/[^)]+)\)')
        html_img_pattern = re.compile(r'<img[^>]*src="([^"]*markdown-images/[^"]+)"[^>]*>')

        for obj in queryset:
            original_content = obj.content_markdown
            new_content = original_content
            has_changes = False

            # 1. Markdown-синтаксис
            for match in markdown_img_pattern.finditer(original_content):
                old_url = match.group(2)
                if not self._is_valid_url(old_url):
                    continue
                new_url = self._move_image(obj, old_url, is_about)
                if new_url:
                    new_content = new_content.replace(old_url, new_url)
                    has_changes = True

            # 2. HTML-теги
            for match in html_img_pattern.finditer(original_content):
                old_url = match.group(1)
                if not self._is_valid_url(old_url):
                    continue
                new_url = self._move_image(obj, old_url, is_about)
                if new_url:
                    new_content = new_content.replace(old_url, new_url)
                    has_changes = True

            if has_changes:
                obj.content_markdown = new_content
                obj.save(update_fields=['content_markdown'])
                updated_count += 1
                model_name = "AboutPage" if is_about else "BlogPost"
                self.stdout.write(f"✅ Обновлён {model_name}: {obj.title if hasattr(obj, 'title') else obj.pk}")

        return updated_count

    def _is_valid_url(self, url):
        """Проверяет, что URL содержит markdown-images/"""
        return url and 'markdown-images/' in url

    def _move_image(self, obj, old_url, is_about=False):
        try:
            if not old_url.startswith(settings.MEDIA_URL):
                self.stdout.write(self.style.WARNING(f"URL не начинается с MEDIA_URL: {old_url}"))
                return None

            old_name = old_url[len(settings.MEDIA_URL):].lstrip('/')
            if not old_name.startswith('markdown-images/'):
                return None

            filename = os.path.basename(old_name)
            ext = filename.split('.')[-1]

            if is_about:
                # Для AboutPage: about_images/{id}/internal_picture.{ext}
                if not obj.pk:
                    self.stdout.write(self.style.WARNING("AboutPage без pk — пропуск"))
                    return None
                new_name = f"about_images/{obj.pk}/internal_picture.{ext}"
            else:
                # Для BlogPost: post_images/{location_path}/{slug}/internal_picture.{ext}
                if not obj.location or not obj.slug:
                    self.stdout.write(self.style.WARNING(f"BlogPost без location или slug: {obj.title}"))
                    return None
                location_path = obj.location.get_path_slug()
                new_name = f"post_images/{location_path}/{obj.slug}/internal_picture.{ext}"

            if not default_storage.exists(old_name):
                self.stdout.write(self.style.WARNING(f"Файл не найден: {old_name}"))
                return None

            with default_storage.open(old_name, 'rb') as f:
                file_content = f.read()

            new_full_name = default_storage.save(new_name, ContentFile(file_content))
            default_storage.delete(old_name)

            new_url = default_storage.url(new_full_name)
            return new_url

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при перемещении {old_url}: {e}"))
            return None