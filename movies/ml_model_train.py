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
def train_model(epochs=20, batch_size=256, lr=0.001, embedding_dim=50):
    ratings_csv_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings_small.csv")
    save_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "ml_model_ncf.pth")
    # Load dataset
    data = pd.read_csv(ratings_csv_path)
    data = data.sort_values('timestamp').drop_duplicates(['userId', 'movieId'], keep='last')

    # Map movieId to indices
    data['movie_idx'] = data['movieId'].astype('category').cat.codes
    num_movies = data['movie_idx'].nunique()

    # Train/test split
    train_df, test_df = train_test_split(data, test_size=0.2, random_state=42)
    train_loader = DataLoader(MovieRatingDataset(train_df), batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(MovieRatingDataset(test_df), batch_size=batch_size, shuffle=False)

    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Model, loss, optimizer
    model = NCF(num_movies, embedding_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Training loop
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for movies, ratings in train_loader:
            movies, ratings = movies.to(device), ratings.to(device)
            # Create dummy user embedding (zeros)
            user_emb = torch.zeros((movies.size(0), embedding_dim), device=device)
            optimizer.zero_grad()
            outputs = model(user_emb, movies)
            loss = criterion(outputs, ratings)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * movies.size(0)
        train_loss /= len(train_loader.dataset)
        print(f"Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss:.4f}")

    # Save model
    if save_path is None:
        save_path = os.path.join(os.getcwd(), "ml_model_ncf.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'num_movies': num_movies
    }, save_path)
    print(f"Model saved to {save_path}")

    return model, data



