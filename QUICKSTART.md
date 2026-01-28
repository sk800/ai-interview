# Quick Start Guide

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- OpenRouter API key (get one at https://openrouter.ai)

## Quick Setup (Windows)

1. **Run setup script:**
   ```bash
   setup.bat
   ```

2. **Configure environment:**
   - Edit `backend/.env` and add your `OPENROUTER_API_KEY`
   - Edit `backend/.env` and set a secure `SECRET_KEY`

3. **Start Backend:**
   ```bash
   cd backend
   venv\Scripts\activate
   uvicorn main:app --reload
   ```
   Backend will run on http://localhost:8000

4. **Start Frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on http://localhost:3000

## Quick Setup (Linux/Mac)

1. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment:**
   - Edit `backend/.env` and add your `OPENROUTER_API_KEY`
   - Edit `backend/.env` and set a secure `SECRET_KEY`

3. **Start Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

4. **Start Frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

## First Use

1. Open http://localhost:3000 in your browser
2. Register a new account
3. Upload video and audio samples (10 seconds each)
4. Select an interview type and start the interview
5. Answer 10 questions
6. View your results and summary

## Troubleshooting

### Backend Issues

- **Import errors:** Make sure virtual environment is activated
- **Port already in use:** Change port in `uvicorn main:app --reload --port 8001`
- **Database errors:** Delete `interview.db` and restart
- **Face recognition errors:** Ensure InsightFace models are downloaded (automatic on first use)

### Frontend Issues

- **API connection errors:** Check `NEXT_PUBLIC_API_URL` in `.env.local`
- **Build errors:** Delete `.next` folder and run `npm run dev` again
- **Type errors:** Run `npm install` to ensure all dependencies are installed

### Common Issues

- **Camera/microphone not working:** Check browser permissions
- **Questions not loading:** Verify OpenRouter API key is correct
- **Verification failing:** Ensure good lighting and clear audio in samples

## Production Deployment

See `README.md` for production deployment instructions.

