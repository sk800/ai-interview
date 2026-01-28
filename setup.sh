#!/bin/bash

echo "Setting up AI Interview Automation System..."

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p samples temp
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please update .env with your API keys"
fi
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
if [ ! -f .env.local ]; then
    cp .env.example .env.local
fi
cd ..

echo "Setup complete!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm run dev"

