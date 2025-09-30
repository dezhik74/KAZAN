# blog/urls.py

from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Главная — список последних постов
    path('', views.PostListView.as_view(), name='home'),

    # Локации
    path('location/', views.RootLocationListView.as_view(), name='location_root'),
    path('location/<path:location_path>/', views.LocationDetailView.as_view(), name='location_detail'),

    # Посты
    path('post/', views.PostArchiveView.as_view(), name='post_archive'),
    path('post/<path:location_path>/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),

    # Теги
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tag/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
]