from flask import Blueprint, request, jsonify
from app.database import (
    db, Organization, UserOrganization, 
    User, Role, StudentGroup
)
from app.tokens import auth_middleware
from app.rbac import authorize
import uuid
from datetime import datetime

bp = Blueprint('organizations', __name__, url_prefix='/api/v1/organizations')

@bp.route('/', methods=['GET'])
@auth_middleware
@authorize('read:organizations')
def list_organizations():
    """Get all organizations with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Organization.query
        organizations = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            "success": True,
            "organizations": [{
                "id": str(org.id),
                "name": org.name,
                "created_at": org.created_at.isoformat(),
                "member_count": len(org.user_organizations)
            } for org in organizations.items],
            "total": organizations.total,
            "pages": organizations.pages,
            "current_page": organizations.page
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/', methods=['POST'])
@auth_middleware
@authorize('write:organizations')
def create_organization():
    """Create a new organization"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "error": "Organization name is required"
            }), 400
            
        org = Organization(
            id=uuid.uuid4(),
            name=data['name'],
            created_at=datetime.utcnow()
        )
        db.session.add(org)
        
        # Assign creator as admin of organization
        user_id = request.user_id
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            user_org = UserOrganization(
                id=uuid.uuid4(),
                user_id=user_id,
                organization_id=org.id,
                role_id=admin_role.id
            )
            db.session.add(user_org)
            
        db.session.commit()
        
        return jsonify({
            "success": True,
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "created_at": org.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<org_id>', methods=['GET'])
@auth_middleware
@authorize('read:organizations')
def get_organization(org_id):
    """Get organization details including members and groups"""
    try:
        org = Organization.query.filter_by(id=uuid.UUID(org_id)).first()
        if not org:
            return jsonify({
                "success": False,
                "error": "Organization not found"
            }), 404
            
        members = [{
            "user_id": str(uo.user_id),
            "user_name": uo.user.name,
            "role": uo.role.name
        } for uo in org.user_organizations]
        
        groups = [{
            "id": str(group.id),
            "name": group.name,
            "member_count": len(group.members)
        } for group in org.student_groups]
        
        return jsonify({
            "success": True,
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "created_at": org.created_at.isoformat(),
                "members": members,
                "groups": groups
            }
        }), 200
    except ValueError:
        return jsonify({"success": False, "error": "Invalid organization ID"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<org_id>/members', methods=['POST'])
@auth_middleware
@authorize('write:organizations')
def add_member():
    """Add a member to organization"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'role_name' not in data:
            return jsonify({
                "success": False,
                "error": "User ID and role name are required"
            }), 400
            
        org = Organization.query.filter_by(id=uuid.UUID(org_id)).first()
        if not org:
            return jsonify({
                "success": False,
                "error": "Organization not found"
            }), 404
            
        user = User.query.filter_by(id=uuid.UUID(data['user_id'])).first()
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
            
        role = Role.query.filter_by(name=data['role_name']).first()
        if not role:
            return jsonify({
                "success": False,
                "error": "Role not found"
            }), 404
            
        # Check if user is already a member
        if UserOrganization.query.filter_by(
            user_id=user.id,
            organization_id=org.id
        ).first():
            return jsonify({
                "success": False,
                "error": "User is already a member"
            }), 400
            
        user_org = UserOrganization(
            id=uuid.uuid4(),
            user_id=user.id,
            organization_id=org.id,
            role_id=role.id
        )
        db.session.add(user_org)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"User added to organization with role {role.name}"
        }), 200
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid UUID format"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<org_id>/members/<user_id>', methods=['DELETE'])
@auth_middleware
@authorize('write:organizations')
def remove_member(org_id, user_id):
    """Remove a member from organization"""
    try:
        user_org = UserOrganization.query.filter_by(
            organization_id=uuid.UUID(org_id),
            user_id=uuid.UUID(user_id)
        ).first()
        
        if not user_org:
            return jsonify({
                "success": False,
                "error": "User is not a member of this organization"
            }), 404
            
        db.session.delete(user_org)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Member removed successfully"
        }), 200
    except ValueError:
        return jsonify({"success": False, "error": "Invalid UUID format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500





        