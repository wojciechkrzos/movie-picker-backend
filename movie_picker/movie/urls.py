# movie/urls.py
from django.urls import path
from . import views

app_name = 'movie'

urlpatterns = [
    path('films/', views.FilmListCreateView.as_view(), name='film-list-create'),
    path('films/<int:pk>/', views.FilmDetailView.as_view(), name='film-detail'),

    path('actors/', views.ActorListCreateView.as_view(), name='actor-list-create'),
    path('actors/<int:pk>/', views.ActorDetailView.as_view(), name='actor-detail'),

    path('directors/', views.DirectorListCreateView.as_view(), name='director-list-create'),
    path('directors/<int:pk>/', views.DirectorDetailView.as_view(), name='director-detail'),

    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    path('tags/', views.TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag-detail'),

    path('streaming-services/', views.StreamingServiceListCreateView.as_view(), name='streaming-service-list-create'),
    path('streaming-services/<int:pk>/', views.StreamingServiceDetailView.as_view(), name='streaming-service-detail'),

    path('watched/', views.WatchedFilmListCreateView.as_view(), name='watched-film-list-create'),
    path('watched/<int:pk>/', views.WatchedFilmDetailView.as_view(), name='watched-film-detail'),

    path('my-films/', views.MyWatchedFilmsView.as_view(), name='my-watched-films'),
    path('recommendations/', views.RecommendedFilmsView.as_view(), name='film-recommendations'),
    path('my-stats/', views.user_stats, name='user-stats'),
]
