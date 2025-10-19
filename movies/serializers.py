# your_app/serializers.py

from rest_framework import serializers
from .models import (
    Genre, Keyword, ProductionCompany, ProductionCountry, SpokenLanguage,
    Movie, Rating
)


# --- Nested Serializers (For M2M Fields) ---

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ['id', 'name']


class ProductionCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionCompany
        fields = ['id', 'name']


class ProductionCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionCountry
        fields = ['id', 'name']


class SpokenLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpokenLanguage
        fields = ['id', 'name']


# ----------------------------------------------------------------------
# 2. Movie Serializer (With Nested M2M Fields)
# ----------------------------------------------------------------------

class MovieSerializer(serializers.ModelSerializer):
    # Use the nested serializers for all Many-to-Many fields
    # many=True is required for M2M fields
    genres = GenreSerializer(many=True, read_only=True)
    keywords = KeywordSerializer(many=True, read_only=True)
    production_companies = ProductionCompanySerializer(many=True, read_only=True)
    production_countries = ProductionCountrySerializer(many=True, read_only=True)
    spoken_languages = SpokenLanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'movieId', 'title', 'original_title', 'overview',
            'tagline', 'status', 'release_date', 'runtime', 'revenue', 'budget',
            'adult', 'vote_average', 'vote_count', 'popularity', 'imdb_id',
            'original_language', 'poster_path', 'backdrop_path', 'homepage',

            # Nested M2M Fields
            'genres', 'keywords', 'production_companies',
            'production_countries', 'spoken_languages',
        ]


# ----------------------------------------------------------------------
# 3. Rating Serializer
# ----------------------------------------------------------------------

class RatingSerializer(serializers.ModelSerializer):
    # Optionally include related fields for context
    # Use StringRelatedField for simple representation (e.g., movie title)
    # movie = serializers.StringRelatedField()

    # Or use PrimaryKeyRelatedField if you only need the ID on the user side
    # user = serializers.PrimaryKeyRelatedField(read_only=True)

    # Or nest the movie serializer for a detailed view:
    # movie_details = MovieSerializer(source='movie', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'movie', 'rating', 'timestamp']

        # Ensures that the user is only read, or explicitly set to the current user in the view
        read_only_fields = ['timestamp']