from flask import Blueprint, request, jsonify
from app.database import db, User, Role, UserRole
from app.tokens import auth_middleware
from app.rbac import authorize
import uuid

bp = Blueprint('users', __name__, url_prefix='/api/v1')

@bp.route('/users', methods=['GET'])
@auth_middleware
@authorize('read:users')
def list_users():
    """Get all users with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role = request.args.get('role')
        
        query = User.query
        if role:
            query = query.join(UserRole).join(Role).filter(Role.name == role)
            
        users = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            "success": True,
            "users": [user.to_dict() for user in users.items],
            "total": users.total,
            "pages": users.pages,
            "current_page": users.page
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/users/<user_id>', methods=['GET'])
@auth_middleware
@authorize('read:users')
def get_user(user_id):
    """Get user details by ID"""
    try:
        user = User.query.filter_by(id=uuid.UUID(user_id)).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
            
        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({"success": False, "error": "Invalid user ID"}), 400