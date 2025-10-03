from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from blog.sitemaps import StaticViewSitemap, BlogPostSitemap, LocationSitemap, TagSitemap, AboutPageSitemap
from blog.views import robots_txt
from kazan import settings

sitemaps = {
    'static': StaticViewSitemap,
    'posts': BlogPostSitemap,
    'locations': LocationSitemap,
    'tags': TagSitemap,
    'about': AboutPageSitemap,
}

urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),
    path('', include('blog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)