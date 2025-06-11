from flask import Blueprint, request, jsonify, redirect
from redis import Redis
from requests_oauthlib import OAuth2Session
import logging
from app.database import db, Tenant, User, APIToken, assign_user_role
from app.tokens import generate_access_token, generate_refresh_token, generate_api_token

bp = Blueprint('auth', __name__, url_prefix='/auth')

redis_client = Redis()
logging.basicConfig(level=logging.INFO)

ctx = None  # Not needed in Python, but kept for similarity
DefaultConfigTenant = None

@bp.route('/login', methods=['GET'])
def login():
    """OAuth2 login endpoint"""
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    tenant = Tenant.query.filter_by(domain=domain).first()
    if not tenant:
        tenant = DefaultConfigTenant

    oauth2_session = OAuth2Session(
        client_id=tenant.client_id,
        client_secret=tenant.client_secret,
        redirect_uri=f"http://localhost:8080/auth/callback?domain={tenant.domain}",
        scope=["openid", "profile", "email"]
    )
    authorization_url, state = oauth2_session.authorization_url(tenant.auth_url)
    return redirect(authorization_url)

@bp.route('/callback', methods=['GET'])
def callback():
    """OAuth2 callback handler"""
    domain = request.args.get('domain')
    code = request.args.get('code')
    
    tenant = Tenant.query.filter_by(domain=domain).first()
    if not tenant:
        tenant = DefaultConfigTenant
    oauth2_session = OAuth2Session(
        client_id=tenant.client_id,
        client_secret=tenant.client_secret,
        redirect_uri=f"http://localhost:8080/auth/callback?domain={tenant.domain}",
        scope=["openid", "profile", "email"]
    )
    
    try:
        token = oauth2_session.fetch_token(
            tenant.token_url,
            client_id=tenant.client_id,
            client_secret=tenant.client_secret,
            code=code
        )

        resp = oauth2_session.get(tenant.userinfo_url)
        user_info = resp.json()
        
        # Create or update user
        user = User.query.filter_by(email=user_info.get("email")).first()
        if not user:
            user = User(
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture", "")
            )
            db.session.add(user)
            db.session.commit()
            assign_user_role(user.id, "Member")
        
        # Generate tokens
        access_token = generate_access_token(user.id, user.email)
        refresh_token = generate_refresh_token()
        
        # Store refresh token in Redis
        key = f"refresh:{refresh_token}"
        redis_client.setex(key, 30 * 24 * 3600, f"{user.id}:{user.email}")
        
        return jsonify({
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600
        })
        
    except Exception as e:
        logging.error(f"OAuth error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 401

@bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    refresh_token = request.json.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    key = f"refresh:{refresh_token}"
    data = redis_client.get(key)
    if not data:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    user_id, user_email = data.decode().split(":", 1)
    new_access_token = generate_access_token(user_id, user_email)
    
    return jsonify({
        "access_token": new_access_token,
        "expires_in": 3600
    })

@bp.route('/logout', methods=['POST'])
def logout():
    """Logout and invalidate refresh token"""
    refresh_token = request.json.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    key = f"refresh:{refresh_token}"
    redis_client.delete(key)
    return jsonify({"message": "Logged out successfully"})