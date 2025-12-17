from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base
import uuid

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    module = Column(String, index=True)
    chapter = Column(Integer)
    content = Column(Text)
    url = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to embeddings
    embeddings = relationship("Embedding", back_populates="document")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    content = Column(Text)
    embedding_vector = Column(String)  # In production, use a proper vector type
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to document
    document = relationship("Document", back_populates="embeddings")