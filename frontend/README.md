# AI Interview Automation - Frontend

Next.js frontend for AI-powered interview automation system.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Features

- User authentication (login/register)
- Video and audio sample collection
- Real-time interview with video monitoring
- Anti-cheating measures:
  - Copy-paste disabled
  - Tab switching detection
  - Continuous face verification
- Question display with timer
- Answer submission (text or audio)
- Interview summary and results

## Pages

- `/login` - Login/Register page
- `/dashboard` - Main dashboard to start interviews
- `/samples` - Upload video/audio samples
- `/interview/[id]` - Interview page
- `/summary/[id]` - Interview results summary

