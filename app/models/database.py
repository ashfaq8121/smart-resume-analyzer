# database.py — UPGRADE 3: SQLAlchemy Database Models
# ─────────────────────────────────────────────────────────────────
# Adds persistent storage so analysis history is never lost.
#
# Tables:
#   User          → accounts (email, hashed password)
#   AnalysisResult→ saved single-resume analysis records
#   RankingSession→ saved multi-resume ranking records
#
# Usage:
#   from app.models.database import db, User, AnalysisResult
# ─────────────────────────────────────────────────────────────────

# from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy
# from flask_bcrypt import Bcrypt
# from flask_login import UserMixin

# db     = SQLAlchemy()
# bcrypt = Bcrypt()


# class User(UserMixin, db.Model):
#     """
#     User account.
#     UserMixin gives Flask-Login methods: is_authenticated, is_active, get_id()
#     """
#     __tablename__ = 'users'

#     id         = db.Column(db.Integer, primary_key=True)
#     name       = db.Column(db.String(120), nullable=False)
#     email      = db.Column(db.String(120), unique=True, nullable=False)
#     password   = db.Column(db.String(200), nullable=False)  # bcrypt hash
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     # Relationships
#     analyses = db.relationship('AnalysisResult', backref='user', lazy=True, cascade='all,delete')
#     rankings = db.relationship('RankingSession', backref='user', lazy=True, cascade='all,delete')

#     def set_password(self, password: str):
#         """Hash password with bcrypt before storing."""
#         self.password = bcrypt.generate_password_hash(password).decode('utf-8')

#     def check_password(self, password: str) -> bool:
#         """Verify a password against the stored hash."""
#         return bcrypt.check_password_hash(self.password, password)

#     def __repr__(self):
#         return f'<User {self.email}>'


# class AnalysisResult(db.Model):
#     """
#     Saved single-resume analysis.
#     Every time a user analyzes a resume, we store the result here
#     so they can view their history and track score improvements.
#     """
#     __tablename__ = 'analysis_results'

#     id               = db.Column(db.Integer, primary_key=True)
#     user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
#     filename         = db.Column(db.String(255), nullable=False)
#     job_description  = db.Column(db.Text, nullable=False)
#     overall_score    = db.Column(db.Float, nullable=False)
#     semantic_score   = db.Column(db.Float, default=0.0)
#     skills_score     = db.Column(db.Float, default=0.0)
#     ats_score        = db.Column(db.Float, default=0.0)
#     matched_skills   = db.Column(db.JSON, default=list)   # stored as JSON array
#     missing_skills   = db.Column(db.JSON, default=list)
#     grade_letter     = db.Column(db.String(5), default='F')
#     grade_label      = db.Column(db.String(50), default='')
#     suggestions      = db.Column(db.JSON, default=list)
#     created_at       = db.Column(db.DateTime, default=datetime.utcnow)

#     def to_dict(self) -> dict:
#         """Convert to dictionary for JSON responses."""
#         return {
#             'id':             self.id,
#             'filename':       self.filename,
#             'overall_score':  self.overall_score,
#             'semantic_score': self.semantic_score,
#             'skills_score':   self.skills_score,
#             'ats_score':      self.ats_score,
#             'matched_skills': self.matched_skills or [],
#             'missing_skills': self.missing_skills or [],
#             'grade_letter':   self.grade_letter,
#             'grade_label':    self.grade_label,
#             'created_at':     self.created_at.strftime('%d %b %Y, %I:%M %p'),
#         }


# class RankingSession(db.Model):
#     """
#     Saved multi-resume ranking session.
#     Stores summary info about each ranking run.
#     """
#     __tablename__ = 'ranking_sessions'

#     id              = db.Column(db.Integer, primary_key=True)
#     user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
#     job_description = db.Column(db.Text, nullable=False)
#     total_candidates= db.Column(db.Integer, default=0)
#     top_candidate   = db.Column(db.String(255), default='')
#     avg_score       = db.Column(db.Float, default=0.0)
#     results_json    = db.Column(db.JSON, default=dict)   # full ranking stored as JSON
#     created_at      = db.Column(db.DateTime, default=datetime.utcnow)

#     def to_dict(self) -> dict:
#         return {
#             'id':                self.id,
#             'total_candidates':  self.total_candidates,
#             'top_candidate':     self.top_candidate,
#             'avg_score':         self.avg_score,
#             'created_at':        self.created_at.strftime('%d %b %Y, %I:%M %p'),
#         }


# def init_db(app):
#     """
#     Initialise database with the Flask app.
#     Creates all tables if they don't exist.
#     Call this from app/__init__.py
#     """
#     db.init_app(app)
#     bcrypt.init_app(app)

#     with app.app_context():
#         db.create_all()
#         print("  ✅  Database initialised (SQLite)")


from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    analyses = db.relationship(
        "AnalysisResult",
        backref="user",
        lazy=True,
        cascade="all,delete"
    )
    rankings = db.relationship(
        "RankingSession",
        backref="user",
        lazy=True,
        cascade="all,delete"
    )

    def set_password(self, password: str):
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.email}>"


class AnalysisResult(db.Model):
    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    semantic_score = db.Column(db.Float, default=0.0)
    skills_score = db.Column(db.Float, default=0.0)
    ats_score = db.Column(db.Float, default=0.0)
    matched_skills = db.Column(db.JSON, default=list)
    missing_skills = db.Column(db.JSON, default=list)
    grade_letter = db.Column(db.String(5), default="F")
    grade_label = db.Column(db.String(50), default="")
    suggestions = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def job_description_preview(self, length=120):
        if self.job_description and len(self.job_description) > length:
            return self.job_description[:length] + "..."
        return self.job_description or ""

    def score_display(self):
        return f"{self.overall_score:.1f}%"

    def uploaded_at_display(self):
        return self.created_at.strftime("%d %b %Y, %I:%M %p")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "overall_score": self.overall_score,
            "semantic_score": self.semantic_score,
            "skills_score": self.skills_score,
            "ats_score": self.ats_score,
            "matched_skills": self.matched_skills or [],
            "missing_skills": self.missing_skills or [],
            "grade_letter": self.grade_letter,
            "grade_label": self.grade_label,
            "created_at": self.created_at.strftime("%d %b %Y, %I:%M %p"),
        }


class RankingSession(db.Model):
    __tablename__ = "ranking_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    job_description = db.Column(db.Text, nullable=False)
    total_candidates = db.Column(db.Integer, default=0)
    top_candidate = db.Column(db.String(255), default="")
    avg_score = db.Column(db.Float, default=0.0)
    results_json = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "total_candidates": self.total_candidates,
            "top_candidate": self.top_candidate,
            "avg_score": self.avg_score,
            "created_at": self.created_at.strftime("%d %b %Y, %I:%M %p"),
        }


def init_db(app):
    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()
        print("✅ Database initialised (SQLite)")