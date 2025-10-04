import pandas as pd
import numpy as np
from models.ncf_model import NCFModel
from models.content_model import ContentBasedModel
from models.hybrid_engine import HybridRecommender

def train_recommendation_models():
    print("🚀 Starting model training...")

    # Load processed data
    movies_df = pd.read_csv('../data/processed/movies_final.csv')
    ratings_df = pd.read_csv('../data/processed/ratings_clean.csv')

    print(f"📊 Training data: {len(ratings_df):,} ratings")

    # Prepare data for NCF
    user_ids = ratings_df['userId'].values
    movie_ids = ratings_df['movieId'].values
    ratings = ratings_df['rating'].values

    # Create user and movie mappings
    unique_users = ratings_df['userId'].unique()
    unique_movies = ratings_df['movieId'].unique()

    user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
    movie_to_idx = {movie: idx for idx, movie in enumerate(unique_movies)}

    # Convert to indices
    user_indices = np.array([user_to_idx[user] for user in user_ids])
    movie_indices = np.array([movie_to_idx[movie] for movie in movie_ids])

    # Train NCF Model
    print("🧠 Training Neural Collaborative Filtering model...")
    ncf_model = NCFModel(
        num_users=len(unique_users),
        num_movies=len(unique_movies),
        embedding_dim=64
    )

    ncf_model.train(user_indices, movie_indices, ratings, epochs=5)

    # Train Content-Based Model
    print("📝 Training content-based model...")
    content_model = ContentBasedModel()
    content_model.prepare_content_features(movies_df)

    # Create Hybrid Recommender
    print("🔗 Creating hybrid recommender...")
    hybrid_recommender = HybridRecommender(ncf_model, content_model, movies_df)

    # Save models
    print("💾 Saving models...")
    ncf_model.model.save('./models/ncf_model.h5')

    # Save mappings
    import pickle
    with open('./models/user_mappings.pkl', 'wb') as f:
        pickle.dump({'user_to_idx': user_to_idx, 'movie_to_idx': movie_to_idx}, f)

    print("✅ Model training completed!")
    return hybrid_recommender

if __name__ == "__main__":
    recommender = train_recommendation_models()
