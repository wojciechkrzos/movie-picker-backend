import os
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from movie.models import (
    Film, Actor, Director, Category,
    FilmActor, FilmDirector, FilmCategory, StreamingService, FilmStreamingService
)
from authentication.models import Question

load_dotenv()


class Command(BaseCommand):
    help = "Seed database with movies from TMBD API"

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to fetch from TMDb (default: 5)'
        )
        parser.add_argument(
            '--popular',
            action='store_true',
            help='Fetch popular movies'
        )
        parser.add_argument(
            '--top-rated',
            action='store_true',
            help='Fetch top rated movies'
        )
        parser.add_argument(
            '--questions',
            action='store_true',
            help='Seed quiz questions'
        )
        parser.add_argument(
            '--providers',
            action='store_true',
            help='Fetch streaming providers from TMDb'
        )

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('API_KEY_TMDB')
        self.base_url = os.getenv('TMDB_BASE_URL', 'https://api.themoviedb.org/3')
        self.image_base_url = os.getenv('TMDB_IMAGE_BASE_URL', 'https://image.tmdb.org/t/p/w500')

        if not self.api_key:
            raise ValueError("API_KEY_TMDB environment variable is required")

    def handle(self, *args, **options):
        pages = options['pages']

        if options['providers']:
            self.stdout.write("Fetching streaming providers...")
            self.fetch_streaming_providers()

        if options['questions']:
            self.stdout.write("Seeding quiz questions...")
            self.seed_questions()

        if options['popular']:
            self.stdout.write("Fetching popular movies...")
            self.fetch_movies('popular', pages)
        elif options['top_rated']:
            self.stdout.write("Fetching top rated movies...")
            self.fetch_movies('top_rated', pages)
        elif not options['questions'] and not options['providers']:
            # Only fetch movies if not just seeding questions or providers
            self.stdout.write("Fetching both popular and top rated movies...")
            self.fetch_movies('popular', pages)
            self.fetch_movies('top_rated', pages)

        self.stdout.write(
            self.style.SUCCESS("Database seeding completed successfully!")
        )

    def fetch_movies(self, category, pages):
        """Fetch movies from TMDb API"""
        for page in range(1, pages + 1):
            self.stdout.write(f"Fetching {category} movies - page {page}...")

            url = f"{self.base_url}/movie/{category}"
            params = {
                'api_key': self.api_key,
                'page': page,
                'language': 'en-US'
            }

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                self.process_movies(data['results'])

            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f"Error fetching data: {e}")
                )
                continue

    def process_movies(self, movies):
        """Process and save movies to database"""
        for movie_data in movies:
            try:
                with transaction.atomic():
                    self.create_movie(movie_data)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Error processing movie {movie_data.get('title', 'Unknown')}: {e}")
                )

    def create_movie(self, movie_data):
        """Create movie record with detailed information"""
        tmdb_id = movie_data['id']

        # Check if movie already exists by tmdb_id first, then by title
        if Film.objects.filter(tmdb_id=tmdb_id).exists():
            return
        if Film.objects.filter(title=movie_data['title']).exists():
            return

        # Debug: Print movie data to see what we're receiving
        print(f"DEBUG: Processing movie: {movie_data.get('title', 'Unknown')}")
        print(f"DEBUG: Overview available: {bool(movie_data.get('overview'))}")
        if movie_data.get('overview'):
            print(f"DEBUG: Overview length: {len(movie_data.get('overview', ''))}")
            print(f"DEBUG: Overview preview: {movie_data.get('overview', '')[:100]}...")
        else:
            print("DEBUG: No overview in movie_data")

        release_date = None
        if movie_data.get('release_date'):
            try:
                release_date = datetime.strptime(movie_data['release_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        overview_text = movie_data.get('overview', '')
        print(f"DEBUG: Creating film with overview: {bool(overview_text)}")

        # Construct poster URL
        poster_url = None
        if movie_data.get('poster_path'):
            poster_url = f"{self.image_base_url}{movie_data['poster_path']}"
            print(f"DEBUG: Poster URL: {poster_url}")

        film = Film.objects.create(
            title=movie_data['title'],
            release_date=release_date or datetime.now().date(),
            language=movie_data.get('original_language', 'en'),
            overview=overview_text,
            poster_url=poster_url,
            tmdb_id=tmdb_id
        )

        print(f"DEBUG: Film created. Overview in DB: {bool(film.overview)}")
        print(f"DEBUG: Film created. Poster URL in DB: {bool(film.poster_url)}")

        self.add_movie_details(film, tmdb_id)

        self.add_movie_streaming_providers(film, tmdb_id)

        if movie_data.get('genre_ids'):
            self.add_genres(film, movie_data['genre_ids'])

        self.stdout.write(f"Created movie: {film.title}")

    def add_movie_details(self, film, tmdb_id):
        """Fetch and add detailed movie information"""
        url = f"{self.base_url}/movie/{tmdb_id}"
        params = {
            'api_key': self.api_key,
            'append_to_response': 'credits'
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'credits' in data and 'cast' in data['credits']:
                self.add_cast(film, data['credits']['cast'][:10])  # limit is here

            if 'credits' in data and 'crew' in data['credits']:
                self.add_directors(film, data['credits']['crew'])

        except requests.RequestException as e:
            self.stdout.write(
                self.style.WARNING(f"Error fetching details for {film.title}: {e}")
            )

    def add_cast(self, film, cast_data):
        """Add actors to the film"""
        for actor_data in cast_data:
            if not actor_data.get('name'):
                continue

            name_parts = actor_data['name'].split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            actor, created = Actor.objects.get_or_create(
                first_name=first_name,
                last_name=last_name
            )

            FilmActor.objects.get_or_create(film=film, actor=actor)

    def add_directors(self, film, crew_data):
        """Add directors to the film"""
        directors = [person for person in crew_data if person.get('job') == 'Director']

        for director_data in directors:
            if not director_data.get('name'):
                continue

            name_parts = director_data['name'].split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            director, created = Director.objects.get_or_create(
                first_name=first_name,
                last_name=last_name
            )

            FilmDirector.objects.get_or_create(film=film, director=director)

    def add_genres(self, film, genre_ids):
        """Add genres as categories"""
        # genre mapping from tmdb, not sure if this shouldn't be stored externally
        genre_map = {
            28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
            80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
            14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
            9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
            10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
        }

        for genre_id in genre_ids:
            if genre_id in genre_map:
                category, created = Category.objects.get_or_create(
                    name=genre_map[genre_id]
                )
                FilmCategory.objects.get_or_create(film=film, category=category)

    def seed_questions(self):
        """Add predefined quiz questions to the database"""
        questions_data = [
            {
                'question': "What's your mood today?",
                'available_answers': ["Energetic", "Bored", "Chill", "Jittery"]
            },
            {
                'question': "What type of movie do you prefer?",
                'available_answers': ["Action-packed", "Emotional", "Mind-bending", "Light-hearted"]
            },
            {
                'question': "What's your favorite time period for movies?",
                'available_answers': [
                    "Classic (before 1980)", "Retro (1980-2000)",
                    "Modern (2000-2015)", "Recent (2015+)"
                ]
            },
            {
                'question': "How do you prefer to watch movies?",
                'available_answers': ["Alone for focus", "With friends for fun", "Date night romance", "Family time"]
            },
            {
                'question': "What movie length do you prefer?",
                'available_answers': [
                    "Short and sweet (under 90 min)", "Standard length (90-120 min)",
                    "Epic length (over 2 hours)", "No preference"
                ]
            },
            {
                'question': "What draws you to a movie most?",
                'available_answers': ["Amazing visuals", "Great storyline", "Favorite actors", "Director's reputation"]
            }
        ]

        for question_data in questions_data:
            question, created = Question.objects.get_or_create(
                question=question_data['question'],
                defaults={'available_answers': question_data['available_answers']}
            )

            if created:
                self.stdout.write(f"Created question: {question.question}")
            else:
                self.stdout.write(f"Question already exists: {question.question}")

    def fetch_streaming_providers(self):
        """Fetch streaming providers from TMDb API"""
        url = f"{self.base_url}/watch/providers/movie"
        params = {
            'api_key': self.api_key,
            'watch_region': 'US'  # for now only US, we can change this later
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'results' in data:
                self.process_streaming_providers(data['results'])
            else:
                self.stdout.write(
                    self.style.WARNING("No streaming providers found in response")
                )

        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f"Error fetching streaming providers: {e}")
            )

    def process_streaming_providers(self, providers):
        """Process and save streaming providers to database"""
        for provider_data in providers:
            try:
                with transaction.atomic():
                    self.create_streaming_provider(provider_data)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Error processing provider "
                        f"{provider_data.get('provider_name', 'Unknown')}: {e}"
                    )
                )

    def create_streaming_provider(self, provider_data):
        """Create streaming provider record"""
        tmdb_provider_id = provider_data['provider_id']

        if StreamingService.objects.filter(tmdb_provider_id=tmdb_provider_id).exists():
            return

        logo_url = None
        if provider_data.get('logo_path'):
            logo_url = f"{self.image_base_url}{provider_data['logo_path']}"

        provider = StreamingService.objects.create(
            name=provider_data['provider_name'],
            tmdb_provider_id=tmdb_provider_id,
            logo_path=logo_url
        )

        self.stdout.write(f"Created streaming provider: {provider.name}")

    def add_movie_streaming_providers(self, film, tmdb_id):
        """Fetch and add streaming providers for a specific movie"""
        url = f"{self.base_url}/movie/{tmdb_id}/watch/providers"
        params = {
            'api_key': self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'results' in data and 'US' in data['results']:
                us_providers = data['results']['US']

                all_providers = []

                if 'flatrate' in us_providers:
                    all_providers.extend(us_providers['flatrate'])

                if 'rent' in us_providers:
                    all_providers.extend(us_providers['rent'])

                if 'buy' in us_providers:
                    all_providers.extend(us_providers['buy'])

                for provider_data in all_providers:
                    self.link_movie_to_provider(film, provider_data)

        except requests.RequestException as e:
            self.stdout.write(
                self.style.WARNING(f"Error fetching streaming providers for {film.title}: {e}")
            )

    def link_movie_to_provider(self, film, provider_data):
        """Link a movie to a streaming provider"""
        tmdb_provider_id = provider_data['provider_id']

        try:
            streaming_service = StreamingService.objects.get(tmdb_provider_id=tmdb_provider_id)

            FilmStreamingService.objects.get_or_create(
                film=film,
                streaming_service=streaming_service
            )

        except StreamingService.DoesNotExist:
            logo_url = None
            if provider_data.get('logo_path'):
                logo_url = f"{self.image_base_url}{provider_data['logo_path']}"

            streaming_service = StreamingService.objects.create(
                name=provider_data['provider_name'],
                tmdb_provider_id=tmdb_provider_id,
                logo_path=logo_url
            )

            FilmStreamingService.objects.get_or_create(
                film=film,
                streaming_service=streaming_service
            )
