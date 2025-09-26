from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from markdownx.models import MarkdownxField
from treebeard.mp_tree import MP_Node


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
        help_text="Поддерживается вставка изображений и ссылок на Rutube"
    )

    cover_image = models.ImageField(
        "Обложка",
        upload_to="blog/covers/%Y/%m/",
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
        return self.is_published and self.published_at is not None and self.published_at <= now

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

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
        upload_to="blog/gallery/%Y/%m/"
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