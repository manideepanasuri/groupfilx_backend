import os
import torch
import pandas as pd
from django.conf import settings
from .ml_model_train import NCF
from .models import Movie

# ------------------ Configuration ------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"⚙️ Using device: {device}")

# ------------------ Load model ------------------
def load_model(model_path):
    checkpoint = torch.load(model_path, map_location=device)
    num_movies = checkpoint["num_movies"]
    model = NCF(num_movies)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, num_movies




# ------------------ Recommend function ------------------
def recommend_movies(user_ratings_dict, top_n=10, batch_size=2000):
    """
    Recommend movies for a new user based on their {movieId: rating} history.
    """
    # ------------------ Preload dataset ------------------
    ratings_csv_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings_small.csv")
    model_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "ml_model_ncf.pth")

    # Load CSV once (keep in memory)
    print("📂 Loading dataset...")
    data = pd.read_csv(ratings_csv_path)
    data = data.sort_values("timestamp").drop_duplicates(["userId", "movieId"], keep="last")
    data["movie_idx"] = data["movieId"].astype("category").cat.codes
    movie_id_map = dict(zip(data["movieId"], data["movie_idx"]))
    print(f"✅ Loaded {len(movie_id_map)} unique movies")

    # Load model once
    model, _ = load_model(model_path)
    print("✅ Model loaded successfully!")

    # Filter out unseen movies

    valid_rated = {m: r for m, r in user_ratings_dict.items() if m in movie_id_map}
    if not valid_rated:
        raise ValueError("No valid rated movies found in dataset.")

    rated_movie_ids = [movie_id_map[m] for m in valid_rated.keys()]
    ratings_tensor = torch.FloatTensor(list(valid_rated.values())).to(device)
    movie_tensor = torch.LongTensor(rated_movie_ids).to(device)

    # Build user embedding
    with torch.no_grad():
        movie_emb = model.movie_embedding(movie_tensor)
        user_emb = (movie_emb * ratings_tensor.unsqueeze(1)).mean(dim=0, keepdim=True)

    # Build candidate list
    candidate_movies = [m for m in movie_id_map.keys() if m not in valid_rated]
    candidate_idx = torch.LongTensor([movie_id_map[m] for m in candidate_movies]).to(device)

    predictions = []
    model.eval()

    # Batched prediction for memory safety
    print(f"🔮 Predicting scores for {len(candidate_idx)} movies (batch={batch_size})...")
    with torch.no_grad():
        for i in range(0, len(candidate_idx), batch_size):
            batch = candidate_idx[i : i + batch_size]
            preds = model(user_emb.repeat(len(batch), 1), batch)
            predictions.append(preds.cpu())
    predictions = torch.cat(predictions).numpy()

    # Sort and select top-N
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
