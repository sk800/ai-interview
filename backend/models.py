from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interviews = relationship("Interview", back_populates="user")
    samples = relationship("Sample", back_populates="user")

class Sample(Base):
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_path = Column(String)
    audio_path = Column(String)
    face_encoding = Column(Text)  # JSON string
    audio_features = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="samples")

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interview_type = Column(String)  # ai, react, java, etc.
    status = Column(String, default="pending")  # pending, in_progress, completed, terminated
    alert_count = Column(Integer, default=0)
    consecutive_face_failures = Column(Integer, default=0)  # Track consecutive face failures
    termination_reason = Column(String, nullable=True)  # face_violation, audio_violation, tab_switch
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="interviews")
    questions = relationship("Question", back_populates="interview")
    answers = relationship("Answer", back_populates="interview")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question_text = Column(Text)
    question_type = Column(String)  # text, audio, code
    time_limit = Column(Integer)  # seconds
    difficulty = Column(String)  # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interview = relationship("Interview", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_text = Column(Text)
    score = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question", back_populates="answers")

