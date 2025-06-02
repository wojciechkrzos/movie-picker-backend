import os
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from movie.models import (
    Film, Actor, Director, Category, Tag, StreamingService,
    FilmActor, FilmDirector, FilmCategory
)

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

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('TMDB_API_KEY')
        self.base_url = 'https://api.themoviedb.org/3' # i think that we should move this to env
        self.image_base_url = 'https://image.tmdb.org/t/p/w500' # i think that we should move this to env
        # for base_url and image_base_url, those aren't used anywhere else but moving them seems to be the correct choice
        # will wait for the review
        
        if not self.api_key:
            raise ValueError("TMDB_API_KEY environment variable is required")

    def handle(self, *args, **options):
        pages = options['pages']
        
        if options['popular']:
            self.stdout.write("Fetching popular movies...")
            self.fetch_movies('popular', pages)
        elif options['top_rated']:
            self.stdout.write("Fetching top rated movies...")
            self.fetch_movies('top_rated', pages)
        else:
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
        if Film.objects.filter(title=movie_data['title']).exists():
            return

        release_date = None
        if movie_data.get('release_date'):
            try:
                release_date = datetime.strptime(movie_data['release_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        film = Film.objects.create(
            title=movie_data['title'],
            release_date=release_date or datetime.now().date(),
            language=movie_data.get('original_language', 'en')
        )

        self.add_movie_details(film, movie_data['id'])
        
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
