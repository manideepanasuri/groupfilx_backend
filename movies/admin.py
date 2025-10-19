from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Genre)
admin.site.register(Keyword)
admin.site.register(ProductionCompany)
admin.site.register(ProductionCountry)
admin.site.register(SpokenLanguage)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    # --- 1. Filter by M2M Fields (genres, keywords, etc.) ---
    # This creates the filter sidebar on the right of the admin list view.
    list_filter = (
        'adult',  # Basic Boolean Field
        'status',  # Basic CharField
        'release_date',  # Basic DateField (provides year/month filters)
        'vote_average',  # Basic FloatField (optional, may not be very useful)
        'genres',  # M2M Field
        'keywords',  # M2M Field
        'production_companies',  # M2M Field
        'production_countries',  # M2M Field
        'spoken_languages',  # M2M Field
    )

    # --- 2. Search by Title ---
    # This enables the search bar at the top of the admin list view.
    # Searching is performed using the SQL LIKE query (usually case-insensitive).
    search_fields = (
        'title',
        'original_title',
        'overview',  # Adding overview for broader search context
        'imdb_id',  # Useful for direct lookup
        'movieId',
    )

    # --- 3. Sorting (Ordering) ---
    # Sets the default sort order for the list view.
    # Use '-' prefix for DESCENDING (e.g., highest vote first).
    ordering = (
        '-vote_average',  # Primary sort: Highest average vote first
        '-vote_count',  # Secondary sort: Highest vote count first (breaks ties)
    )

    # Optional: Fields to display in the list view (for context)
    list_display = (
        'title',
        'release_date',
        'vote_average',
        'vote_count',
        'popularity',
        'id',
        'movieId',
    )
admin.site.register(Rating)
admin.site.register(Comments)