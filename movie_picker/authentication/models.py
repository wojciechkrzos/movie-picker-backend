# authentication/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, TimestampedModel):
    # Override email field to make it unique and required
    email = models.EmailField(unique=True)

    # Use email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    streaming_services = models.ManyToManyField(
        'movie.StreamingService', through='UserStreamingService', related_name='users')

    def __str__(self):
        return self.email


class UserStreamingService(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    streaming_service = models.ForeignKey('movie.StreamingService', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'streaming_service')


class Question(TimestampedModel):
    question = models.CharField(max_length=255)
    available_answers = models.JSONField()


class Answer(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'question')
