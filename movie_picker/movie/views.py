from rest_framework import generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg
from .models import (
    Film, Actor, Director, Category, Tag, StreamingService,
    WatchedFilm
)
from .serializers import (
    FilmListSerializer, FilmDetailSerializer, ActorSerializer,
    DirectorSerializer, CategorySerializer, TagSerializer,
    StreamingServiceSerializer, WatchedFilmSerializer,
    WatchedFilmCreateSerializer
)
from django.http import JsonResponse
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework import status


# FILM VIEWS
class FilmListCreateView(generics.ListCreateAPIView):
    """
    GET: List all films (public access)
    POST: Create a new film (requires authentication)
    """
    queryset = Film.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['release_date', 'language', 'tmdb_id']
    search_fields = ['title', 'actors__first_name', 'actors__last_name',
                     'directors__first_name', 'directors__last_name']
    ordering_fields = ['title', 'release_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FilmListSerializer
        return FilmDetailSerializer


class FilmDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific film (public access)
    PUT/PATCH: Update a film (requires authentication)
    DELETE: Delete a film (requires authentication)
    """
    queryset = Film.objects.all()
    serializer_class = FilmDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ACTOR VIEWS
class ActorListCreateView(generics.ListCreateAPIView):
    """List all actors or create a new actor"""
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['first_name', 'last_name', 'birthdate']
    ordering = ['last_name', 'first_name']


class ActorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an actor"""
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# DIRECTOR VIEWS
class DirectorListCreateView(generics.ListCreateAPIView):
    """List all directors or create a new director"""
    queryset = Director.objects.all()
    serializer_class = DirectorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['first_name', 'last_name', 'birthdate']
    ordering = ['last_name', 'first_name']


class DirectorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a director"""
    queryset = Director.objects.all()
    serializer_class = DirectorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# CATEGORY VIEWS
class CategoryListCreateView(generics.ListCreateAPIView):
    """List all categories or create a new category"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# TAG VIEWS
class TagListCreateView(generics.ListCreateAPIView):
    """List all tags or create a new tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# STREAMING SERVICE VIEWS
class StreamingServiceListCreateView(generics.ListCreateAPIView):
    """List all streaming services or create a new streaming service"""
    queryset = StreamingService.objects.all()
    serializer_class = StreamingServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tmdb_provider_id']
    search_fields = ['name']
    ordering = ['name']


class StreamingServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a streaming service"""
    queryset = StreamingService.objects.all()
    serializer_class = StreamingServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# WATCHED FILMS VIEWS (User-specific, requires authentication)
class WatchedFilmListCreateView(generics.ListCreateAPIView):
    """
    GET: List watched films for the authenticated user
    POST: Mark a film as watched for the authenticated user
    """
    serializer_class = WatchedFilmSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'review']
    ordering = ['-created_at']

    def get_queryset(self):
        # Only return watched films for the current user
        return WatchedFilm.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WatchedFilmCreateSerializer
        return WatchedFilmSerializer


class WatchedFilmDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific watched film for the authenticated user
    PUT/PATCH: Update review for a watched film
    DELETE: Remove film from watched list
    """
    serializer_class = WatchedFilmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchedFilm.objects.filter(user=self.request.user)


# USER-SPECIFIC VIEWS
class MyWatchedFilmsView(generics.ListAPIView):
    """Get all films watched by the authenticated user with detailed information"""
    serializer_class = FilmDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        watched_films = WatchedFilm.objects.filter(user=self.request.user).values_list('film_id', flat=True)
        return Film.objects.filter(id__in=watched_films)


class RecommendedFilmsView(APIView):
    """
    Get film recommendations based on user's streaming services and preferences
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_streaming_services = user.streaming_services.all()

        available_films = Film.objects.filter(
            streaming_services__in=user_streaming_services
        ).distinct()

        watched_film_ids = WatchedFilm.objects.filter(
            user=user
        ).values_list('film_id', flat=True)

        recommended_films = available_films.exclude(id__in=watched_film_ids)

        # RECOMMENDATION LOGIC HERE

        serializer = FilmListSerializer(recommended_films[:20], many=True)
        return Response({
            'message': f'Recommendations based on your {user_streaming_services.count()} streaming services',
            'streaming_services': [service.name for service in user_streaming_services],
            'recommendations': serializer.data
        })


class APIRootView(View):
    """
    API Root endpoint that provides information about available endpoints
    """
    def get(self, request):
        return JsonResponse({
            "message": "Welcome to Movie Picker API",
            "version": "1.0",
            "endpoints": {
                "authentication": {
                    "login": "/login/",
                    "admin": "/admin/",
                    "api_auth": "/api/v1/auth/",
                    "google_login": "/api/v1/auth/google/",
                    "google_callback": "/api/v1/auth/google/callback/"
                }
            },
            "status": "active"
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Get statistics for the authenticated user"""
    user = request.user

    watched_count = WatchedFilm.objects.filter(user=user).count()
    reviewed_count = WatchedFilm.objects.filter(user=user, review__isnull=False).count()
    streaming_services_count = user.streaming_services.count()

    reviews = WatchedFilm.objects.filter(user=user, review__isnull=False)
    avg_review = reviews.aggregate(avg=Avg('review'))['avg'] if reviews.exists() else None

    return Response({
        'username': user.username,
        'watched_films_count': watched_count,
        'reviewed_films_count': reviewed_count,
        'streaming_services_count': streaming_services_count,
        'average_review_score': round(avg_review, 2) if avg_review else None,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint - publicly accessible
    """
    return Response({
        "status": "healthy",
        "message": "Movie Picker API is running"
    }, status=status.HTTP_200_OK)
