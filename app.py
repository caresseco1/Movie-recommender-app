from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import Config
from data import users_db, movies_df, ratings_df, tmdb_service

# Import routes
from routes.auth import auth_bp
from routes.movies import movies_bp
from routes.recommendations import recommendations_bp
from routes.reviews import reviews_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(movies_bp, url_prefix='/api/movies')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

# Basic routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/contact', methods=['POST'])
def contact_support():
    data = request.get_json()
    name = data.get('name', '')
    email = data.get('email', '')
    message = data.get('message', '')
    
    # In production, save to database or send email
    print(f"Contact form: {name} ({email}) - {message}")
    
    return jsonify({
        "success": True,
        "message": "Thank you for your message! We'll get back to you soon."
    })

import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")

@app.route('/api/welcome', methods=['GET'])
def welcome():
    logger.info(f"Welcome endpoint accessed: {request.method} {request.path}")
    return jsonify({"message": "Welcome to the Movie Recommender API!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
