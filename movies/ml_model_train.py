import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from django.conf import settings


# ---- Dataset ----
class MovieRatingDataset(Dataset):
    def __init__(self, df):
        self.movies = torch.LongTensor(df['movie_idx'].values)
        self.ratings = torch.FloatTensor(df['rating'].values)

    def __len__(self):
        return len(self.ratings)

    def __getitem__(self, idx):
        return self.movies[idx], self.ratings[idx]


# ---- Neural Collaborative Filtering Model ----
class NCF(nn.Module):
    def __init__(self, num_movies, embedding_dim=50):
        super(NCF, self).__init__()
        self.movie_embedding = nn.Embedding(num_movies, embedding_dim)
        self.fc_layers = nn.Sequential(
            nn.Linear(embedding_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, user_emb, movie_ids):
        movie_emb = self.movie_embedding(movie_ids)
        x = torch.cat([user_emb, movie_emb], dim=1)
        return self.fc_layers(x).squeeze()


# ---- Training Function ----
def train_model(epochs=20, batch_size=256, lr=0.005, embedding_dim=50):
    ratings_csv_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings.csv")
    save_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "ml_model_ncf_full.pth")

    # --- Load dataset safely ---
    # Read only the needed columns
    cols = ['userId', 'movieId', 'rating', 'timestamp']
    try:
        data = pd.read_csv(ratings_csv_path, usecols=cols)
    except Exception as e:
        print("Error reading CSV:", e)
        return None, None
    print("csv reading completed")
    # Drop duplicate ratings for the same user/movie (keep latest)
    #data = data.sort_values('timestamp').drop_duplicates(['userId', 'movieId'], keep='last')

    # Map movieId to indices
    data['movie_idx'] = data['movieId'].astype('category').cat.codes
    num_movies = data['movie_idx'].nunique()
    print("num_movies", num_movies)
    # Train/test split
    train_loader = DataLoader(MovieRatingDataset(data), batch_size=batch_size, shuffle=True)

    print("loding completed")
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Model, loss, optimizer
    model = NCF(num_movies, embedding_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    print("starting training")
    # Training loop
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        count=0
        for movies, ratings in train_loader:
            movies, ratings = movies.to(device), ratings.to(device)
            user_emb = torch.zeros((movies.size(0), embedding_dim), device=device)
            optimizer.zero_grad()
            outputs = model(user_emb, movies)
            loss = criterion(outputs, ratings)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * movies.size(0)
            count+=1
            if count % 1000 == 0:
                print("training loss: ", train_loss)
        train_loss /= len(train_loader.dataset)
        print(f"Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss:.4f}")

    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'num_movies': num_movies
    }, save_path)
    print(f"Model saved to {save_path}")

    return model, data
