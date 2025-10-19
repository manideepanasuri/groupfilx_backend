from django.urls import path

from movies.views import *
from users.views import UserAuthSignupView

urlpatterns = [
    path('recomendations/', Recommendation.as_view(), name='recommendations'),
    path('query/',MovieListView.as_view(), name='query'),
    path('rating/',AddRatingView.as_view(), name='rating'),
    path('comment/',AddCommentView.as_view(), name='comment'),
    path('genres/', GetAllGenresView.as_view(), name='genres'),
    path('getmovie/', AllMovieDetailsView.as_view(), name='getmovie'),
]