from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import pandas as pd
from data import movies_df, ratings_df
# from app import recommender  # TODO: implement recommender

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get personalized movie recommendations"""
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 10))
        
        # For now, return trending movies as recommendations
        # In production, use the recommender model
        recommendations = []
        if not movies_df.empty:
            # Simple recommendation: top rated movies
            top_movies = movies_df.nlargest(limit, 'vote_average')
            for _, movie in top_movies.iterrows():
                recommendations.append({
                    'id': movie.get('id'),
                    'title': movie.get('title', ''),
                    'overview': movie.get('overview', ''),
                    'poster_path': movie.get('poster_path', ''),
                    'vote_average': movie.get('vote_average', 0),
                    'genres': movie.get('genres', [])
                })
        
        return jsonify(recommendations), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommendations_bp.route('/similar/<int:movie_id>', methods=['GET'])
def get_similar_movies(movie_id):
    """Get movies similar to the given movie"""
    try:
        # Find the movie
        movie = movies_df[movies_df['id'] == movie_id]
        if movie.empty:
            return jsonify({"error": "Movie not found"}), 404
        
        movie_data = movie.iloc[0]
        genres = movie_data.get('genres', [])
        
        # Find movies with similar genres
        similar_movies = movies_df[
            movies_df['genres'].apply(
                lambda x: any(g in genres for g in x) if isinstance(x, list) and genres else False
            )
        ].head(10)
        
        formatted_movies = []
        for _, sim_movie in similar_movies.iterrows():
            if sim_movie['id'] != movie_id:
                formatted_movies.append({
                    'id': sim_movie.get('id'),
                    'title': sim_movie.get('title', ''),
                    'overview': sim_movie.get('overview', ''),
                    'poster_path': sim_movie.get('poster_path', ''),
                    'vote_average': sim_movie.get('vote_average', 0),
                    'genres': sim_movie.get('genres', [])
                })
        
        return jsonify(formatted_movies), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
