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
    WatchedFilmCreateSerializer, WatchedFilmWithDetailsSerializer
)
from django.http import JsonResponse
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework import status
from authentication.models import Answer
import random


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
        return WatchedFilmWithDetailsSerializer


class WatchedFilmDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific watched film for the authenticated user
    PUT/PATCH: Update review for a watched film
    DELETE: Remove film from watched list
    """
    serializer_class = WatchedFilmWithDetailsSerializer
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

        # Get user's streaming services
        user_streaming_services = user.streaming_services.all()

        if not user_streaming_services.exists():
            return Response({
                'message': 'Please select your streaming services first to get recommendations',
                'streaming_services': [],
                'recommendations': []
            })

        # Get films available on user's streaming services
        available_films = Film.objects.filter(
            streaming_services__in=user_streaming_services
        ).distinct()

        # Exclude already watched films
        watched_film_ids = WatchedFilm.objects.filter(
            user=user
        ).values_list('film_id', flat=True)

        recommended_films = available_films.exclude(id__in=watched_film_ids)

        # RECOMMENDATION LOGIC
        recommended_films = self._apply_recommendation_logic(user, recommended_films)

        # Limit to top 5 recommendations
        final_recommendations = recommended_films[:5]

        serializer = FilmListSerializer(final_recommendations, many=True)
        streaming_count = user_streaming_services.count()
        message = f'Recommendations based on your {streaming_count} streaming services and preferences'
        return Response({
            'message': message,
            'streaming_services': [service.name for service in user_streaming_services],
            'recommendations': serializer.data
        })

    def _apply_recommendation_logic(self, user, films_queryset):
        """
        Apply sophisticated recommendation logic based on:
        1. User's quiz answers
        2. User's review history (highly rated films)
        3. Popular films among similar users
        4. Variety in recommendations
        """
        # Get user's quiz answers
        user_answers = Answer.objects.filter(user=user).select_related('question')

        # Create preference weights based on quiz answers
        category_weights = self._get_category_weights_from_quiz(user_answers)

        # Get user's review preferences
        review_preferences = self._get_review_preferences(user)

        # Score films based on multiple factors
        scored_films = []

        for film in films_queryset.prefetch_related('categories', 'actors', 'directors'):
            score = self._calculate_film_score(film, category_weights, review_preferences, user)
            scored_films.append((film, score))

        # Sort by score (highest first) and return films
        scored_films.sort(key=lambda x: x[1], reverse=True)

        # Add some randomization to avoid always showing the same films
        top_films = [film for film, score in scored_films[:40]]
        random.shuffle(top_films[:10])  # Shuffle only the top 10 to maintain quality

        return top_films

    def _get_category_weights_from_quiz(self, user_answers):
        """
        Map quiz answers to film category preferences
        """
        category_weights = {
            'Action': 0,
            'Comedy': 0,
            'Drama': 0,
            'Horror': 0,
            'Romance': 0,
            'Science Fiction': 0,
            'Thriller': 0,
            'Animation': 0,
            'Documentary': 0,
            'Fantasy': 0,
            'Adventure': 0,
            'Crime': 0,
            'Mystery': 0
        }

        for answer in user_answers:
            question_text = answer.question.question.lower()
            answer_text = answer.answer.lower()

            # Map mood-based answers to categories
            if "mood" in question_text:
                if answer_text == "energetic":
                    category_weights['Action'] += 3
                    category_weights['Adventure'] += 3
                    category_weights['Thriller'] += 2
                elif answer_text == "bored":
                    category_weights['Comedy'] += 3
                    category_weights['Action'] += 2
                    category_weights['Adventure'] += 2
                elif answer_text == "chill":
                    category_weights['Romance'] += 3
                    category_weights['Drama'] += 2
                    category_weights['Documentary'] += 1
                elif answer_text == "jittery":
                    category_weights['Horror'] += 3
                    category_weights['Thriller'] += 3
                    category_weights['Mystery'] += 2

            # Map preference-based answers to categories
            elif "type of movie" in question_text or "prefer" in question_text:
                if answer_text == "action-packed":
                    category_weights['Action'] += 4
                    category_weights['Adventure'] += 3
                    category_weights['Thriller'] += 2
                elif answer_text == "emotional":
                    category_weights['Drama'] += 4
                    category_weights['Romance'] += 3
                elif answer_text == "mind-bending":
                    category_weights['Science Fiction'] += 4
                    category_weights['Thriller'] += 2
                    category_weights['Mystery'] += 2
                elif answer_text == "light-hearted":
                    category_weights['Comedy'] += 4
                    category_weights['Animation'] += 2
                    category_weights['Romance'] += 1

            # Map viewing context to categories
            elif "how do you prefer to watch" in question_text:
                if "alone for focus" in answer_text:
                    category_weights['Drama'] += 2
                    category_weights['Documentary'] += 2
                    category_weights['Thriller'] += 1
                elif "with friends for fun" in answer_text:
                    category_weights['Comedy'] += 3
                    category_weights['Action'] += 2
                    category_weights['Horror'] += 1
                elif "date night romance" in answer_text:
                    category_weights['Romance'] += 4
                    category_weights['Comedy'] += 1
                elif "family time" in answer_text:
                    category_weights['Animation'] += 3
                    category_weights['Adventure'] += 2
                    category_weights['Comedy'] += 2

            # Map what draws to movie preferences
            elif "what draws you" in question_text:
                if "amazing visuals" in answer_text:
                    category_weights['Science Fiction'] += 3
                    category_weights['Fantasy'] += 3
                    category_weights['Action'] += 2
                    category_weights['Animation'] += 2
                elif "great storyline" in answer_text:
                    category_weights['Drama'] += 3
                    category_weights['Mystery'] += 2
                    category_weights['Thriller'] += 2
                elif "favorite actors" in answer_text:
                    # This will be handled in actor-based scoring
                    pass
                elif "director's reputation" in answer_text:
                    # This will be handled in director-based scoring
                    pass

        return category_weights

    def _get_review_preferences(self, user):
        """
        Analyze user's review history to understand preferences
        """
        highly_rated_films = WatchedFilm.objects.filter(
            user=user,
            review__gte=4
        ).select_related('film').prefetch_related('film__categories', 'film__actors', 'film__directors')

        # Get categories, actors, and directors from highly rated films
        preferred_categories = []
        preferred_actors = []
        preferred_directors = []

        for watched in highly_rated_films:
            film = watched.film
            preferred_categories.extend([cat.name for cat in film.categories.all()])
            preferred_actors.extend([f"{actor.first_name} {actor.last_name}" for actor in film.actors.all()])
            preferred_directors.extend([f"{dir.first_name} {dir.last_name}" for dir in film.directors.all()])

        return {
            'categories': preferred_categories,
            'actors': preferred_actors,
            'directors': preferred_directors,
            'avg_rating': WatchedFilm.objects.filter(user=user, review__isnull=False).aggregate(
                avg=Avg('review')
            )['avg'] or 0
        }

    def _calculate_film_score(self, film, category_weights, review_preferences, user):
        """
        Calculate a recommendation score for a film based on various factors
        """
        score = 0

        # Category-based scoring from quiz answers
        film_categories = [cat.name for cat in film.categories.all()]
        for category in film_categories:
            if category in category_weights:
                score += category_weights[category] * 10

        # Boost score based on user's review history preferences
        for category in film_categories:
            if category in review_preferences['categories']:
                # Count how many times this category appears in user's highly rated films
                category_frequency = review_preferences['categories'].count(category)
                score += category_frequency * 15

        # Actor-based scoring
        film_actors = [f"{actor.first_name} {actor.last_name}" for actor in film.actors.all()]
        for actor in film_actors:
            if actor in review_preferences['actors']:
                actor_frequency = review_preferences['actors'].count(actor)
                score += actor_frequency * 20

        # Director-based scoring
        film_directors = [f"{dir.first_name} {dir.last_name}" for dir in film.directors.all()]
        for director in film_directors:
            if director in review_preferences['directors']:
                director_frequency = review_preferences['directors'].count(director)
                score += director_frequency * 25

        # Time period preferences from quiz
        time_period_preference = self._get_time_period_preference(user)
        if time_period_preference and film.release_date:
            release_year = film.release_date.year
            if time_period_preference == "classic" and release_year < 1980:
                score += 15
            elif time_period_preference == "retro" and 1980 <= release_year < 2000:
                score += 15
            elif time_period_preference == "modern" and 2000 <= release_year < 2015:
                score += 15
            elif time_period_preference == "recent" and release_year >= 2015:
                score += 15

        # Add some base scoring to ensure variety
        score += random.randint(1, 10)

        # Boost newer films slightly for users with no time preference (encourage discovering recent content)
        if not time_period_preference and film.release_date and film.release_date.year >= 2020:
            score += 5

        return score

    def _get_time_period_preference(self, user):
        """
        Get user's time period preference from quiz answers
        """
        try:
            time_answer = Answer.objects.filter(
                user=user,
                question__question__icontains="time period"
            ).first()

            if time_answer:
                answer_text = time_answer.answer.lower()
                if "classic" in answer_text:
                    return "classic"
                elif "retro" in answer_text:
                    return "retro"
                elif "modern" in answer_text:
                    return "modern"
                elif "recent" in answer_text:
                    return "recent"
        except Exception:
            pass

        return None


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
