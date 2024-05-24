from rest_framework import serializers
from .models import Query, Movie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['movie_id', 'movie_name', 'movie_type', 'movie_actors']

class QuerySerializer(serializers.ModelSerializer):
    movies = MovieSerializer(many=True, read_only=True)

    class Meta:
        model = Query
        fields = ['id', 'queryTitle']
