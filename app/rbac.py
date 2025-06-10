from functools import wraps
from flask import request, jsonify
from app.database import UserRole, Role, Permission, User

def authorize(permission_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            # Check if user has the required permission
            user_roles = UserRole.query.filter_by(user_id=user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            for role in roles:
                perms = [rp.permission_id for rp in role.role_permissions]
                if Permission.query.filter(Permission.id.in_(perms), Permission.name == permission_name).first():
                    return f(*args, **kwargs)
            return jsonify({"error": "Forbidden"}), 403
        return wrapper
    return decorator