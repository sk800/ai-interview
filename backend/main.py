from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv
import json
import asyncio

from database import SessionLocal, engine, Base
from models import User, Interview, Question, Answer, Sample
from schemas import UserCreate, UserLogin, InterviewCreate, QuestionResponse, AnswerSubmit
from auth import verify_token, create_access_token, get_password_hash, verify_password
from face_recognition_service import FaceRecognitionService
from audio_service import AudioService
from question_service import QuestionService
from evaluation_service import EvaluationService

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interview Automation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Initialize services
face_service = FaceRecognitionService()
audio_service = AudioService()
question_service = QuestionService()
evaluation_service = EvaluationService()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/api/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.post("/api/samples/upload")
async def upload_samples(
    photo: UploadFile = File(...),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload photo and audio samples for user verification"""
    try:
        # Save photo sample
        photo_path = f"samples/{current_user.id}_photo.jpg"
        os.makedirs("samples", exist_ok=True)
        with open(photo_path, "wb") as f:
            content = await photo.read()
            f.write(content)
        
        # Save audio sample
        audio_path = f"samples/{current_user.id}_audio.webm"
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Process samples for face and audio recognition
        face_id = await face_service.process_sample(photo_path)
        audio_reference = await audio_service.process_sample(audio_path)  # Store audio path for verification
        
        # Store in database
        # Note: face_encoding field stores the Azure Face ID (as string) instead of encoding array
        # audio_features stores the audio file path for verification
        sample = Sample(
            user_id=current_user.id,
            video_path=photo_path,  # Store photo path in video_path field for compatibility
            audio_path=audio_path,
            face_encoding=face_id if face_id else None,  # Store Azure Face ID as string
            audio_features=audio_reference if audio_reference else None  # Store audio path for verification
        )
        db.add(sample)
        db.commit()
        
        return {"message": "Samples uploaded successfully", "sample_id": sample.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing samples: {str(e)}")

@app.post("/api/interviews/start")
async def start_interview(
    interview_data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new interview"""
    # Check if user has samples
    sample = db.query(Sample).filter(Sample.user_id == current_user.id).order_by(Sample.created_at.desc()).first()
    if not sample:
        raise HTTPException(status_code=400, detail="Please upload video and audio samples first")
    
    # Create interview
    interview = Interview(
        user_id=current_user.id,
        interview_type=interview_data.interview_type,
        status="in_progress"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return {"interview_id": interview.id, "message": "Interview started"}

@app.get("/api/interviews/{interview_id}/question")
async def get_question(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get next question for the interview"""
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Check interview status first
    if interview.status == "completed":
        return {"completed": True, "message": "Interview already completed"}
    
    if interview.status == "terminated":
        return {"completed": True, "terminated": True, "message": "Interview was terminated"}
    
    # Get answered questions count
    answered_count = db.query(Answer).filter(Answer.interview_id == interview_id).count()
    
    if answered_count >= 10:
        # Interview complete
        interview.status = "completed"
        db.commit()
        return {"completed": True, "message": "Interview completed"}
    
    # Generate or get question
    question = await question_service.get_question(interview.interview_type, answered_count)
    
    # Store question in database
    db_question = Question(
        interview_id=interview_id,
        question_text=question["question"],
        question_type=question.get("type", "text"),
        time_limit=question.get("time_limit", 300),
        difficulty=question.get("difficulty", "medium")
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # Randomly assign answer mode (speaking or writing)
    import random
    answer_mode = random.choice(["speaking", "writing"])
    
    return {
        "question_id": db_question.id,
        "question": db_question.question_text,
        "type": db_question.question_type,
        "time_limit": db_question.time_limit,
        "question_number": answered_count + 1,
        "total_questions": 10,
        "answer_mode": answer_mode
    }

@app.post("/api/interviews/{interview_id}/answer")
async def submit_answer(
    interview_id: int,
    answer_data: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit answer for a question"""
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.status == "terminated":
        raise HTTPException(status_code=400, detail="Interview has been terminated")
    
    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")
    
    question = db.query(Question).filter(Question.id == answer_data.question_id, Question.interview_id == interview_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Evaluate answer (even if empty, evaluate what was provided)
    evaluation = await evaluation_service.evaluate_answer(
        question.question_text,
        answer_data.answer_text,
        interview.interview_type
    )
    
    # Store answer
    answer = Answer(
        interview_id=interview_id,
        question_id=answer_data.question_id,
        answer_text=answer_data.answer_text,
        score=evaluation["score"],
        feedback=evaluation["feedback"]
    )
    db.add(answer)
    db.commit()
    
    # Check if this was the last question (10 questions total)
    answered_count = db.query(Answer).filter(Answer.interview_id == interview_id).count()
    is_completed = answered_count >= 10
    
    if is_completed:
        interview.status = "completed"
        db.commit()
    
    return {
        "answer_id": answer.id,
        "score": answer.score,
        "feedback": answer.feedback,
        "next_question_available": not is_completed,
        "interview_completed": is_completed
    }

@app.post("/api/interviews/{interview_id}/terminate")
async def terminate_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminate interview (e.g., due to tab switch)"""
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Only set termination_reason if it's not already set (to avoid overwriting face/audio violations)
    if interview.status != "terminated" or interview.termination_reason is None:
        interview.status = "terminated"
        interview.termination_reason = "tab_switch"  # Mark as tab switch termination
    # If already terminated with a reason, don't overwrite it
    elif interview.status == "terminated" and interview.termination_reason:
        # Already terminated with a specific reason, don't change it
        pass
    
    db.commit()
    
    return {"message": "Interview terminated", "interview_id": interview_id}

@app.post("/api/interviews/{interview_id}/verify")
async def verify_user(
    interview_id: int,
    snapshot: UploadFile = File(...),
    audio_clip: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify user identity during interview (called every 5 seconds)"""
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get user's sample
    sample = db.query(Sample).filter(Sample.user_id == current_user.id).order_by(Sample.created_at.desc()).first()
    if not sample:
        raise HTTPException(status_code=400, detail="No samples found")
    
    # Save snapshot temporarily
    snapshot_path = f"temp/{interview_id}_snapshot.jpg"
    os.makedirs("temp", exist_ok=True)
    with open(snapshot_path, "wb") as f:
        content = await snapshot.read()
        f.write(content)
    
    # Verify face - returns (is_match, reason)
    face_match, face_reason = await face_service.verify_face(snapshot_path, sample.face_encoding)
    
    # Track consecutive face failures
    # Only count actual violations: no_face or different_face
    is_face_violation = face_reason in ["no_face", "different_face"]
    
    if is_face_violation:
        interview.consecutive_face_failures = (interview.consecutive_face_failures or 0) + 1
    else:
        # Reset counter on successful verification
        interview.consecutive_face_failures = 0
    
    # Verify audio - compare with stored audio sample (captured before interview)
    audio_match = True
    audio_path = None
    if audio_clip:
        audio_path = f"temp/{interview_id}_audio.webm"
        with open(audio_path, "wb") as f:
            content = await audio_clip.read()
            f.write(content)
        # Verify against stored audio sample path (photo and audio captured before interview start)
        stored_audio_path = sample.audio_path  # Path to original audio sample captured before interview
        if stored_audio_path and os.path.exists(stored_audio_path):
            audio_match = await audio_service.verify_audio(audio_path, stored_audio_path)
        else:
            print("Stored audio file not found, allowing verification")
            audio_match = True  # Allow if stored audio not found
    
    # Clean up temp files
    try:
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
        if audio_clip and audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        print(f"Error cleaning up temp files: {str(e)}")
    
    # Only alert on actual violations:
    # - Face: 3 consecutive failures (no face or different face)
    # - Audio: mismatch
    violation_type = None
    should_alert = False
    
    # Face violation: only if 3 consecutive failures
    if interview.consecutive_face_failures >= 3:
        violation_type = "face_violation"
        should_alert = True
    # Audio violation: immediate alert
    elif not audio_match:
        violation_type = "audio_violation"
        should_alert = True
    
    if should_alert:
        interview.alert_count = (interview.alert_count or 0) + 1
        db.commit()
        
        # Terminate after 3 alerts (changed from 2)
        if interview.alert_count >= 3:
            interview.status = "terminated"
            interview.termination_reason = violation_type  # Store termination reason
            db.commit()
            return {
                "verified": False,
                "alert": True,
                "terminated": True,
                "violation_type": violation_type,
                "alert_count": interview.alert_count,
                "message": f"Interview terminated due to {violation_type.replace('_', ' ')} (3 alerts)"
            }
        
        return {
            "verified": False,
            "alert": True,
            "alert_count": interview.alert_count,
            "violation_type": violation_type,
            "message": f"Identity verification failed: {violation_type.replace('_', ' ')} ({interview.alert_count}/3 alerts)"
        }
    
    return {"verified": True, "alert": False}

@app.get("/api/interviews/{interview_id}/summary")
async def get_summary(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview summary (for completed or terminated interviews)"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Allow summary both when interview is fully completed and when it was terminated
    if interview.status not in ("completed", "terminated"):
        raise HTTPException(status_code=400, detail="Interview not completed or terminated yet")

    # Get all answers given before completion/termination
    answers = db.query(Answer).filter(Answer.interview_id == interview_id).all()

    total_score = sum(answer.score for answer in answers)
    average_score = total_score / len(answers) if answers else 0

    # Generate high-level summary using evaluation service
    summary = await evaluation_service.generate_summary(interview, answers, db)

    return {
        "interview_id": interview.id,
        "interview_type": interview.interview_type,
        "status": interview.status,
        "termination_reason": interview.termination_reason,  # Include termination reason
        "total_questions": len(answers),
        "average_score": average_score,
        "total_score": total_score,
        "summary": summary,
        "answers": [
            {
                "question": db.query(Question).filter(Question.id == answer.question_id).first().question_text,
                "answer": answer.answer_text,
                "score": answer.score,
                "feedback": answer.feedback,
            }
            for answer in answers
        ],
    }

@app.websocket("/ws/interviews/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: int):
    """WebSocket for real-time monitoring"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Handle real-time monitoring data
            await websocket.send_json({"status": "received"})
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

