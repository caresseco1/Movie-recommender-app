from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from data import movies_df, tmdb_service

movies_bp = Blueprint('movies', __name__)

@movies_bp.route('/trending', methods=['GET'])
def get_trending_movies():
    """Get trending movies from TMDB"""
    try:
        trending_movies = tmdb_service.get_trending_movies()
        
        # Format response
        formatted_movies = []
        for movie in trending_movies:
            formatted_movies.append({
                'id': movie['id'],
                'title': movie.get('title', ''),
                'overview': movie.get('overview', ''),
                'poster_path': f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}",
                'release_date': movie.get('release_date', ''),
                'vote_average': movie.get('vote_average', 0),
                'vote_count': movie.get('vote_count', 0),
                'popularity': movie.get('popularity', 0)
            })
        
        return jsonify(formatted_movies), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@movies_bp.route('/', methods=['GET'])
def get_all_movies():
    """Get all movies from dataset with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        movies_slice = movies_df.iloc[start_idx:end_idx]
        
        formatted_movies = []
        for _, movie in movies_slice.iterrows():
            formatted_movies.append(format_movie_response(movie))
        
        return jsonify({
            "movies": formatted_movies,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(movies_df),
                "total_pages": (len(movies_df) + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@movies_bp.route('/search', methods=['GET'])
def search_movies():
    """Search movies by title, genre, actor, or year"""
    try:
        query = request.args.get('q', '').lower()
        genre = request.args.get('genre', '')
        year = request.args.get('year', '')
        actor = request.args.get('actor', '').lower()
        
        filtered_movies = movies_df.copy()
        
        # Text search in title and overview
        if query:
            filtered_movies = filtered_movies[
                filtered_movies['title'].str.lower().str.contains(query, na=False) |
                filtered_movies['overview'].str.lower().str.contains(query, na=False)
            ]
        
        # Genre filter
        if genre:
            filtered_movies = filtered_movies[
                filtered_movies['genres'].apply(
                    lambda x: genre.lower() in ' '.join(x).lower() if isinstance(x, list) else False
                )
            ]
        
        # Year filter
        if year:
            filtered_movies = filtered_movies[
                filtered_movies['release_year'] == int(year)
            ]
        
        # Actor filter
        if actor:
            filtered_movies = filtered_movies[
                filtered_movies['cast'].apply(
                    lambda x: actor in ' '.join(x).lower() if isinstance(x, list) else False
                )
            ]
        
        formatted_movies = []
        for _, movie in filtered_movies.head(100).iterrows():  # Limit results
            formatted_movies.append(format_movie_response(movie))
        
        return jsonify(formatted_movies), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@movies_bp.route('/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """Get detailed information for a specific movie"""
    try:
        movie = movies_df[movies_df['movieId'] == movie_id]
        if movie.empty:
            return jsonify({"error": "Movie not found"}), 404
        
        movie_data = movie.iloc[0]
        detailed_response = format_movie_response(movie_data)
        
        # Add additional details
        detailed_response.update({
            'runtime': movie_data.get('runtime', 0),
            'director': movie_data.get('director', ''),
            'cast': movie_data.get('cast', []),
            'keywords': movie_data.get('keywords', []),
            'production_companies': movie_data.get('production_companies', [])
        })
        
        return jsonify(detailed_response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def format_movie_response(movie):
    """Format movie data for API response"""
    return {
        'movieId': movie.get('movieId'),
        'id': movie.get('id'),
        'title': movie.get('title', ''),
        'overview': movie.get('overview', ''),
        'poster_path': f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}" if movie.get('poster_path') else '',
        'release_date': movie.get('release_date', ''),
        'release_year': movie.get('release_year'),
        'vote_average': movie.get('vote_average', 0),
        'vote_count': movie.get('vote_count', 0),
        'popularity': movie.get('popularity', 0),
        'genres': movie.get('genres', [])
    }
