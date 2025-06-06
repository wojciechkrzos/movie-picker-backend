from rest_framework import serializers
from .models import (
    Film, Actor, Director, Category, Tag, StreamingService, 
    WatchedFilm, FilmTag, FilmStreamingService, FilmCategory, 
    FilmDirector, FilmActor
)


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = '__all__'


class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class StreamingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingService
        fields = '__all__'


class FilmListSerializer(serializers.ModelSerializer):
    """Serializer for film list view with basic information"""
    actors_count = serializers.SerializerMethodField()
    directors_count = serializers.SerializerMethodField()
    categories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Film
        fields = [
            'id', 'title', 'release_date', 'language', 'created_at', 'modified_at',
            'actors_count', 'directors_count', 'categories_count'
        ]
    
    def get_actors_count(self, obj):
        return obj.actors.count()
    
    def get_directors_count(self, obj):
        return obj.directors.count()
    
    def get_categories_count(self, obj):
        return obj.categories.count()


class FilmDetailSerializer(serializers.ModelSerializer):
    """Serializer for film detail view with full information"""
    actors = ActorSerializer(many=True, read_only=True)
    directors = DirectorSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    streaming_services = StreamingServiceSerializer(many=True, read_only=True)
    
    # For creating/updating relationships
    actor_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    director_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    category_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    streaming_service_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    
    class Meta:
        model = Film
        fields = '__all__'
    
    def create(self, validated_data):
        # Extract many-to-many data
        actor_ids = validated_data.pop('actor_ids', [])
        director_ids = validated_data.pop('director_ids', [])
        category_ids = validated_data.pop('category_ids', [])
        tag_ids = validated_data.pop('tag_ids', [])
        streaming_service_ids = validated_data.pop('streaming_service_ids', [])
        
        # Create the film
        film = Film.objects.create(**validated_data)
        
        # Set many-to-many relationships
        if actor_ids:
            film.actors.set(actor_ids)
        if director_ids:
            film.directors.set(director_ids)
        if category_ids:
            film.categories.set(category_ids)
        if tag_ids:
            film.tags.set(tag_ids)
        if streaming_service_ids:
            film.streaming_services.set(streaming_service_ids)
        
        return film
    
    def update(self, instance, validated_data):
        # Extract many-to-many data
        actor_ids = validated_data.pop('actor_ids', None)
        director_ids = validated_data.pop('director_ids', None)
        category_ids = validated_data.pop('category_ids', None)
        tag_ids = validated_data.pop('tag_ids', None)
        streaming_service_ids = validated_data.pop('streaming_service_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships if provided
        if actor_ids is not None:
            instance.actors.set(actor_ids)
        if director_ids is not None:
            instance.directors.set(director_ids)
        if category_ids is not None:
            instance.categories.set(category_ids)
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        if streaming_service_ids is not None:
            instance.streaming_services.set(streaming_service_ids)
        
        return instance


class WatchedFilmSerializer(serializers.ModelSerializer):
    film_title = serializers.CharField(source='film.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = WatchedFilm
        fields = '__all__'
        
    def create(self, validated_data):
        # Automatically set the user to the current authenticated user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WatchedFilmCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating watched films (user is set automatically)"""
    
    class Meta:
        model = WatchedFilm
        fields = ['film', 'review']
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
