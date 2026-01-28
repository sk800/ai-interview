@echo off
echo Setting up AI Interview Automation System...

REM Backend setup
echo Setting up backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if not exist samples mkdir samples
if not exist temp mkdir temp
if not exist .env (
    copy .env.example .env
    echo Please update .env with your API keys
)
cd ..

REM Frontend setup
echo Setting up frontend...
cd frontend
call npm install
if not exist .env.local (
    copy .env.example .env.local
)
cd ..

echo Setup complete!
echo.
echo To start the backend:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn main:app --reload
echo.
echo To start the frontend:
echo   cd frontend
echo   npm run dev

pause

