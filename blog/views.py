from datetime import timedelta

from django.db import models
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.urls import reverse
from markdownx.views import markdownify_func

from .models import BlogPost, Location, Tag, PostView, PostRating, AboutPage
from .utils import markdownify_with_video, add_title_to_context


class PostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            is_moderated=True,
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).select_related('author', 'location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [("Главная", "/")]
        context = add_title_to_context(context, "Путешествия и локации")
        return context


class PostArchiveView(ListView):
    model = BlogPost
    template_name = 'blog/post_archive.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            is_moderated=True,
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).select_related('author', 'location').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [("Главная", "/"), ("Архив", "/posts/")]
        return context


class PostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        location_path = self.kwargs['location_path'].rstrip('/')
        slug = self.kwargs['slug']
        # Находим локацию
        slug_parts = location_path.split('/')
        try:
            location = Location.objects.get(slug=slug_parts[-1])
            if location.get_path_slug() != location_path:
                raise Location.DoesNotExist
        except Location.DoesNotExist:
            raise Http404("Локация не найдена")

        post = get_object_or_404(BlogPost, slug=slug, location=location)

        # Режим предпросмотра: только для авторизованных (в т.ч. из админки)
        preview = self.request.GET.get('preview') == '1'
        if preview:
            if not self.request.user.is_authenticated:
                raise Http404()
        else:
            # Обычный режим: только опубликованные и отмодерированные
            if not post.is_visible_to_public():
                raise Http404()

        # Счётчик просмотров — только в обычном режиме
        if not preview:
            ip = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR'))
            if ip:
                day_ago = timezone.now() - timedelta(hours=24)
                if not PostView.objects.filter(
                        post=post,
                        ip_address=ip,
                        created_at__gte=day_ago
                ).exists():
                    PostView.objects.create(post=post, ip_address=ip)
                    BlogPost.objects.filter(pk=post.pk).update(views_count=models.F('views_count') + 1)
                    post.views_count += 1

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.object.get_breadcrumbs()
        context["content_markdown_safe"] = markdownify_with_video(self.object.content_markdown)
        return context


class LocationDetailView(ListView):
    template_name = 'blog/location_detail.html'
    context_object_name = 'posts'
    paginate_by = 10  # ← пагинация

    def get_queryset(self):
        location_path = self.kwargs['location_path'].rstrip('/')
        slug_parts = location_path.split('/')
        try:
            location = Location.objects.get(slug=slug_parts[-1])
            if location.get_path_slug() != location_path:
                raise Location.DoesNotExist
        except Location.DoesNotExist:
            raise Http404("Локация не найдена")

        # Сохраняем локацию в self.location для использования в get_context_data
        self.location = location

        # Все посты в этой локации и её подлокациях
        descendants = list(location.get_descendants()) + [location]
        return BlogPost.objects.filter(
            location__in=descendants,
            is_published=True,
            is_moderated=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'location').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.location

        # Хлебные крошки
        crumbs = [("Главная", "/")]
        location_crumbs = self.location.get_breadcrumbs()
        for loc, url in location_crumbs:
            crumbs.append((loc.name, url))
        context['breadcrumbs'] = crumbs
        context = add_title_to_context(context, self.location.name)
        return context

class RootLocationListView(ListView):
    model = Location
    template_name = 'blog/location_root.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return Location.get_root_nodes()


class TagListView(ListView):
    model = Tag
    template_name = 'blog/tag_list.html'
    context_object_name = 'tags'
    queryset = Tag.objects.all()

class TagDetailView(ListView):
    template_name = 'blog/tag_detail.html'
    context_object_name = 'posts'
    paginate_by = 10  # как на главной

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            tags=self.tag,
            is_published=True,
            is_moderated=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'location').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        # Хлебные крошки
        context['breadcrumbs'] = [
            ("Главная", "/"),
            ("Теги", reverse("blog:tag_list")),
            (self.tag.name, None)
        ]
        context = add_title_to_context(context, f"{self.tag.name} - Теги")
        return context


class PostRatingView(View):
    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, pk=post_id)
        score = request.POST.get('score')
        if not score or not score.isdigit():
            return HttpResponse("Неверная оценка", status=400)
        score = int(score)
        if score < 1 or score > 5:
            return HttpResponse("Оценка должна быть от 1 до 5", status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if ip:
            # Обновляем или создаём оценку
            PostRating.objects.update_or_create(
                post=post,
                ip_address=ip,
                defaults={'score': score}
            )
            # Обновляем кэшированные значения (если бы они были) — пока не нужно
        else:
            return HttpResponse("Не удалось определить IP", status=400)

        # Рендерим только обновлённый блок рейтинга
        context = {'post': post}
        return render(request, 'blog/partials/post_rating.html', context)


class BestPostsView(ListView):
    model = BlogPost
    template_name = 'blog/best_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            is_moderated=True,
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).annotate(
            avg_rating=models.Avg('ratings__score')
        ).filter(
            avg_rating__isnull=False
        ).order_by('-avg_rating', '-views_count').select_related('author', 'location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            ("Главная", "/"),
            ("Лучшие", None)
        ]
        return context


class PopularPostsView(ListView):
    model = BlogPost
    template_name = 'blog/popular_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            published_at__isnull=False,
            is_moderated=True,
            published_at__lte=timezone.now()
        ).order_by('-views_count', '-published_at').select_related('author', 'location')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            ("Главная", "/"),
            ("Популярные", None)
        ]
        return context


class AboutPageView(DetailView):
    model = AboutPage
    template_name = 'blog/about_page.html'
    context_object_name = 'page'

    def get_object(self, queryset=None):
        # Всегда возвращаем единственную активную запись
        return get_object_or_404(AboutPage, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            ("Главная", "/"),
            ("О нас", None)
        ]
        # Рендерим контент с поддержкой Rutube и безопасным HTML
        context['content_safe'] = markdownify_with_video(self.object.content_markdown)
        return context


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /markdownx/",
        # добавляем страницы старого домена, которые надо убрать из индексации (замечание Яндекс Вебмастер)
        "Disallow: /category/без-рубрики",
        "Disallow: /kuda-poehat-v-rossii/aktualnye-novosti",
        "Disallow: /kupit-tur-po-rossii",
        "Disallow: /sdat-oge-i-ege-na-100-ballov",
        "Disallow: /без-рубрики/zolotoe-kolczo-rossii-tury",
        "Disallow: /author/admin",
        "Disallow: /karta-sajta-1",
        # -----------
        "Allow: /",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
