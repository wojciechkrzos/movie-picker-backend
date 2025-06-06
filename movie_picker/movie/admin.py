from django.contrib import admin
from .models import (
    Film, Actor, Director, Category, Tag, StreamingService,
    WatchedFilm, FilmTag, FilmStreamingService, FilmCategory,
    FilmDirector, FilmActor
)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'birthdate', 'created_at']
    list_filter = ['created_at', 'birthdate']
    search_fields = ['first_name', 'last_name']
    ordering = ['last_name', 'first_name']


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'birthdate', 'created_at']
    list_filter = ['created_at', 'birthdate']
    search_fields = ['first_name', 'last_name']
    ordering = ['last_name', 'first_name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(StreamingService)
class StreamingServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


class FilmActorInline(admin.TabularInline):
    model = FilmActor
    extra = 1


class FilmDirectorInline(admin.TabularInline):
    model = FilmDirector
    extra = 1


class FilmCategoryInline(admin.TabularInline):
    model = FilmCategory
    extra = 1


class FilmTagInline(admin.TabularInline):
    model = FilmTag
    extra = 1


class FilmStreamingServiceInline(admin.TabularInline):
    model = FilmStreamingService
    extra = 1


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_date', 'language', 'created_at']
    list_filter = ['release_date', 'language', 'created_at', 'categories', 'streaming_services']
    search_fields = ['title', 'actors__first_name', 'actors__last_name', 'directors__first_name', 'directors__last_name']
    ordering = ['-created_at']
    date_hierarchy = 'release_date'
    
    inlines = [
        FilmActorInline,
        FilmDirectorInline,
        FilmCategoryInline,
        FilmTagInline,
        FilmStreamingServiceInline,
    ]


@admin.register(WatchedFilm)
class WatchedFilmAdmin(admin.ModelAdmin):
    list_display = ['user', 'film', 'review', 'created_at']
    list_filter = ['review', 'created_at', 'film__release_date']
    search_fields = ['user__username', 'user__email', 'film__title']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'film']
