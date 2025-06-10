from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Boolean, Integer, Text, DateTime, ForeignKey, Numeric
from datetime import datetime
import uuid
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True)
    domain = db.Column(db.String(100), unique=True)
    provider = db.Column(db.String(100))
    client_id = db.Column(db.String(200))
    client_secret = db.Column(db.String(200))
    auth_url = db.Column(db.String(200))
    token_url = db.Column(db.String(200))
    userinfo_url = db.Column(db.String(200))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(100))
    picture = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(UUID(as_uuid=True), db.ForeignKey('permissions.id'), nullable=False)

    role = db.relationship('Role', backref='role_permissions')
    permission = db.relationship('Permission', backref='role_permissions')

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)

    user = db.relationship('User', backref='user_roles')
    role = db.relationship('Role', backref='user_roles')

class UserOrganization(db.Model):
    __tablename__ = 'user_organizations'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)

    user = db.relationship('User', backref='user_organizations')
    organization = db.relationship('Organization', backref='user_organizations')
    role = db.relationship('Role', backref='user_organizations')

class APIToken(db.Model):
    __tablename__ = 'api_tokens'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='api_tokens')

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(Text, nullable=False)
    description = db.Column(Text, nullable=True)
    duration = db.Column(Integer, nullable=True)
    instructions = db.Column(Text, nullable=True)
    total_marks = db.Column(Integer, nullable=True)
    passing_percentage = db.Column(Integer, nullable=True)
    is_published = db.Column(Boolean, default=False, nullable=False)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_date = db.Column(DateTime, nullable=True)
    config = db.Column(JSONB, nullable=True)

    organization = db.relationship('Organization', backref=db.backref('exams', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_exams', lazy=True))

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = db.Column(UUID(as_uuid=True), db.ForeignKey('exams.id'), nullable=False)
    type = db.Column(Text, nullable=False)
    text = db.Column(Text, nullable=False)
    marks = db.Column(Integer, nullable=True)
    correct_answer = db.Column(JSONB, nullable=True)
    order = db.Column(Integer, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    diagram_url = db.Column(Text, nullable=True)

    exam = db.relationship('Exam', backref=db.backref('questions', lazy=True))

class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = db.Column(UUID(as_uuid=True), db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(Text, nullable=False)
    order = db.Column(Integer, nullable=True)
    iscorrect = db.Column(Boolean, default=False, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)

    question = db.relationship('Question', backref=db.backref('options', lazy=True))

class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = db.Column(UUID(as_uuid=True), db.ForeignKey('exams.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(DateTime, nullable=True)
    end_time = db.Column(DateTime, nullable=True)
    status = db.Column(Text, nullable=True)
    score = db.Column(Integer, nullable=True)
    percentage = db.Column(Numeric, nullable=True)
    answers = db.Column(JSONB, nullable=True)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)

    exam = db.relationship('Exam', backref=db.backref('attempts', lazy=True))
    user = db.relationship('User', backref=db.backref('exam_attempts', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('exam_attempts', lazy=True))

class StudentGroup(db.Model):
    __tablename__ = 'student_groups'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(Text, nullable=False)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    description = db.Column(Text, nullable=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = db.relationship('Organization', backref=db.backref('student_groups', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_groups', lazy=True))

class ExamAssignment(db.Model):
    __tablename__ = 'exam_assignments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = db.Column(UUID(as_uuid=True), db.ForeignKey('exams.id'), nullable=False)
    assigned_to_type = db.Column(Text, nullable=False)  # e.g., "user" or "group"
    assigned_to_id = db.Column(UUID(as_uuid=True), nullable=False)
    due_date = db.Column(DateTime, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)

    exam = db.relationship('Exam', backref=db.backref('assignments', lazy=True))

class StudentGroupMember(db.Model):
    __tablename__ = 'student_group_members'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = db.Column(UUID(as_uuid=True), db.ForeignKey('student_groups.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)

    group = db.relationship('StudentGroup', backref=db.backref('members', lazy=True))
    student = db.relationship('User', backref=db.backref('group_memberships', lazy=True))

# --- Helper functions (unchanged) ---

def seed_roles_and_permissions():
    roles = ['Admin', 'Viewer', 'Student', 'Member']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(id=uuid.uuid4(), name=role_name))
    db.session.commit()

    permissions = [
        'read:users',
        'write:users',
        'read:reports',
        'write:reports'
    ]
    for perm_name in permissions:
        if not Permission.query.filter_by(name=perm_name).first():
            db.session.add(Permission(id=uuid.uuid4(), name=perm_name))
    db.session.commit()

    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        for perm in Permission.query.all():
            if not RolePermission.query.filter_by(role_id=admin_role.id, permission_id=perm.id).first():
                db.session.add(RolePermission(id=uuid.uuid4(), role_id=admin_role.id, permission_id=perm.id))
        db.session.commit()

def assign_user_role(user_id, role_name):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return False
    if not UserRole.query.filter_by(user_id=user_id, role_id=role.id).first():
        db.session.add(UserRole(id=uuid.uuid4(), user_id=user_id, role_id=role.id))
        db.session.commit()
    return True

def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
        seed_roles_and_permissions()
        if not User.query.filter_by(username="testuser").first():
            db.session.add(User(id=uuid.uuid4(), username="testuser"))
            db.session.commit()
        if not Organization.query.filter_by(name="Default Org").first():
            db.session.add(Organization(id=uuid.uuid4(), name="Default Org", created_at=datetime.utcnow()))
            db.session.commit()