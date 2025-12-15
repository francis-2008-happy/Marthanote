"""
SQLAlchemy models for document metadata, chat history, and session management.
Provides persistent storage for documents, embeddings, and conversation context.
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Document(Base):
    """
    Stores metadata for uploaded documents.
    Each document gets a unique ID and maintains its own FAISS index.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    summary = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    document_size = Column(Integer, default=0)  # Size in bytes
    chunk_count = Column(Integer, default=0)  # Number of chunks created
    is_active = Column(Boolean, default=False)  # Mark as active document for queries
    device_id = Column(String, nullable=True)  # Optional device identifier for per-device filtering

    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "upload_time": self.upload_time.isoformat(),
            "summary": self.summary,
            "chunk_count": self.chunk_count,
            "is_active": self.is_active,
            "device_id": self.device_id,
        }


class ChatMessage(Base):
    """
    Stores chat history for conversation context.
    Links messages to documents for multi-document support.
    """
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chat_messages")

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
