from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .question_generator import QuestionGenerator

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "knowledge" / "ai_problems.json"

app = FastAPI(title="AI Question Generator", version="0.1.0")

# Allow localhost frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = QuestionGenerator(KB_PATH)


class GenerateRequest(BaseModel):
    count: int = 1
    allowed_problems: Optional[List[str]] = None
    seed: Optional[int] = None


class EvaluateRequest(BaseModel):
    question_id: str
    answer_text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/questions/generate")
def generate_questions(req: GenerateRequest):
    questions = []
    for i in range(max(1, req.count)):
        q = generator.generate_question(
            allowed_problems=req.allowed_problems, seed=req.seed
        )
        questions.append(q)
    return {"questions": questions}


@app.get("/questions/{question_id}/reference")
def reference_answers(question_id: str):
    try:
        variants = generator.get_reference_answers(question_id)
        return {"question_id": question_id, "reference_answers": variants}
    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")


@app.post("/answers/evaluate")
def evaluate_answer(req: EvaluateRequest):
    try:
        result = generator.evaluate_answer(req.question_id, req.answer_text)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")