# I love tests by Claude 4.0 <3

from django.test import TestCase
from django.core.management import call_command
from django.db import IntegrityError
from datetime import date
from unittest.mock import patch, MagicMock

from .models import (
    Film, Actor, Director, Category, Tag, StreamingService,
    FilmActor, FilmDirector, FilmCategory, WatchedFilm
)
from authentication.models import User


class MovieModelsTest(TestCase):
    """Test basic functionality of movie models"""

    def setUp(self):
        """Set up test data"""
        self.actor = Actor.objects.create(
            first_name="Tom",
            last_name="Hanks",
            birthdate=date(1956, 7, 9)
        )

        self.director = Director.objects.create(
            first_name="Steven",
            last_name="Spielberg",
            birthdate=date(1946, 12, 18)
        )

        self.category = Category.objects.create(name="Drama")
        self.tag = Tag.objects.create(name="Oscar Winner")
        self.streaming_service = StreamingService.objects.create(name="Netflix")

        self.film = Film.objects.create(
            title="Forrest Gump",
            release_date=date(1994, 7, 6),
            language="en"
        )

    def test_film_creation(self):
        """Test that films are created correctly"""
        self.assertEqual(self.film.title, "Forrest Gump")
        self.assertEqual(self.film.release_date, date(1994, 7, 6))
        self.assertEqual(self.film.language, "en")
        self.assertEqual(str(self.film), "Forrest Gump")

    def test_actor_creation(self):
        """Test that actors are created correctly"""
        self.assertEqual(self.actor.first_name, "Tom")
        self.assertEqual(self.actor.last_name, "Hanks")
        self.assertEqual(self.actor.birthdate, date(1956, 7, 9))

    def test_director_creation(self):
        """Test that directors are created correctly"""
        self.assertEqual(self.director.first_name, "Steven")
        self.assertEqual(self.director.last_name, "Spielberg")
        self.assertEqual(self.director.birthdate, date(1946, 12, 18))

    def test_film_actor_relationship(self):
        """Test many-to-many relationship between films and actors"""
        FilmActor.objects.create(film=self.film, actor=self.actor)

        self.assertIn(self.actor, self.film.actors.all())
        self.assertEqual(self.film.actors.count(), 1)

        with self.assertRaises(IntegrityError):
            FilmActor.objects.create(film=self.film, actor=self.actor)

    def test_film_director_relationship(self):
        """Test many-to-many relationship between films and directors"""
        FilmDirector.objects.create(film=self.film, director=self.director)

        self.assertIn(self.director, self.film.directors.all())
        self.assertEqual(self.film.directors.count(), 1)

    def test_film_category_relationship(self):
        """Test many-to-many relationship between films and categories"""
        FilmCategory.objects.create(film=self.film, category=self.category)

        self.assertIn(self.category, self.film.categories.all())
        self.assertEqual(self.film.categories.count(), 1)

    def test_timestamped_model_fields(self):
        """Test that timestamp fields are automatically populated"""
        self.assertIsNotNone(self.film.created_at)
        self.assertIsNotNone(self.film.modified_at)
        self.assertIsNotNone(self.actor.created_at)
        self.assertIsNotNone(self.director.created_at)


class MovieSeedCommandTest(TestCase):
    """Test the database seeding command"""

    @patch('movie.management.commands.db_seed.requests.get')
    def test_db_seed_command_with_mock_data(self, mock_get):
        """Test the db_seed command with mocked API responses"""

        # TODO: Configure
        mock_movie_response = MagicMock()
        mock_movie_response.json.return_value = {
            'results': [
                {
                    'id': 123,
                    'title': 'Test Movie',
                    'release_date': '2023-01-01',
                    'original_language': 'en',
                    'genre_ids': [28, 12]  # Action, Adventure
                }
            ]
        }
        mock_movie_response.raise_for_status.return_value = None

        # TODO: configure
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {
            'credits': {
                'cast': [
                    {'name': 'Test Actor', 'id': 1},
                    {'name': 'Another Actor', 'id': 2}
                ],
                'crew': [
                    {'name': 'Test Director', 'job': 'Director', 'id': 3}
                ]
            }
        }
        mock_detail_response.raise_for_status.return_value = None

        # TODO: configure
        def mock_requests_get(url, params=None):
            if 'movie/popular' in url:
                return mock_movie_response
            elif 'movie/123' in url:
                return mock_detail_response
            return mock_movie_response

        mock_get.side_effect = mock_requests_get

        try:
            with patch.dict('os.environ', {'TMDB_API_KEY': 'test_key'}):
                call_command('db_seed', '--popular', '--pages', '1', verbosity=0)
        except Exception as e:
            self.fail(f"db_seed command raised an exception: {e}")

        # check if data created
        self.assertTrue(Film.objects.filter(title='Test Movie').exists())
        self.assertTrue(Actor.objects.filter(first_name='Test').exists())
        self.assertTrue(Director.objects.filter(first_name='Test').exists())
        self.assertTrue(Category.objects.filter(name='Action').exists())

    def test_db_seed_command_help(self):
        """Test that the command help works"""
        try:
            with patch.dict('os.environ', {'TMDB_API_KEY': 'test_key'}):
                call_command('db_seed', '--help')
        except SystemExit:
            pass

    def test_db_seed_without_api_key(self):
        """Test that command fails gracefully without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                call_command('db_seed', '--popular', '--pages', '1')


class WatchedFilmTest(TestCase):
    """Test the WatchedFilm model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.film = Film.objects.create(
            title="Test Film",
            release_date=date(2023, 1, 1),
            language="en"
        )

    def test_watched_film_creation(self):
        """Test creating a watched film record"""
        watched = WatchedFilm.objects.create(
            film=self.film,
            user=self.user,
            review=8
        )

        self.assertEqual(watched.film, self.film)
        self.assertEqual(watched.user, self.user)
        self.assertEqual(watched.review, 8)

    def test_watched_film_unique_constraint(self):
        """Test that a user can't watch the same film twice"""
        WatchedFilm.objects.create(film=self.film, user=self.user, review=8)

        with self.assertRaises(IntegrityError):
            WatchedFilm.objects.create(film=self.film, user=self.user, review=9)
