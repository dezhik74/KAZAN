# blog/management/commands/publish_post.py
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import BlogPost

class Command(BaseCommand):
    help = "Публикует один отмодерированный, но неопубликованный пост, если прошло более суток с последней публикации."

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        one_day_ago = now - timedelta(hours=23)

        # 1. Находим самый поздний опубликованный пост
        latest_published = BlogPost.objects.filter(
            is_published=True,
            published_at__isnull=False
        ).order_by('-published_at').first()

        # 2. Если нет ни одного опубликованного поста — публикуем первый отмодерированный
        if latest_published is None:
            self.stdout.write("Нет опубликованных постов. Ищем первый отмодерированный...")
            candidate = BlogPost.objects.filter(
                is_moderated=True,
                is_published=False
            ).order_by('created_at').first()
            if candidate:
                self._publish_post(candidate, now)
            else:
                self.stdout.write("Нет подходящих постов для публикации.")
            return

        # 3. Если последняя публикация была менее суток назад — ничего не делаем
        if latest_published.published_at >= one_day_ago:
            self.stdout.write(
                f"Последняя публикация была {latest_published.published_at}. "
                "Менее суток назад — пропускаем."
            )
            return

        # 4. Ищем самый ранний по updated_at отмодерированный, но неопубликованный пост
        candidate = BlogPost.objects.filter(
            is_moderated=True,
            is_published=False
        ).order_by('updated_at').first()

        if candidate:
            self._publish_post(candidate, now)
        else:
            self.stdout.write("Нет отмодерированных, но неопубликованных постов.")

    def _publish_post(self, post, now):
        post.is_published = True
        post.published_at = now
        post.save(update_fields=['is_published', 'published_at'])
        self.stdout.write(
            self.style.SUCCESS(f"✅ Опубликован пост: {post.title} (ID={post.pk})")
        )