from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import uuid
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# In-memory user storage (replace with database in production)
users_db = {}

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        password = data.get('password', '')
        username = data.get('username', '')
        
        # Validation
        if not email or not password or not username:
            return jsonify({"error": "All fields are required"}), 400
        
        if email in users_db:
            return jsonify({"error": "User already exists"}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        users_db[email] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now().isoformat(),
            'preferences': {
                'favorite_genres': [],
                'watch_history': []
            }
        }
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "username": username,
                "email": email
            },
            "access_token": access_token
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        user = users_db.get(email)
        if not user or not bcrypt.check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create access token
        access_token = create_access_token(identity=user['id'])
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            },
            "access_token": access_token
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        
        # Find user by ID
        user = next((u for u in users_db.values() if u['id'] == user_id), None)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "created_at": user['created_at'],
                "preferences": user['preferences']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
