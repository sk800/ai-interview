from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class InterviewCreate(BaseModel):
    interview_type: str  # ai, react, java, etc.

class QuestionResponse(BaseModel):
    question_id: int
    question: str
    type: str
    time_limit: int
    question_number: int
    total_questions: int

class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str

