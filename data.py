import pandas as pd
import numpy as np
import os
from config import Config

# Global variables (in production, use a database)
users_db = {}
ratings_db = []

# Load datasets
try:
    movies_df = pd.read_csv('../data/processed/movies_final.csv')
    print(f"✅ Loaded {len(movies_df)} movies")
except:
    print("❌ Could not load movies data")
    movies_df = pd.DataFrame()

try:
    ratings_df = pd.read_csv('../data/processed/ratings_clean.csv')
    print(f"✅ Loaded {len(ratings_df)} ratings")
except:
    print("❌ Could not load ratings data")
    ratings_df = pd.DataFrame()

# TMDB Service
class TMDBService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = Config.TMDB_BASE_URL

    def get_trending_movies(self):
        """Get trending movies from TMDB"""
        import requests
        try:
            response = requests.get(
                f"{self.base_url}/trending/movie/week",
                params={"api_key": self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()['results'][:20]
            return []
        except:
            return []

tmdb_service = TMDBService(Config.TMDB_API_KEY)
