# Project Structure

## Backend (FastAPI)

```
backend/
├── main.py                      # Main FastAPI application
├── database.py                  # Database configuration
├── models.py                    # SQLAlchemy models
├── schemas.py                   # Pydantic schemas
├── auth.py                      # Authentication utilities
├── face_recognition_service.py # Face recognition using InsightFace
├── audio_service.py             # Audio processing and verification
├── question_service.py          # Question generation (LLM/Question bank)
├── evaluation_service.py        # Answer evaluation using LLM
├── question_bank.json           # Pre-defined questions
├── requirements.txt            # Python dependencies
├── run.py                      # Server runner script
├── .env.example                # Environment variables template
└── README.md                   # Backend documentation
```

## Frontend (Next.js)

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page (redirects)
│   ├── globals.css             # Global styles
│   ├── login/
│   │   └── page.tsx            # Login/Register page
│   ├── dashboard/
│   │   └── page.tsx            # Dashboard to start interviews
│   ├── samples/
│   │   └── page.tsx            # Video/audio sample upload
│   ├── interview/
│   │   └── [id]/
│   │       └── page.tsx        # Interview page with monitoring
│   └── summary/
│       └── [id]/
│           └── page.tsx        # Interview results summary
├── lib/
│   └── api.ts                  # API client configuration
├── types/
│   └── index.ts                # TypeScript type definitions
├── package.json                # Node dependencies
├── next.config.js              # Next.js configuration
├── tsconfig.json               # TypeScript configuration
└── README.md                   # Frontend documentation
```

## Key Features Implementation

### Authentication
- ✅ JWT-based authentication
- ✅ User registration and login
- ✅ Protected routes

### Sample Collection
- ✅ Video recording (10 seconds)
- ✅ Audio recording
- ✅ Face encoding extraction
- ✅ Audio feature extraction
- ✅ Sample storage

### Interview Flow
- ✅ Interview type selection
- ✅ Question generation (LLM or question bank)
- ✅ 10 questions per interview
- ✅ Time limits per question
- ✅ Answer submission (text)
- ✅ Sequential question flow

### Monitoring & Anti-Cheating
- ✅ Continuous video monitoring (every 5 seconds)
- ✅ Face verification against sample
- ✅ Audio verification
- ✅ Copy-paste disabled
- ✅ Tab switching detection
- ✅ Alert system (2 alerts = termination)
- ✅ Automatic interview termination

### Evaluation
- ✅ AI-powered answer evaluation
- ✅ Score calculation (0-100)
- ✅ Detailed feedback per answer
- ✅ Final summary generation
- ✅ Performance metrics

### UI/UX
- ✅ Modern, responsive design
- ✅ Real-time timer
- ✅ Video preview
- ✅ Toast notifications
- ✅ Loading states
- ✅ Error handling

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

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite:///./interview.db
SECRET_KEY=your-secret-key
OPENROUTER_API_KEY=your-openrouter-api-key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Development

1. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Production

1. **Backend:**
   - Use Gunicorn with Uvicorn workers
   - Set up PostgreSQL database
   - Configure environment variables
   - Use HTTPS

2. **Frontend:**
   ```bash
   npm run build
   npm start
   ```
   Or deploy to Vercel/Netlify

## Technologies Used

- **Frontend:** Next.js 14, React 18, TypeScript
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **AI/ML:** InsightFace, OpenAI Whisper, Librosa
- **LLM:** OpenRouter API (GPT-3.5/GPT-4)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Authentication:** JWT

