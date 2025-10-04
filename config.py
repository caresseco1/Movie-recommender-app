import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # TMDB Configuration
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'a95f39801011aef66bad6c36ff575757')
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Dataset paths
    DATA_RAW_PATH = "../data/raw/"
    DATA_PROCESSED_PATH = "../data/processed/"
    
    # Model paths
    MODEL_PATH = "../models/"
