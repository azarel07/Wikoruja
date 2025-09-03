from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Role:
    ADMIN="ADMIN"; INSTRUTOR="INSTRUTOR"; MONITOR="MONITOR"; ALUNO="ALUNO"; AUDITOR="AUDITOR"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=Role.ALUNO)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    namespace = db.Column(db.String(64), index=True, nullable=False)
    slug = db.Column(db.String(120), index=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.Text, nullable=True)
    classification = db.Column(db.String(16), default="PUBLICO")  # PUBLICO/RESTRITO/CONFIDENCIAL
    content = db.Column(db.Text, default="")
    summary = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('namespace','slug', name='uix_namespace_slug'),)
    
class Revision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    content = db.Column(db.Text, default="")
    author = db.Column(db.String(80), default="system")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    db.create_all()
