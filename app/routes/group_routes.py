from flask import Blueprint, request, jsonify
from app.database import db, StudentGroup, StudentGroupMember, User
from app.tokens import auth_middleware
from app.rbac import authorize
import uuid

bp = Blueprint('groups', __name__, url_prefix='/api/v1/groups')

@bp.route('/', methods=['GET'])
@auth_middleware
@authorize('read:groups')
def list_groups():
    """List all student groups"""
    try:
        org_id = request.args.get('organization_id')
        if not org_id:
            return jsonify({
                "success": False,
                "error": "Organization ID is required"
            }), 400
            
        groups = StudentGroup.query.filter_by(
            organization_id=uuid.UUID(org_id)
        ).all()
        
        return jsonify({
            "success": True,
            "groups": [{
                "id": str(group.id),
                "name": group.name,
                "description": group.description,
                "member_count": len(group.members)
            } for group in groups]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<group_id>/members', methods=['POST'])
@auth_middleware
@authorize('write:groups')
def add_member(group_id):
    """Add a member to a student group"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                "success": False,
                "error": "Student ID is required"
            }), 400
            
        member = StudentGroupMember(
            id=uuid.uuid4(),
            group_id=uuid.UUID(group_id),
            student_id=uuid.UUID(data['student_id'])
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Member added successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500