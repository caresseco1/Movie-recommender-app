from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from data import ratings_db
import uuid
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/<int:movie_id>', methods=['GET'])
def get_movie_reviews(movie_id):
    """Get reviews for a specific movie"""
    try:
        movie_reviews = [r for r in ratings_db if r.get('movieId') == movie_id]
        
        formatted_reviews = []
        for review in movie_reviews:
            formatted_reviews.append({
                'id': review.get('id'),
                'user_id': review.get('userId'),
                'movie_id': review.get('movieId'),
                'rating': review.get('rating'),
                'timestamp': review.get('timestamp'),
                'review_text': review.get('review_text', '')
            })
        
        return jsonify(formatted_reviews), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reviews_bp.route('/<int:movie_id>', methods=['POST'])
@jwt_required()
def add_movie_review(movie_id):
    """Add a review for a movie"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        rating = data.get('rating')
        review_text = data.get('review_text', '')
        
        if not rating or not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        # Create review
        review_id = str(uuid.uuid4())
        review = {
            'id': review_id,
            'userId': user_id,
            'movieId': movie_id,
            'rating': rating,
            'timestamp': datetime.now().isoformat(),
            'review_text': review_text
        }
        
        ratings_db.append(review)
        
        return jsonify({
            "success": True,
            "message": "Review added successfully",
            "review": review
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@reviews_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_reviews():
    """Get reviews by the current user"""
    try:
        user_id = get_jwt_identity()
        user_reviews = [r for r in ratings_db if r.get('userId') == user_id]
        
        return jsonify(user_reviews), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
