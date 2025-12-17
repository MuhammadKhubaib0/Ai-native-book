"""
Database models and connection setup for the RAG implementation
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# For now, using SQLite as a placeholder - in production this would likely be PostgreSQL or similar
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_textbook.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Import all models here to ensure they're registered with SQLAlchemy
from .models import Document, Embedding

def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()