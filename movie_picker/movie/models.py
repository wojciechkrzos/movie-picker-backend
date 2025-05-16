# movie/models.py
from django.db import models
from django.utils import timezone
from authentication.models import User

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Film(TimestampedModel):
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    language = models.CharField(max_length=255)

    actors = models.ManyToManyField('Actor', through='FilmActor')
    directors = models.ManyToManyField('Director', through='FilmDirector')
    categories = models.ManyToManyField('Category', through='FilmCategory')
    tags = models.ManyToManyField('Tag', through='FilmTag')
    streaming_services = models.ManyToManyField('StreamingService', through='FilmStreamingService')

    def __str__(self):
        return self.title

class Actor(TimestampedModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birthdate = models.DateField(null=True, blank=True)

class Director(TimestampedModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birthdate = models.DateField(null=True, blank=True)

class Category(TimestampedModel):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('id', 'name')

class Tag(TimestampedModel):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('id', 'name')

class StreamingService(TimestampedModel):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('id', 'name')

class WatchedFilm(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('film', 'user')

class FilmTag(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('film', 'tag')

class FilmStreamingService(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    streaming_service = models.ForeignKey(StreamingService, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('film', 'streaming_service')

class FilmCategory(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('film', 'category')

class FilmDirector(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('film', 'director')

class FilmActor(TimestampedModel):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('film', 'actor')
