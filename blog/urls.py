from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),          # Главная
    path('posts/', views.PostArchiveView.as_view(), name='post_archive'),  # Архив
    path('<path:location_path>/', views.LocationDetailView.as_view(), name='location_detail'),
    path('<path:location_path>/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
]