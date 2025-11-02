import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { generateQuestions, getReference, evaluateAnswer } from "./api";

const problems = [
  { key: "n_queens", label: "n-queens" },
  { key: "graph_coloring", label: "colorarea unui graf" },
  { key: "knights_tour", label: "drumul calului" },
  { key: "generalized_hanoi", label: "Turnurile din Hanoi (generalizat)" }
];

function App() {
  const [selectedProblems, setSelectedProblems] = useState(problems.map(p => p.key));
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [score, setScore] = useState(null);
  const [refAnswers, setRefAnswers] = useState([]);

  const toggleProblem = (key) => {
    setSelectedProblems(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
  };

  const onGenerate = async () => {
    setQuestion(null);
    setAnswer("");
    setScore(null);
    setRefAnswers([]);
    const resp = await generateQuestions({ count: 1, allowed_problems: selectedProblems, seed: Date.now() % 100000 });
    setQuestion(resp.questions[0]);
  };

  const onEvaluate = async () => {
    if (!question || !answer.trim()) return;
    const res = await evaluateAnswer(question.id, answer);
    setScore(res);
    const refs = await getReference(question.id);
    setRefAnswers(refs.reference_answers || []);
  };

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: 20, maxWidth: 900, margin: "0 auto" }}>
      <h1>AI Question Generator</h1>

      <section style={{ marginBottom: 16 }}>
        <h3>Probleme posibile</h3>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {problems.map(p => (
            <label key={p.key} style={{ border: "1px solid #ccc", padding: "6px 10px", borderRadius: 6 }}>
              <input
                type="checkbox"
                checked={selectedProblems.includes(p.key)}
                onChange={() => toggleProblem(p.key)}
                style={{ marginRight: 8 }}
              />
              {p.label}
            </label>
          ))}
        </div>
        <button onClick={onGenerate} style={{ marginTop: 12 }}>Generează întrebare</button>
      </section>

      {question && (
        <section style={{ marginBottom: 16 }}>
          <h3>Întrebare</h3>
          <div style={{ padding: 12, background: "#f8f8f8", borderRadius: 6 }}>
            {question.text}
          </div>
        </section>
      )}

      {question && (
        <section style={{ marginBottom: 16 }}>
          <h3>Răspunsul tău</h3>
          <textarea
            rows={8}
            style={{ width: "100%", padding: 8 }}
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Scrie răspunsul aici (în română)..."
          />
          <div>
            <button onClick={onEvaluate} style={{ marginTop: 8 }}>Evaluează</button>
          </div>
        </section>
      )}

      {score && (
        <section style={{ marginBottom: 16 }}>
          <h3>Evaluare</h3>
          <div style={{ padding: 12, background: "#eef7ee", borderRadius: 6 }}>
            <p><strong>Scor:</strong> {score.score}%</p>
            {score.best_match_name && <p><strong>Strategie potrivită detectată:</strong> {score.best_match_name}</p>}
            {score.matched_keywords?.length > 0 && (
              <p><strong>Cuvinte-cheie potrivite:</strong> {score.matched_keywords.join(", ")}</p>
            )}
            {score.missing_keywords?.length > 0 && (
              <p><strong>Cuvinte-cheie lipsă:</strong> {score.missing_keywords.slice(0, 15).join(", ")}{score.missing_keywords.length > 15 ? " ..." : ""}</p>
            )}
          </div>
        </section>
      )}

      {refAnswers.length > 0 && (
        <section style={{ marginBottom: 16 }}>
          <h3>Răspuns de referință</h3>
          <ul>
            {refAnswers.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);