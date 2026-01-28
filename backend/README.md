# AI Interview Automation - Backend

FastAPI backend for AI-powered interview automation system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `SECRET_KEY`: A secure secret key for JWT tokens

4. Create necessary directories:
```bash
mkdir -p samples temp
```

5. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/samples/upload` - Upload video/audio samples
- `POST /api/interviews/start` - Start interview
- `GET /api/interviews/{id}/question` - Get next question
- `POST /api/interviews/{id}/answer` - Submit answer
- `POST /api/interviews/{id}/verify` - Verify user identity
- `GET /api/interviews/{id}/summary` - Get interview summary

## Features

- User authentication with JWT
- Face recognition using InsightFace
- Audio verification using librosa features
- Question generation via OpenRouter API or question bank
- AI-powered answer evaluation
- Real-time monitoring and anti-cheating measures

