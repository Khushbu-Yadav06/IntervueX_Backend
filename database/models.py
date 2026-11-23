from sqlalchemy import Column, Integer, String, Text, DateTime, JSON , ForeignKey , Float , Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(150), nullable=False)

    email = Column(String(150), unique=True, nullable=False, index=True)

    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

class InterviewSession(Base):

    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)

    interview_id = Column(String(36), unique=True, nullable=False, index=True)
    ai_session_id = Column(String(100), nullable=True)


    target_role = Column(String(150), nullable=False)
    education = Column(String(200), nullable=False)
    experience = Column(String(200), nullable=False)

    skills = Column(JSON, nullable=False)

    interview_type = Column(String(30), nullable=False)
    difficulty = Column(String(30), nullable=False)

    number_of_questions = Column(Integer, nullable=False)

    resume_text = Column(Text, nullable=True)

    status = Column(String(30), default="in_progress", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan"
    )

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)

    interview_session_id = Column(
        Integer,
        ForeignKey("interview_sessions.id"),
        nullable=False
    )

    question_text = Column(Text, nullable=False)

    question_order = Column(Integer, nullable=False)

    interview = relationship(
        "InterviewSession",
        back_populates="questions"
    )

    answer = relationship(
        "InterviewAnswer",
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan"
    )

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)

    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id"),
        unique=True,
        nullable=False
    )

    answer_text = Column(Text, nullable=False)

    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship(
        "InterviewQuestion",
        back_populates="answer"
    )

    evaluation = relationship(
        "AnswerEvaluation",
        back_populates="answer",
        uselist=False,
        cascade="all, delete-orphan"
    )

class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    answer_id = Column(
        Integer,
        ForeignKey("interview_answers.id"),
        unique=True,
        nullable=False
    )

    feedback = Column(Text, nullable=False)

    score = Column(Float, nullable=False)

    evaluated_at = Column(DateTime, default=datetime.utcnow)

    answer = relationship(
        "InterviewAnswer",
        back_populates="evaluation"
    )

