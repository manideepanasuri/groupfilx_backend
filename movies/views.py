import random

from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.ml_model import recommend_movies
from movies.models import *
from users.models import CustomUser
from .helpers import write_rating_to_csv
from .serializers import *


# Create your views here.

class Recommendation(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        ratings = Rating.objects.filter(user=user)

        # Case 1: Not enough ratings (less than 3)
        if ratings.count() < 3:
            # Get top 50 movies sorted by rating
            top_movies = list(Movie.objects.order_by('-popularity')[:50])

            # Randomly select 5
            recommended_movies = random.sample(top_movies, min(5, len(top_movies)))

            # Serialize
            serializer = MovieSerializer(recommended_movies, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Case 2: Enough ratings, use recommendation model
        user_ratings = {int(r.movie.movieId): r.rating for r in ratings}
        recommended_ids = recommend_movies(user_ratings, 50)

        recommended_ids_sample = random.sample(recommended_ids, min(5, len(recommended_ids)))
        #recommended_ids_sample = recommended_ids[:5]
        movies = Movie.objects.filter(movieId__in=recommended_ids_sample)
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework import generics
from rest_framework import filters
from .models import Movie
from .serializers import MovieSerializer, GenreSerializer
from .filters import MovieFilter  # Import your custom filter


from rest_framework.pagination import LimitOffsetPagination

class SmallPagination(LimitOffsetPagination):
    default_limit = 20   # default number of results
    max_limit = 100      # prevent abuse via very high limits


class MovieListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Movie.objects.all().distinct()  # .distinct() is important for M2M filtering
    serializer_class = MovieSerializer

    # --- 1. Filter by M2M Fields (using django-filter) ---
    filterset_class = MovieFilter

    # --- 2. Search by Title (Replicating search_fields) ---
    search_fields = (
        '=imdb_id',  # Exact match for imdb_id (Admin is case-insensitive, this is common for IDs)
        'title',  # Contains search
        'original_title',
        'overview',
    )

    # --- 3. Sorting (Replicating ordering) ---
    ordering_fields = [
        'vote_average',
        'vote_count',
        'popularity',
        'release_date',
        # Any other field you want the user to be able to sort by
    ]
    # Set the default ordering (Replicating ordering = ('-vote_average', '-vote_count'))
    ordering = ['-vote_average', '-vote_count']

    pagination_class = SmallPagination


class AddRatingView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        movie_id = request.data['movie_id']
        rating = request.data['rating']
        if int(rating)>5 or int(rating)<1:
            return Response({'message': 'Invalid rating'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            movie = Movie.objects.get(id=movie_id)
            user = request.user

            if Rating.objects.filter(user=user, movie=movie).exists() :
                Rating.objects.filter(user=user, movie=movie).update(rating=rating)
            else:
                Rating.objects.create(user=user, movie=movie, rating=rating)
            return Response({'message': 'Rating added successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        rating_id = request.data['rating_id']
        if not Rating.objects.filter(id=rating_id).exists() :
            return Response({'message': 'Invalid Query'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            Rating.objects.filter(id=rating_id).delete()
            return Response({'message': 'Rating deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AddCommentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        movie_id = request.data['movie_id']
        comment = request.data['comment']
        if len(comment)<2:
            return Response({'message': 'Invalid comment'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            movie = Movie.objects.get(id=movie_id)
            user = request.user
            Comments.objects.create(movie=movie, user=user, comment=comment)
            return Response({'message': 'Rating added successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        comment_id = request.data['comment_id']
        if not Comments.objects.filter(id=comment_id).exists():
            return Response({'message': 'Invalid Query'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            Comments.objects.filter(id=comment_id).delete()
            return Response({'message': 'Rating deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetAllGenresView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        try:
            genres = Genre.objects.all()
            data = GenreSerializer(genres, many=True).data
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AllMovieDetailsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        try:
            user=request.user
            movie_id=request.data['movie_id']
            movie = Movie.objects.get(id=movie_id)
            data=MovieSerializer2(movie).data
            if Rating.objects.filter(user=user, movie=movie).exists():
                rating=Rating.objects.get(user=user, movie=movie)
                data["rating"]=rating.rating
            else:
                data["rating"]=0
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)