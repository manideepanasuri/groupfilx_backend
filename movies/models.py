
from django.db import models

from users.models import CustomUser
from csv import writer

User=CustomUser
# --- Normalized Tables ---
class Genre(models.Model):
    name = models.CharField(max_length=1000, unique=True)

    def __str__(self):
        return self.name

class Keyword(models.Model):
    name = models.CharField(max_length=1000, unique=True)

    def __str__(self):
        return self.name

class ProductionCompany(models.Model):
    name = models.CharField(max_length=2000, unique=True)

    def __str__(self):
        return self.name

class ProductionCountry(models.Model):
    name = models.CharField(max_length=2000, unique=True)

    def __str__(self):
        return self.name

class SpokenLanguage(models.Model):
    name = models.CharField(max_length=1000, unique=True)

    def __str__(self):
        return self.name

# --- Movie Table ---
class Movie(models.Model):
    tmdb_id = models.BigIntegerField(unique=True)
    movieId = models.IntegerField(null=True, blank=True)  # from MovieLens
    title = models.CharField(max_length=5000)
    original_title = models.CharField(max_length=5000, null=True, blank=True)
    overview = models.TextField(null=True, blank=True)
    tagline = models.CharField(max_length=5000, null=True, blank=True)
    status = models.CharField(max_length=500, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)
    revenue = models.BigIntegerField(null=True, blank=True)
    budget = models.BigIntegerField(null=True, blank=True)
    adult = models.BooleanField(default=False)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)
    imdb_id = models.CharField(max_length=200, null=True, blank=True)
    original_language = models.CharField(max_length=10, null=True, blank=True)
    poster_path = models.URLField( null=True, blank=True)
    backdrop_path = models.URLField( null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)

    # --- Many-to-Many Relationships ---
    genres = models.ManyToManyField(Genre, related_name='movies')
    keywords = models.ManyToManyField(Keyword, related_name='movies')
    production_companies = models.ManyToManyField(ProductionCompany, related_name='movies')
    production_countries = models.ManyToManyField(ProductionCountry, related_name='movies')
    spoken_languages = models.ManyToManyField(SpokenLanguage, related_name='movies')

    def __str__(self):
        return self.title


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='ratings',null=False,blank=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings',null=False,blank=False)
    rating = models.FloatField()
    timestamp = models.DateTimeField(null=True, blank=True,auto_now=True)

    def __str__(self):
        return f"{self.user} → {self.movie.title} ({self.rating})"

class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='comments',null=False,blank=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments',null=False,blank=False)
    text=models.TextField()
    timestamp = models.DateTimeField(null=True, blank=True,auto_now=True)

    def __str__(self):
        return f"{self.user} → {self.movie.title} )"

