from flask import Blueprint, request, jsonify
from app.database import db, Exam, Question, Option, ExamAttempt, ExamAssignment
from app.tokens import auth_middleware
from app.rbac import authorize
import uuid
from datetime import datetime

bp = Blueprint('exams', __name__, url_prefix='/api/v1/exams')

@bp.route('/', methods=['GET'])
@auth_middleware
@authorize('read:exams')
def list_exams():
    """List all exams with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        org_id = request.args.get('organization_id')
        
        query = Exam.query
        if org_id:
            query = query.filter_by(organization_id=uuid.UUID(org_id))
            
        exams = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            "success": True,
            "exams": [{
                "id": str(exam.id),
                "title": exam.title,
                "description": exam.description,
                "duration": exam.duration,
                "total_marks": exam.total_marks,
                "is_published": exam.is_published,
                "scheduled_date": exam.scheduled_date.isoformat() if exam.scheduled_date else None,
                "created_at": exam.created_at.isoformat()
            } for exam in exams.items],
            "total": exams.total,
            "pages": exams.pages,
            "current_page": page
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/', methods=['POST'])
@auth_middleware
@authorize('write:exams')
def create_exam():
    """Create a new exam"""
    try:
        data = request.get_json()
        required_fields = ['title', 'organization_id']
        if not all(field in data for field in required_fields):
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {required_fields}"
            }), 400
            
        exam = Exam(
            id=uuid.uuid4(),
            title=data['title'],
            description=data.get('description'),
            duration=data.get('duration'),
            instructions=data.get('instructions'),
            total_marks=data.get('total_marks'),
            passing_percentage=data.get('passing_percentage'),
            organization_id=uuid.UUID(data['organization_id']),
            created_by=request.user_id,
            scheduled_date=datetime.fromisoformat(data['scheduled_date']) if data.get('scheduled_date') else None,
            config=data.get('config', {})
        )
        
        db.session.add(exam)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "exam_id": str(exam.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<exam_id>/questions', methods=['POST'])
@auth_middleware
@authorize('write:exams')
def add_question():
    """Add a question to an exam"""
    try:
        data = request.get_json()
        required_fields = ['type', 'text', 'marks']
        if not all(field in data for field in required_fields):
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {required_fields}"
            }), 400
            
        question = Question(
            id=uuid.uuid4(),
            exam_id=uuid.UUID(exam_id),
            type=data['type'],
            text=data['text'],
            marks=data['marks'],
            correct_answer=data.get('correct_answer'),
            order=data.get('order'),
            diagram_url=data.get('diagram_url')
        )
        
        db.session.add(question)
        
        # Add options if provided
        if data.get('options'):
            for opt_data in data['options']:
                option = Option(
                    id=uuid.uuid4(),
                    question_id=question.id,
                    text=opt_data['text'],
                    order=opt_data.get('order'),
                    iscorrect=opt_data.get('iscorrect', False)
                )
                db.session.add(option)
                
        db.session.commit()
        
        return jsonify({
            "success": True,
            "question_id": str(question.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/<exam_id>/start', methods=['POST'])
@auth_middleware
def start_exam(exam_id):
    """Start an exam attempt"""
    try:
        exam = Exam.query.get(uuid.UUID(exam_id))
        if not exam:
            return jsonify({"success": False, "error": "Exam not found"}), 404
            
        # Check if user already has an ongoing attempt
        existing_attempt = ExamAttempt.query.filter_by(
            exam_id=exam.id,
            user_id=request.user_id,
            end_time=None
        ).first()
        
        if existing_attempt:
            return jsonify({
                "success": False,
                "error": "You already have an ongoing attempt"
            }), 400
            
        attempt = ExamAttempt(
            id=uuid.uuid4(),
            exam_id=exam.id,
            user_id=request.user_id,
            organization_id=exam.organization_id,
            start_time=datetime.utcnow(),
            status="ongoing"
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "attempt_id": str(attempt.id),
            "start_time": attempt.start_time.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500