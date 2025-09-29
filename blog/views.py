from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils import timezone
from markdownx.views import markdownify_func

from .models import BlogPost, Location


class PostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).select_related('author', 'location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [("Главная", "/")]
        return context


class PostArchiveView(ListView):
    model = BlogPost
    template_name = 'blog/post_archive.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True,
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
        location_path = self.kwargs['location_path']
        slug = self.kwargs['slug']

        # Восстанавливаем локацию по пути
        slug_parts = location_path.split('/')
        try:
            location = Location.objects.get(slug=slug_parts[-1])
            # Проверяем, что полный путь совпадает
            if location.get_path_slug() != location_path:
                raise Location.DoesNotExist
        except Location.DoesNotExist:
            raise BlogPost.DoesNotExist

        return get_object_or_404(
            BlogPost,
            slug=slug,
            location=location,
            is_published=True,
            published_at__lte=timezone.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.object.get_breadcrumbs()
        context["content_markdown_safe"] = markdownify_func(self.object.content_markdown)
        return context


class LocationDetailView(DetailView):
    model = Location
    template_name = 'blog/location_detail.html'
    context_object_name = 'location'

    def get_object(self, queryset=None):
        location_path = self.kwargs['location_path']
        slug_parts = location_path.split('/')
        try:
            location = Location.objects.get(slug=slug_parts[-1])
            if location.get_path_slug() != location_path:
                raise Location.DoesNotExist
        except Location.DoesNotExist:
            raise Location.DoesNotExist("Location not found")
        return location

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Все посты в этой локации И её подлокациях
        descendants = list(self.object.get_descendants())+[self.object]
        context['posts'] = BlogPost.objects.filter(
            location__in=descendants,
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')
        crumbs = [("Главная", "/")]
        location_crumbs = self.object.get_breadcrumbs()
        for loc, url in location_crumbs:
            crumbs.append((loc.name, url))
        context['breadcrumbs'] = crumbs
        return context