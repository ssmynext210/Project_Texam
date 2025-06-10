from flask import Blueprint, request, jsonify, redirect
from redis import Redis
from requests_oauthlib import OAuth2Session
import requests
import json
import time
import logging
from app.database import db, Tenant, User, APIToken, assign_user_role

bp = Blueprint('auth', __name__)

redis_client = Redis()
logging.basicConfig(level=logging.INFO)

# Placeholder for context and models
ctx = None  # Not needed in Python, but kept for similarity
DefaultConfigTenant = None  # Should be set to your default tenant config

# Models: Tenant, User, APIToken should be defined elsewhere

def handle_login():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    tenant = Tenant.query.filter_by(domain=domain).first()
    if not tenant:
        tenant = DefaultConfigTenant

    oauth2_session = OAuth2Session(
        client_id=tenant.client_id,
        client_secret=tenant.client_secret,
        redirect_uri=f"http://localhost:8080/callback?domain={tenant.domain}",
        scope=["openid", "profile", "email"]
    )
    authorization_url, state = oauth2_session.authorization_url(tenant.auth_url)
    return redirect(authorization_url)

def handle_callback():
    domain = request.args.get('domain')
    code = request.args.get('code')

    tenant = Tenant.query.filter_by(domain=domain).first()
    if not tenant:
        tenant = DefaultConfigTenant

    oauth2_session = OAuth2Session(
        client_id=tenant.client_id,
        client_secret=tenant.client_secret,
        redirect_uri=f"http://localhost:8080/callback?domain={tenant.domain}",
        scope=["openid", "profile", "email"]
    )
    token = oauth2_session.fetch_token(
        tenant.token_url,
        client_secret=tenant.client_secret,
        code=code
    )

    resp = oauth2_session.get(tenant.userinfo_url)
    user_info = resp.json()
    logging.info(user_info)

    user_email = user_info.get("email")
    user_picture = user_info.get("picture", "")

    user = User.query.filter_by(email=user_email).first()
    if not user:
        user = User(
            email=user_email,
            name=user_info.get("name"),
            picture=user_picture
        )
        db.session.add(user)
        db.session.commit()
        if tenant.domain != "default":
            assign_user_role(user.id, tenant.id, "Member")
    else:
        if user.picture:
            user_picture = user.picture
        user.name = user_info.get("name")
        user.picture = user_picture
        db.session.commit()

    access_token = generate_access_token(user.id, user.email)
    if not access_token:
        return jsonify({"error": "Failed to generate JWT"}), 500

    refresh_token = generate_refresh_token()
    key = f"refresh:{refresh_token}"
    redis_client.setex(key, 30 * 24 * 3600, f"{user.id}:{user.email}")

    return jsonify({
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 3600
    })

def list_users():
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]})

def refresh_access_token():
    req = request.get_json()
    refresh_token = req.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Invalid request"}), 400

    key = f"refresh:{refresh_token}"
    data = redis_client.get(key)
    if not data:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    user_id, user_email = data.decode().split(":", 1)
    new_access_token = generate_access_token(uuid.UUID(user_id), user_email)
    if not new_access_token:
        return jsonify({"error": "Failed to generate JWT"}), 500

    return jsonify({
        "access_token": new_access_token,
        "expires_in": 3600
    })

def logout():
    req = request.get_json()
    refresh_token = req.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Invalid request"}), 400

    key = f"refresh:{refresh_token}"
    redis_client.delete(key)
    return jsonify({"message": "Logged out successfully"})

def create_api_token():
    user_id = request.user_id  # You need to set this from your auth middleware
    token = generate_api_token(user_id, 30 * 24 * 3600)
    if not token:
        return jsonify({"error": "Failed to generate token"}), 500
    return jsonify({"api_token": token})

def revoke_api_token():
    req = request.get_json()
    api_token_id = req.get("api_token_id")
    if not api_token_id:
        return jsonify({"error": "Invalid request"}), 400

    result = APIToken.query.filter_by(id=api_token_id).update({"revoked": True})
    db.session.commit()
    if not result:
        return jsonify({"error": "Invalid API token"}), 401
    return jsonify({"message": "API token revoked"})

# Flask route bindings (example)
bp.route('/login', methods=['GET'])(handle_login)
bp.route('/callback', methods=['GET'])(handle_callback)
bp.route('/users', methods=['GET'])(list_users)
bp.route('/refresh', methods=['POST'])(refresh_access_token)
bp.route('/logout', methods=['POST'])(logout)
bp.route('/api-token', methods=['POST'])(create_api_token)
bp.route('/revoke-api-token', methods=['POST'])(revoke_api_token)