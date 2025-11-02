import json
import random
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

import spacy


class RomanianNLP:
    def __init__(self):
        self.nlp = self._load_ro_model()

    def _load_ro_model(self):
        try:
            return spacy.load("ro_core_news_sm")
        except Exception:
            # Fallback to multilingual small model if Romanian model is unavailable
            try:
                return spacy.load("xx_sent_ud_sm")
            except Exception:
                # As an absolute fallback, create a blank Romanian pipeline
                return spacy.blank("ro")

    def normalize(self, text: str) -> List[str]:
        doc = self.nlp(text.lower())
        lemmas = []
        for t in doc:
            if t.is_stop or t.is_punct or t.is_space:
                continue
            lemma = (t.lemma_ or t.text).strip().lower()
            if lemma:
                lemmas.append(lemma)
        return lemmas

    def tokenize_set(self, text: str) -> Set[str]:
        return set(self.normalize(text))


class QuestionGenerator:
    """
    Generates exam-style questions and evaluates answers using spaCy-based normalization
    and rule-based keyword coverage. No LLMs are used.
    """

    def __init__(self, knowledge_path: Path):
        if not knowledge_path.exists():
            raise FileNotFoundError(f"Knowledge base not found at {knowledge_path}")
        with open(knowledge_path, "r", encoding="utf-8") as f:
            self.kb: Dict = json.load(f)

        self.available_problems = list(self.kb.keys())
        self.ro_nlp = RomanianNLP()
        self._questions_store: Dict[str, Dict] = {}

    def _build_instance(self, problem_key: str) -> str:
        instances = self.kb[problem_key].get("instances", [])
        if not instances:
            return ""
        return random.choice(instances)

    def generate_question(
        self,
        allowed_problems: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> Dict:
        if seed is not None:
            random.seed(seed)

        problems = (
            [p for p in allowed_problems if p in self.kb]
            if allowed_problems
            else self.available_problems
        )
        if not problems:
            raise ValueError("No valid problems available for generation.")

        problem_key = random.choice(problems)
        instance = self._build_instance(problem_key)

        # Romanian phrasing for the requested deliverable
        # Example:
        # "Pentru problema n-queens (instanță: n=8), care este cea mai potrivită strategie de rezolvare, dintre cele menţionate la curs?"
        problem_label = self.kb[problem_key].get("label_ro", problem_key)
        question_text = (
            f"Pentru problema {problem_label}"
            + (f" (instanță: {instance})" if instance else "")
            + ", care este cea mai potrivită strategie de rezolvare, dintre cele menţionate la curs?"
        )

        qid = str(uuid.uuid4())
        question = {
            "id": qid,
            "problem_key": problem_key,
            "instance": instance,
            "text": question_text,
        }
        self._questions_store[qid] = question
        return question

    def get_reference_answers(self, question_id: str) -> List[str]:
        q = self._questions_store.get(question_id)
        if not q:
            raise KeyError("Question not found.")
        problem_key = q["problem_key"]
        template = self.kb[problem_key].get("answer_template_ro", "")
        # Also include strategy names as acceptable variants
        strategies = self.kb[problem_key].get("strategies", [])
        variants = [template] if template else []
        variants.extend([s.get("name", "") for s in strategies if s.get("name")])
        # Filter empties
        return [v for v in variants if v and v.strip()]

    def evaluate_answer(self, question_id: str, answer_text: str) -> Dict:
        """
        Returns:
          {
            "score": float (0..100),
            "matched_keywords": List[str],
            "missing_keywords": List[str],
            "problem_key": str,
            "best_match_name": str (strategy),
            "explanations": str (reference template),
          }
        """
        q = self._questions_store.get(question_id)
        if not q:
            raise KeyError("Question not found.")

        problem_key = q["problem_key"]
        strategies = self.kb[problem_key].get("strategies", [])
        user_tokens = self.ro_nlp.tokenize_set(answer_text)

        best_score = 0.0
        best_match_name = ""
        best_matched: List[str] = []
        best_missing: List[str] = []

        # Scoring: keyword coverage per strategy, then choose the max.
        # Score = coverage_ratio * 100, with mild bonus for mentioning key heuristics.
        for strat in strategies:
            kw = strat.get("keywords", [])
            kw_tokens = set()
            for term in kw:
                kw_tokens |= self.ro_nlp.tokenize_set(term)

            if not kw_tokens:
                continue

            matched = sorted(list(kw_tokens & user_tokens))
            coverage = len(matched) / len(kw_tokens)
            score = coverage * 100.0

            # Bonus if name of strategy roughly appears
            name = strat.get("name", "")
            name_tokens = self.ro_nlp.tokenize_set(name)
            if name_tokens and name_tokens & user_tokens:
                score += 5.0  # small bonus

            if score > best_score:
                best_score = min(score, 100.0)
                best_match_name = name
                best_matched = matched
                best_missing = sorted(list(kw_tokens - user_tokens))

        explanations = self.kb[problem_key].get("answer_template_ro", "")
        return {
            "score": round(best_score, 1),
            "matched_keywords": best_matched,
            "missing_keywords": best_missing,
            "problem_key": problem_key,
            "best_match_name": best_match_name,
            "explanations": explanations,
        }