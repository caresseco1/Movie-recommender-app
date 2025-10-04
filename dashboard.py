from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from data import movies_df, ratings_df, users_db
import pandas as pd

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        user_id = get_jwt_identity()
        
        # User-specific stats
        user_ratings = [r for r in ratings_db if r.get('userId') == user_id]
        total_ratings = len(user_ratings)
        avg_rating = sum(r.get('rating', 0) for r in user_ratings) / total_ratings if total_ratings > 0 else 0
        
        # Global stats
        total_movies = len(movies_df) if movies_df is not None else 0
        total_users = len(users_db)
        total_reviews = len(ratings_db)
        
        return jsonify({
            "user_stats": {
                "total_ratings": total_ratings,
                "average_rating": round(avg_rating, 2)
            },
            "global_stats": {
                "total_movies": total_movies,
                "total_users": total_users,
                "total_reviews": total_reviews
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_user_activity():
    """Get user activity history"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's recent ratings
        user_ratings = sorted(
            [r for r in ratings_db if r.get('userId') == user_id],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]  # Last 10
        
        activity = []
        for rating in user_ratings:
            movie = movies_df[movies_df['movieId'] == rating.get('movieId')] if movies_df is not None else pd.DataFrame()
            movie_title = movie['title'].iloc[0] if not movie.empty else "Unknown Movie"
            
            activity.append({
                'type': 'rating',
                'movie_id': rating.get('movieId'),
                'movie_title': movie_title,
                'rating': rating.get('rating'),
                'timestamp': rating.get('timestamp')
            })
        
        return jsonify(activity), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
