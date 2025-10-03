from django.utils import timezone

from django.contrib import sitemaps
from django.urls import reverse
from .models import BlogPost, Location, Tag, AboutPage

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.9
    changefreq = 'monthly'

    def items(self):
        return ['blog:home', 'blog:location_root', 'blog:tag_list', 'blog:about_page']

    def location(self, item):
        return reverse(item)

class BlogPostSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.filter(
            is_published=True,
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).order_by('-published_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

class LocationSitemap(sitemaps.Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Location.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

class TagSitemap(sitemaps.Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Tag.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

class AboutPageSitemap(sitemaps.Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        # Только активная версия
        return AboutPage.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('blog:about_page')