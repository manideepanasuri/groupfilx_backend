import csv

from django.db import transaction
from datetime import datetime
import os
import pandas as pd
from movies.models import (
    Movie, Rating, Genre, Keyword, ProductionCompany,
    ProductionCountry, SpokenLanguage
)
from django.conf import settings

DEFAULT_POSTER = ""
DEFAULT_BACKDROP = ""

@transaction.atomic
def update_database():
    """
    Updates the entire database using TMDB + MovieLens datasets.
    Keeps only movies present in both datasets.
    Handles Many-to-Many fields: genres, keywords, production_companies,
    production_countries, spoken_languages.
    """
    # --- Paths ---
    tmdb_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "tmdbmovies.csv")
    movielens_movies_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "movies.csv")
    movielens_links_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "links.csv")


    print("📥 Loading datasets...")
    tmdb_df = pd.read_csv(tmdb_path)
    ml_movies = pd.read_csv(movielens_movies_path)
    ml_links = pd.read_csv(movielens_links_path)


    tmdb_df['id'] = tmdb_df['id'].astype(int)

    # --- Merge MovieLens movies with links ---
    ml_merged = pd.merge(ml_movies, ml_links, on="movieId", how="inner")
    ml_merged = ml_merged.dropna(subset=['tmdbId'])
    ml_merged['tmdbId'] = ml_merged['tmdbId'].astype(int)
    ml_merged = ml_merged[['movieId', 'tmdbId']]

    # --- Merge with TMDB dataset (only common movies) ---
    combined = pd.merge(
        tmdb_df,
        ml_merged,
        left_on='id',
        right_on='tmdbId',
        how='inner',
        suffixes=('_tmdb', '_ml')
    )
    print(combined.head())
    print(f"✅ Found {len(combined)} movies common to both TMDB and MovieLens")

    # --- Clear old data ---
    Movie.objects.all().delete()
    Rating.objects.all().delete()
    Genre.objects.all().delete()
    Keyword.objects.all().delete()
    ProductionCompany.objects.all().delete()
    ProductionCountry.objects.all().delete()
    SpokenLanguage.objects.all().delete()

    # --- Update / Create Movies ---
    for _, row in combined.iterrows():
        try:
            poster = f"https://image.tmdb.org/t/p/original{row.get('poster_path')}" if pd.notna(row.get('poster_path')) else DEFAULT_POSTER
            backdrop = f"https://image.tmdb.org/t/p/original{row.get('backdrop_path')}" if pd.notna(row.get('backdrop_path')) else DEFAULT_BACKDROP

            movie, created = Movie.objects.update_or_create(
                tmdb_id=row["id"],
                defaults={
                    "movieId":row.get("movieId"),
                    "title": row.get("title"),
                    "original_title":row.get("original_title"),
                    "overview": row.get("overview"),
                    "tagline": row.get("tagline"),
                    "status": row.get("status"),
                    "release_date": (
                        datetime.strptime(str(row["release_date"]), "%Y-%m-%d").date()
                        if pd.notna(row.get("release_date")) else None
                    ),
                    "runtime": row.get("runtime"),
                    "revenue": row.get("revenue"),
                    "budget": row.get("budget"),
                    "adult": bool(row.get("adult", False)),
                    "vote_average": row.get("vote_average"),
                    "vote_count": row.get("vote_count"),
                    "popularity": row.get("popularity"),
                    "imdb_id": f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                    "original_language": row.get("original_language"),
                    "poster_path": poster,
                    "backdrop_path": backdrop,
                    "homepage": row.get("homepage"),
                },
            )

            # --- Handle Many-to-Many fields ---
            m2m_fields = {
                "genres": Genre,
                "keywords": Keyword,
                "production_companies": ProductionCompany,
                "production_countries": ProductionCountry,
                "spoken_languages": SpokenLanguage,
            }

            for field_name, model_class in m2m_fields.items():
                items_str = row.get(field_name, "")
                if pd.notna(items_str):
                    items_list = [i.strip() for i in items_str.split(",") if i.strip()]
                    objs = [model_class.objects.get_or_create(name=i)[0] for i in items_list]
                    getattr(movie, field_name).set(objs)

            movie.save()

        except Exception as e:
            print(f"❌ Error saving movie {row.get('title', 'Unknown')}: {e}")

    print("🎬 Movies and related M2M fields updated successfully!")

    print("🎉 Database update complete!")


def export_filtered_ratings():
    """
    Filters MovieLens ratings to include only movies that exist in the Movie table.
    Saves the filtered ratings as a CSV.
    """
    ratings_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "ratings_small.csv")
    output_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings_small.csv")
    print("📥 Loading ratings dataset...")
    ml_ratings = pd.read_csv(ratings_path)
    print(f"Total ratings loaded: {len(ml_ratings)}")

    print("🔍 Getting existing movies from DB...")
    existing_movie_ids = set(Movie.objects.values_list("movieId", flat=True))
    print(f"Movies in DB: {len(existing_movie_ids)}")

    # Convert to string for matching if stored as text
    ml_ratings["movieId"] = ml_ratings["movieId"].astype(str)

    # Filter only ratings of movies that exist
    filtered_ratings = ml_ratings[ml_ratings["movieId"].isin(existing_movie_ids)]

    print(f"✅ Filtered {len(filtered_ratings)} ratings that match existing movies")

    # Save to CSV
    filtered_ratings.to_csv(output_path, index=False)
    print(f"💾 Saved filtered ratings to {output_path}")


from django.db.models import Q

def search_by(search_term:str):

    # 1. Define the search fields (must match your MovieAdmin.search_fields)
    search_fields = ['title', 'original_title', 'overview', 'imdb_id']

    # 2. Build the combined Q object for the 'OR' search logic
    # Django uses __icontains for case-insensitive LIKE searching
    search_query = Q()
    for field in search_fields:
        # Use f-string to construct the lookup: e.g., 'title__icontains'
        kwargs = {f'{field}__icontains': search_term}
        search_query |= Q(**kwargs) # OR the conditions together

    # 3. Execute the query and get the list of primary keys (ids)
    movie_ids = list(
        Movie.objects
        .filter(search_query) # Apply the combined search logic
        .values_list('title', flat=True) # Retrieve only the 'id' field
    )

    # 4. Print the result
    print(movie_ids[:10])
    # Example output: [15, 22, 101, 345, ...]
    return movie_ids[:10]

def write_rating_to_csv(new_row):
    file_path = os.path.join(settings.BASE_DIR, "movielens_dataset", "filtered_ratings_small.csv")
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["userId", "movieId", "rating", "timestamp"])
        writer.writerow(new_row)