const BASE = "http://localhost:8000";

export async function generateQuestions({ count = 1, allowed_problems = null, seed = null } = {}) {
  const res = await fetch(`${BASE}/questions/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count, allowed_problems, seed })
  });
  if (!res.ok) throw new Error("Failed to generate questions");
  return res.json();
}

export async function getReference(questionId) {
  const res = await fetch(`${BASE}/questions/${questionId}/reference`);
  if (!res.ok) throw new Error("Failed to get reference answers");
  return res.json();
}

export async function evaluateAnswer(question_id, answer_text) {
  const res = await fetch(`${BASE}/answers/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_id, answer_text })
  });
  if (!res.ok) throw new Error("Failed to evaluate answer");
  return res.json();
}