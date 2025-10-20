import os
import torch
import pandas as pd
from django.conf import settings
from .ml_model_train import NCF
from .models import Movie


# ---- Load trained model ----
def load_model(model_path):
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
    num_movies = checkpoint['num_movies']
    model = NCF(num_movies)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model, num_movies

ratings_csv_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings.csv")
model_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "ml_model_ncf_full.pth")

# Load model
model, _ = load_model(model_path)

# Load dataset to build movie index map
data = pd.read_csv(ratings_csv_path)
data = data.sort_values('timestamp').drop_duplicates(['userId', 'movieId'], keep='last')
data['movie_idx'] = data['movieId'].astype('category').cat.codes
movie_id_map = dict(zip(data['movieId'], data['movie_idx']))
# ---- Recommendation function ----
def recommend_movies(user_ratings_dict, top_n=10):
    """
    user_ratings_dict: {movieId: rating} for a new user
    """
    # --- Filter out unseen movies from input ---
    valid_rated = {m: r for m, r in user_ratings_dict.items() if m in movie_id_map}
    if not valid_rated:
        raise ValueError("No valid rated movies found in dataset.")

    rated_movie_ids = [movie_id_map[m] for m in valid_rated.keys()]
    ratings_tensor = torch.FloatTensor(list(valid_rated.values()))
    movie_tensor = torch.LongTensor(rated_movie_ids)

    # --- Build user embedding ---
    with torch.no_grad():
        movie_emb = model.movie_embedding(movie_tensor)
        user_emb = (movie_emb * ratings_tensor.unsqueeze(1)).mean(dim=0, keepdim=True)

    # --- Build candidate list ---
    candidate_movies = [m for m in movie_id_map.keys() if m not in valid_rated]
    candidate_idx = []
    for m in candidate_movies:
        if m not in movie_id_map:
            continue  # unseen movie → skip
        candidate_idx.append(movie_id_map[m])

    if not candidate_idx:
        print("No unseen movies to recommend.")
        return []

    candidate_idx = torch.LongTensor(candidate_idx)

    # --- Predict scores ---
    with torch.no_grad():
        predictions = model(user_emb.repeat(len(candidate_idx), 1), candidate_idx).numpy()

    # --- Sort and display top-N ---
    top_idx = predictions.argsort()[-top_n:][::-1]
    top_movie_ids = [candidate_movies[i] for i in top_idx]

    print("🎬 Top Recommendations:")
    for i in top_idx:
        mid = candidate_movies[i]
        score = predictions[i]
        try:
            m = Movie.objects.get(movieId=mid)
            print(f"{m.title} : {score:.3f}")
        except Movie.DoesNotExist:
            print(f"MovieID {mid} : {score:.3f} (not in DB)")

    return top_movie_ids
