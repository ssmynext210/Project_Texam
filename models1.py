from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Boolean, Integer, Text, DateTime, ForeignKey
from datetime import datetime
import uuid
from sqlalchemy import Numeric


db = SQLAlchemy()

# ======== Core Models ========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(100), unique=True, nullable=False)


class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True, nullable=False)


# ======== User ↔ Organization + Role ========
class UserOrganization(db.Model):
    __tablename__ = 'user_organizations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)

    user = db.relationship('User', backref='user_organizations')
    organization = db.relationship('Organization', backref='user_organizations')
    role = db.relationship('Role', backref='user_organizations')




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

