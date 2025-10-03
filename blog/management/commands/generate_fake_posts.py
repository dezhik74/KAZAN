# blog/management/commands/generate_fake_posts.py
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from blog.models import BlogPost, Location, Tag
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт 30 фейковых постов для тестирования'

    def handle(self, *args, **options):
        # 1. Получаем или создаём админа
        admin_user, _ = User.objects.get_or_create(
            username='admin',
        )

        # 2. Создаём корневую фейковую локацию
        fake_location, _ = Location.objects.get_or_create(
            name="Фейковая локация",
            defaults={"slug": "fake-location"},
            depth=1
        )

        # 3. Создаём фейковый тег
        fake_tag, _ = Tag.objects.get_or_create(
            name="Фейковый тег",
            defaults={"slug": "fake-tag"}
        )

        # 4. Подготавливаем контент
        fake_content = (
                "Это фейковый контент для тестирования. " * 20
        )[:500]  # ровно 500 символов

        # 5. Даты
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        minus_one_month = now - timedelta(days=30)

        # 6. Создаём 30 постов
        for i in range(1, 31):
            title = f"Fake Title {i}"
            slug = slugify(title)
            published_at = yesterday + timedelta(minutes=i)
            fake_meta_description = f"Fake Description {i}"

            post, created = BlogPost.objects.get_or_create(
                title=title,
                defaults={
                    "slug": slug,
                    "author": admin_user,
                    "location": fake_location,
                    "content_markdown": fake_content,
                    "meta_title": title,
                    "meta_description": fake_meta_description,
                    "created_at": minus_one_month,
                    "updated_at": minus_one_month,
                    "published_at": published_at,
                    "is_published": True,
                }
            )
            if created:
                post.tags.add(fake_tag)
                self.stdout.write(f"✅ Создан пост: {title}")
            else:
                self.stdout.write(f"⚠️ Пост уже существует: {title}")

        self.stdout.write(
            self.style.SUCCESS("Завершено: создано 30 фейковых постов.")
        )
