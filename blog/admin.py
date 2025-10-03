# blog/admin.py

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Location, Tag, BlogPost, PostImage, PostRating, AboutPage, AboutPageImage


# =============== ЛОКАЦИИ (древовидные) ===============
class LocationAdmin(TreeAdmin):
    form = movenodeform_factory(Location)
    list_display = ("name", "slug", "get_depth", "get_children_count")
    list_display_links = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)

    def get_depth(self, obj):
        return obj.get_depth()
    get_depth.short_description = "Уровень"

    def get_children_count(self, obj):
        return obj.get_children().count()
    get_children_count.short_description = "Подлокаций"


# =============== ТЕГИ ===============
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "Использований"


# =============== ГАЛЕРЕЯ (Inline) ===============
class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ("image", "caption", "order", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "—"
    image_preview.short_description = "Превью"


# =============== ОЦЕНКИ (только чтение) ===============
class PostRatingInline(admin.TabularInline):
    model = PostRating
    extra = 0
    readonly_fields = ("ip_address", "score", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# =============== ЗАПИСЬ БЛОГА ===============
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "location",
        "is_published",
        "published_at",
        "views_count",
        "average_rating_display",
        "created_at",
    )
    list_filter = (
        "is_published",
        "published_at",
        "created_at",
        "location",
        "tags",
        "author",
    )
    search_fields = ("title", "content_markdown", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    filter_horizontal = ("tags",)
    inlines = [PostImageInline, PostRatingInline]
    readonly_fields = ("views_count", "created_at", "updated_at", "average_rating_display")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Принудительно задаём ширину 100% для SEO-полей
        seo_fields = ['meta_title', 'meta_description']
        for field_name in seo_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].widget.attrs.update({
                    'style': 'width: 100%',
                    'class': 'vTextField'
                })
        return form

    fieldsets = (
        ("Основное", {
            "fields": ("title", "slug", "author", "location", "tags")
        }),
        ("Контент", {
            "fields": ("content_markdown", "cover_image")
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description")
        }),
        ("Публикация", {
            "fields": ("is_published", "published_at")
        }),
        ("Статистика", {
            "fields": ("views_count", "average_rating_display", "created_at", "updated_at")
        }),
    )

    class Media:
        css = {
            'all': ('blog/css/markdownx-horizontal.css',)
        }

    def average_rating_display(self, obj):
        avg = obj.average_rating
        count = obj.rating_count
        if avg is not None:
            return f"★{avg} ({count} голосов)"
        return "—"
    average_rating_display.short_description = "Рейтинг"

    # Защита от удаления опубликованных записей без подтверждения
    def has_delete_permission(self, request, obj=None):
        # Можно удалять только неопубликованные или черновики
        if obj and obj.is_published and obj.published_at and obj.published_at <= timezone.now():
            return False
        return super().has_delete_permission(request, obj)

    # Автоматическая установка автора текущим пользователем
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


# =============== РЕГИСТРАЦИЯ ===============
admin.site.register(Location, LocationAdmin)

# Оценки отдельно (на случай ручной модерации)
@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):
    list_display = ("post", "ip_address", "score", "created_at")
    list_filter = ("score", "created_at", "post__location")
    search_fields = ("post__title", "ip_address")
    readonly_fields = ("post", "ip_address", "score", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # только через API или пост

# =============== ГАЛЕРЕЯ ДЛЯ "О НАС" (Inline) ===============
class AboutPageImageInline(admin.TabularInline):
    model = AboutPageImage
    extra = 1
    fields = ("image", "caption", "order", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "—"
    image_preview.short_description = "Превью"


# =============== СТРАНИЦА "О НАС" ===============
@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "author",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "author")
    search_fields = ("title", "content_markdown", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    inlines = [AboutPageImageInline]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Основное", {
            "fields": ("title", "slug", "author", "is_active")
        }),
        ("Контент", {
            "fields": ("content_markdown", "cover_image")
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description")
        }),
        ("Временные метки", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    class Media:
        css = {
            'all': ('blog/css/markdownx-horizontal.css',)
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Принудительно задаём ширину 100% для SEO-полей
        seo_fields = ['meta_title', 'meta_description']
        for field_name in seo_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].widget.attrs.update({
                    'style': 'width: 100%',
                    'class': 'vTextField'
                })
        return form

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Защита от случайного удаления активной версии
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)