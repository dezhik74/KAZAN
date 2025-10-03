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

    # Лучшие, популярные посты
    path('best/', views.BestPostsView.as_view(), name='best_posts'),
    path('popular/', views.PopularPostsView.as_view(), name='popular_posts'),

    # О нас
    path('about/', views.AboutPageView.as_view(), name='about_page'),

    # Оценка поста
    path('post_rate/<int:post_id>/', views.PostRatingView.as_view(), name='post_rate'),
]