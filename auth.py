from functools import wraps
from flask import request, jsonify
from config import AUTHORIZED_USERS

def authenticate(f):
    """Decorator for authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or AUTHORIZED_USERS.get(auth.username) != auth.password:
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function
