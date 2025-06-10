import jwt
import uuid
import hashlib
import datetime
from functools import wraps
from flask import request, jsonify, g
from app.database import db, APIToken, User
from app.redis import redis_client

JWT_SECRET = "your-secret-key"

def generate_access_token(user_id, email):
    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def generate_refresh_token():
    return str(uuid.uuid4())

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def generate_api_token(user_id, duration_seconds):
    raw_token = str(uuid.uuid4())
    hashed_token = hash_token(raw_token)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)
    api_token = APIToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at,
        revoked=False
    )
    db.session.add(api_token)
    db.session.commit()
    return raw_token

def validate_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id"), True
    except Exception:
        return None, False

def validate_api_access_token(token):
    hashed_token = hash_token(token)
    api_token = APIToken.query.filter_by(token=hashed_token, revoked=False).first()
    if api_token and api_token.expires_at > datetime.datetime.utcnow():
        return api_token.user_id, True
    return None, False

def auth_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(" ", 1)[1]
        user_id, ok = validate_jwt_token(token)
        if not ok:
            user_id, ok = validate_api_access_token(token)
            if not ok:
                return jsonify({"error": "Unauthorized"}), 401
        g.user_id = user_id
        request.user_id = user_id  # For compatibility with your controllers
        return f(*args, **kwargs)
    return decorated