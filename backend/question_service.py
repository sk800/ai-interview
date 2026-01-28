import httpx
import os
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class QuestionService:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.question_bank_path = "question_bank.json"
        self.question_bank = self._load_question_bank()
    
    def _load_question_bank(self) -> Dict:
        """Load questions from question bank file"""
        try:
            if os.path.exists(self.question_bank_path):
                with open(self.question_bank_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading question bank: {str(e)}")
        return {}
    
    async def get_question(self, interview_type: str, question_number: int) -> Dict:
        """Get a question for the interview"""
        # Try to get from question bank first
        if interview_type in self.question_bank and question_number < len(self.question_bank[interview_type]):
            question = self.question_bank[interview_type][question_number]
            return {
                "question": question["question"],
                "type": question.get("type", "text"),
                "time_limit": question.get("time_limit", 300),
                "difficulty": question.get("difficulty", "medium")
            }
        
        # Generate using LLM
        return await self._generate_question_llm(interview_type, question_number)
    
    async def _generate_question_llm(self, interview_type: str, question_number: int) -> Dict:
        """Generate question using OpenRouter API"""
        try:
            difficulty = "easy" if question_number < 3 else "medium" if question_number < 7 else "hard"
            
            prompt = f"""Generate an interview question for a {interview_type} interview.
Question number: {question_number + 1} out of 10
Difficulty: {difficulty}

The question should be:
- Clear and specific
- Appropriate for the difficulty level
- Can be answered in text or spoken format
- Have a time limit of 3-5 minutes

Return ONLY the question text, nothing else."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.openrouter_url,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "You are an expert interview question generator."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 200
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    question_text = data["choices"][0]["message"]["content"].strip()
                    
                    return {
                        "question": question_text,
                        "type": "text",
                        "time_limit": 300,
                        "difficulty": difficulty
                    }
        except Exception as e:
            print(f"Error generating question with LLM: {str(e)}")
        
        # Fallback question
        return {
            "question": f"Tell me about your experience with {interview_type}.",
            "type": "text",
            "time_limit": 300,
            "difficulty": "medium"
        }

