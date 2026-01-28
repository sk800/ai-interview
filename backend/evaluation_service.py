import httpx
import os
from typing import Dict, List
from dotenv import load_dotenv
from models import Interview, Answer

load_dotenv()

class EvaluationService:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def evaluate_answer(self, question: str, answer: str, interview_type: str) -> Dict:
        """Evaluate an answer and provide score and feedback"""
        try:
            prompt = f"""Evaluate the following interview answer.

Interview Type: {interview_type}
Question: {question}
Answer: {answer}

Provide:
1. A score from 0 to 100
2. Detailed feedback on the answer

Return your response in JSON format:
{{
    "score": <number>,
    "feedback": "<detailed feedback>"
}}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.openrouter_url,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are an expert interview evaluator. Always respond with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    
                    # Try to parse JSON from response
                    import json
                    try:
                        # Extract JSON from markdown code blocks if present
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                        
                        evaluation = json.loads(content)
                        return {
                            "score": float(evaluation.get("score", 50)),
                            "feedback": evaluation.get("feedback", "No feedback provided")
                        }
                    except json.JSONDecodeError:
                        # Fallback parsing
                        score = 50
                        feedback = content
                        if "score" in content.lower():
                            try:
                                score_str = content.split("score")[1].split()[0].replace(":", "").replace(",", "")
                                score = float(score_str)
                            except:
                                pass
                        
                        return {
                            "score": score,
                            "feedback": feedback
                        }
        except Exception as e:
            print(f"Error evaluating answer: {str(e)}")
        
        # Fallback evaluation
        return {
            "score": 50.0,
            "feedback": "Answer received. Evaluation pending."
        }
    
    async def generate_summary(self, interview: Interview, answers: List[Answer], db=None) -> str:
        """Generate final interview summary"""
        try:
            # Build answers text
            answers_text_parts = []
            for i, answer in enumerate(answers):
                # Get question text from database if available
                if db:
                    from models import Question
                    question = db.query(Question).filter(Question.id == answer.question_id).first()
                    question_text = question.question_text if question else "Question not found"
                else:
                    question_text = "Question"
                answers_text_parts.append(f"Q{i+1}: {question_text}\nA{i+1}: {answer.answer_text}\nScore: {answer.score}\n")
            answers_text = "\n".join(answers_text_parts)
            
            total_score = sum(answer.score for answer in answers)
            average_score = total_score / len(answers) if answers else 0
            
            prompt = f"""Generate a comprehensive interview summary.

Interview Type: {interview.interview_type}
Total Questions: {len(answers)}
Average Score: {average_score:.2f}/100

Questions and Answers:
{answers_text}

Provide a detailed summary including:
1. Overall performance assessment
2. Strengths
3. Areas for improvement
4. Final recommendation

Be professional and constructive."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.openrouter_url,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are an expert interview evaluator providing comprehensive feedback."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
        
        # Fallback summary
        total_score = sum(answer.score for answer in answers)
        average_score = total_score / len(answers) if answers else 0
        return f"Interview completed. Average score: {average_score:.2f}/100. Review your answers for detailed feedback."

