# AI Interview Automation System

A comprehensive AI-powered interview automation platform with real-time monitoring and anti-cheating features.

## Features

### Frontend (Next.js)
- User authentication (login/register)
- Video and audio sample collection for identity verification
- Real-time interview interface with:
  - Live video monitoring
  - Question display with timer
  - Text and audio answer input
  - Continuous identity verification
- Anti-cheating measures:
  - Copy-paste disabled
  - Tab switching detection and alerts
  - Continuous face and audio verification
- Interview summary with detailed feedback

### Backend (FastAPI)
- JWT-based authentication
- Face recognition using InsightFace
- Audio verification using librosa features
- Question generation via OpenRouter API or question bank
- AI-powered answer evaluation using GPT-4
- Real-time monitoring and verification
- Automatic interview termination on violations

## Tech Stack

### Frontend
- Next.js 14
- React 18
- TypeScript
- React Webcam
- Axios
- React Hot Toast

### Backend
- FastAPI
- SQLAlchemy
- InsightFace (face recognition)
- OpenAI Whisper (audio transcription)
- Librosa (audio features)
- OpenRouter API (LLM integration)
- JWT authentication

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Update `.env` with your credentials:
```
DATABASE_URL=sqlite:///./interview.db
SECRET_KEY=your-secret-key-change-in-production
OPENROUTER_API_KEY=your-openrouter-api-key
```

6. Create necessary directories:
```bash
mkdir -p samples temp
```

7. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage Flow

1. **Register/Login**: Create an account or login
2. **Upload Samples**: Record and upload video/audio samples for identity verification
3. **Start Interview**: Select interview type and start the interview
4. **Answer Questions**: Answer 10 questions with time limits
5. **View Results**: Get detailed summary with scores and feedback

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Samples
- `POST /api/samples/upload` - Upload video/audio samples

### Interviews
- `POST /api/interviews/start` - Start new interview
- `GET /api/interviews/{id}/question` - Get next question
- `POST /api/interviews/{id}/answer` - Submit answer
- `POST /api/interviews/{id}/verify` - Verify user identity
- `GET /api/interviews/{id}/summary` - Get interview summary

## Production Deployment

### Backend
- Use a production ASGI server like Gunicorn with Uvicorn workers
- Set up proper database (PostgreSQL recommended)
- Configure environment variables securely
- Set up proper CORS origins
- Use HTTPS

### Frontend
- Build for production: `npm run build`
- Use a production server or deploy to Vercel/Netlify
- Configure environment variables
- Ensure API URL is correct

## Security Considerations

- Change default SECRET_KEY in production
- Use strong passwords for database
- Implement rate limiting
- Add input validation
- Use HTTPS in production
- Secure API keys
- Implement proper error handling

## License

MIT

