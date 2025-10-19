import os
import pandas as pd
import numpy as np
from django.conf import settings
from movies.models import Movie

# Load dataset
ratings_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings_small.csv")
data = pd.read_csv(ratings_path)

data['userId'] = data['userId'].astype(str)

data = data.sort_values(by='timestamp').drop_duplicates(subset=['userId', 'movieId'], keep='last')

# Create user-movie matrix
user_movie_matrix = data.pivot_table(index='userId', columns='movieId', values='rating')
user_movie_matrix.fillna(0, inplace=True)

# Precompute movie vectors for item-based similarity
movie_vectors = user_movie_matrix.T  # movies as rows


def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors"""
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def recommend_movies_from_ratings(user_ratings: dict, top_n=5):
    """
    user_ratings: dict {movieId: rating}
    Returns: list of recommended movieIds
    """
    all_movies = set(movie_vectors.index)
    rated_movies = set(user_ratings.keys())
    candidate_movies = list(all_movies - rated_movies)

    # Calculate predicted score for each candidate movie
    predicted_scores = {}
    for movie_id in candidate_movies:
        sims, weighted_ratings = [], []
        for rated_movie, rating in user_ratings.items():
            if rated_movie not in movie_vectors.index:
                continue
            sim = cosine_similarity(movie_vectors.loc[movie_id].values,
                                    movie_vectors.loc[rated_movie].values)
            sims.append(sim)
            weighted_ratings.append(sim * rating)
        if sims:
            predicted_scores[movie_id] = sum(weighted_ratings) / sum(sims)

    # Sort by predicted score
    recommended = sorted(predicted_scores.items(), key=lambda x: x[1], reverse=True)

    arr= [movie_id for movie_id, _ in recommended[:top_n]]
    return arr



