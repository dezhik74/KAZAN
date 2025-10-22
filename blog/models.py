import os

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from markdownx.models import MarkdownxField
from treebeard.mp_tree import MP_Node

from blog.upload_paths import cover_upload_to, gallery_upload_to, about_page_cover_upload_to
from blog.utils import markdownify_with_video


# =============== ЛОКАЦИИ ===============
class Location(MP_Node):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True)
    description = models.TextField("Описание", blank=True)

    node_order_by = ['name']

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        return self.get_full_path()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_full_path(self):
        return " / ".join(
            node.name for node in list(self.get_ancestors()) + [self]
        )

    def get_path_slug(self):
        """Возвращает путь из slug'ов: 'kazan/kazanskiy-kreml'"""
        ancestors = list(self.get_ancestors()) + [self]
        return "/".join(node.slug for node in ancestors)

    def get_absolute_url(self):
        return f"/location/{self.get_path_slug()}/"

    def get_breadcrumbs(self):
        """Возвращает список кортежей (локация, URL) для хлебных крошек"""
        ancestors = list(self.get_ancestors()) + [self]
        return [
            (node, f"/location/{'/'.join(a.slug for a in list(node.get_ancestors()) + [node])}/")
            for node in ancestors
        ]

# =============== ТЕГИ ===============
class Tag(models.Model):
    name = models.CharField("Название", max_length=50, unique=True)
    slug = models.SlugField("Slug", max_length=50, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag_detail", kwargs={"slug": self.slug})


# =============== ЗАПИСЬ БЛОГА ===============
class BlogPost(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="travel_posts"
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        verbose_name="Локация",
        related_name="posts"
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        blank=True,
        related_name="posts"
    )

    content_markdown = MarkdownxField(
        "Контент",
        help_text="Поддерживается вставка изображений и ссылок на Rutube в формате {{ rutube:abcde123456 }}"
    )

    cover_image = models.ImageField(
        "Обложка",
        upload_to=cover_upload_to,
        blank=True,
        null=True
    )

    # SEO
    meta_title = models.CharField("SEO Title", max_length=255, blank=True)
    meta_description = models.CharField("SEO Description", max_length=160, blank=True)

    # Статистика
    views_count = models.PositiveIntegerField("Просмотры", default=0)

    # Публикация
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    published_at = models.DateTimeField("Дата публикации", null=True, blank=True)
    is_published = models.BooleanField("Опубликовано", default=False)
    is_moderated = models.BooleanField("Прошёл модерацию", default=False)

    class Meta:
        verbose_name = "Запись блога"
        verbose_name_plural = "Записи блога"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def is_visible_to_public(self):
        now = timezone.now()
        return (
                self.is_published
                and self.is_moderated
                and self.published_at is not None
                and self.published_at <= now
        )

    def get_absolute_url(self):
        location_path = self.location.get_path_slug()
        return f"/post/{location_path}/{self.slug}/"

    def get_seo_title(self):
        return self.meta_title or self.title

    @property
    def average_rating(self):
        """Средняя оценка поста (округлённая до 1 знака)"""
        ratings = self.ratings.aggregate(avg=models.Avg('score'))['avg']
        return round(ratings, 1) if ratings else None

    @property
    def rating_count(self):
        """Количество оценок"""
        return self.ratings.count()

    def get_breadcrumbs(self):
        """Хлебные крошки для поста: Главная > Локация1 > Локация2 > Название поста"""
        crumbs = [
            ("Главная", "/"),
        ]
        # Добавляем все локации
        location_crumbs = self.location.get_breadcrumbs()
        for loc, url in location_crumbs:
            crumbs.append((loc.name, url))
        # Добавляем сам пост (без ссылки)
        crumbs.append((self.title, None))
        return crumbs

# =============== ГАЛЕРЕЯ ===============
class PostImage(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        verbose_name="Запись",
        related_name="gallery"
    )
    image = models.ImageField(
        "Изображение",
        upload_to=gallery_upload_to,
        max_length=650,
    )
    caption = models.CharField("Подпись", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Изображение в галерее"
        verbose_name_plural = "Галерея"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.post.title} — {self.caption or 'Изображение'}"


# =============== ОЦЕНКИ ПО IP ===============
class PostRating(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        verbose_name="Запись",
        related_name="ratings"
    )
    ip_address = models.GenericIPAddressField("IP-адрес")
    score = models.PositiveSmallIntegerField("Оценка", choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField("Дата оценки", auto_now_add=True)

    class Meta:
        verbose_name = "Оценка поста"
        verbose_name_plural = "Оценки постов"
        unique_together = ("post", "ip_address")  # ← ключевое ограничение!
        indexes = [
            models.Index(fields=["post", "ip_address"]),
        ]

    def __str__(self):
        return f"{self.post.title} — {self.score}★ от {self.ip_address}"


# =============== Умный счетчик просмотров ===============
class PostView(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'ip_address', 'created_at')
        verbose_name = "Просмотр поста"
        verbose_name_plural = "Просмотры постов"


# =============== СТРАНИЦА "О НАС" ===============
class AboutPage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=False)  # ← не уникальный!
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name="Автор",
        related_name="about_pages",
        null=True,
        blank=True
    )
    content_markdown = MarkdownxField(
        "Контент",
        help_text="Поддерживается вставка изображений и ссылок на Rutube в формате {{ rutube:abcde123456 }}"
    )
    cover_image = models.ImageField(
        "Обложка",
        upload_to=about_page_cover_upload_to,
        blank=True,
        null=True
    )
    # SEO
    meta_title = models.CharField("SEO Title", max_length=255, blank=True)
    meta_description = models.CharField("SEO Description", max_length=160, blank=True)
    # Активность
    is_active = models.BooleanField("Активна", default=False, help_text="Только одна запись может быть активной")
    # Временные метки
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Страница «О нас»"
        verbose_name_plural = "Страницы «О нас»"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Сохраняем запись, чтобы получить pk (для upload_to)
        if self.pk is None:
            saved_image = self.cover_image
            self.cover_image = None
            super().save(*args, **kwargs)
            self.cover_image = saved_image
            if self.cover_image:
                # Обновляем имя файла с учётом pk
                from django.core.files.storage import default_storage
                old_name = self.cover_image.name
                new_name = about_page_cover_upload_to(self, os.path.basename(old_name))
                if old_name != new_name:
                    self.cover_image.name = default_storage.save(new_name, self.cover_image)
                    default_storage.delete(old_name)
        else:
            if self.is_active:
                AboutPage.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def get_seo_title(self):
        return self.meta_title or self.title

    def get_markdown_content(self):
        return markdownify_with_video(self.content_markdown)


# =============== ГАЛЕРЕЯ ДЛЯ "О НАС" ===============
def about_page_gallery_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return f'about_images/{instance.page.pk}/gallery.{ext}'

class AboutPageImage(models.Model):
    page = models.ForeignKey(
        AboutPage,
        on_delete=models.CASCADE,
        verbose_name="Страница «О нас»",
        related_name="gallery"
    )
    image = models.ImageField(
        "Изображение",
        upload_to=about_page_gallery_upload_to,
    )
    caption = models.CharField("Подпись", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Изображение на странице «О нас»"
        verbose_name_plural = "Галерея страницы «О нас»"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.page.title} — {self.caption or 'Изображение'}"

    def save(self, *args, **kwargs):
        # Аналогично: сначала сохраняем без изображения, если pk ещё нет
        if self.pk is None and self.page.pk is None:
            raise ValueError("Нельзя сохранить AboutPageImage без сохранённой страницы AboutPage.")
        super().save(*args, **kwargs)