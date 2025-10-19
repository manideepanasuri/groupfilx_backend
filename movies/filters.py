# D:\Acadamics\3rd year 1st sem\seproject\backend\movies\filters.py

import django_filters
from .models import *


class MovieFilter(django_filters.FilterSet):
    genres = django_filters.ModelMultipleChoiceFilter(
        # CORRECT: Use the object manager of the related model (Genre)
        queryset=Genre.objects.all(),
        field_name='genres',

    )
    keywords = django_filters.ModelMultipleChoiceFilter(
        # CORRECT: Use the object manager of the related model (Keyword)
        queryset=Keyword.objects.all(),
        field_name='keywords',
    )
    production_companies = django_filters.ModelMultipleChoiceFilter(
        # CORRECT: Use the object manager of the related model
        queryset=ProductionCompany.objects.all(),
        field_name='production_companies',
    )
    production_countries = django_filters.ModelMultipleChoiceFilter(
        # CORRECT: Use the object manager of the related model
        queryset=ProductionCountry.objects.all(),
        field_name='production_countries',
    )
    spoken_languages = django_filters.ModelMultipleChoiceFilter(
        # CORRECT: Use the object manager of the related model
        queryset=SpokenLanguage.objects.all(),
        field_name='spoken_languages',
    )

    release_date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Movie
        fields = [
            'adult',
            'status',
            'vote_average',
            'genres',
            'keywords',
            'production_companies',
            'production_countries',
            'spoken_languages',
            'release_date'
        ]