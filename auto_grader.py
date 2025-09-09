# ---------- auto_grader.py ----------

import re
import os
from difflib import SequenceMatcher

# ------------------------
# MULTIPLE CHOICE GRADING
# ------------------------

def normalize_choice(ans):
    """Normalize multiple choice answer to A-E or return empty string if invalid."""
    if not ans or len(ans.strip()) == 0:  # handle empty or whitespace-only
        return ""
    ans = ans.strip().upper()
    if ans[0] in ["A", "B", "C", "D", "E"]:
        return ans[0]
    return ""

def grade_mcq(model_answers, student_answers):
    """
    Grade multiple choice questions.
    model_answers: list of strings like 'Q1: A'
    student_answers: dict of {'Q1': 'B', 'Q2': 'A'}
    Returns (score_percent, feedback_string)
    """
    score = 0
    feedback = ""
    total = len(model_answers)

    for idx, line in enumerate(model_answers):
        if ":" not in line:
            continue
        q, correct = line.split(":", 1)
        q = q.strip()
        correct = correct.strip()
        student = student_answers.get(q, "").strip()

        norm_student = normalize_choice(student)
        norm_correct = normalize_choice(correct)

        if norm_student == norm_correct and norm_student != "":
            score += 1
            feedback += f"Q{idx+1}: ✅ Correct\n"
        elif norm_student != "" and norm_student != norm_correct:
            feedback += f"Q{idx+1}: ❌ Incorrect (Your answer: {student})\n"
        else:
            feedback += f"Q{idx+1}: ⚠️ Missing answer\n"

    final_score = round(score / total * 100, 2) if total > 0 else 0
    return final_score, feedback


# ------------------------
# ESSAY GRADING (AI-POWERED with fallback)
# ------------------------

USE_AI = True  # ✅ AI grading enabled

def grade_with_answer_key(model_answer_text, student_text):
    """
    Essay grading: AI-powered if API key available, fallback to similarity if not.
    """

    if not model_answer_text.strip() or not student_text.strip():
        return 0, "⚠️ Missing answer or answer key."

    if USE_AI:
        import openai, json

        # --- Secure key handling ---
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 🔧 Fallback: paste your key here if env var not set
            api_key = "your-real-api-key-here"

        if api_key and not api_key.startswith("your-real"):
            openai.api_key = api_key
        else:
            # fallback: no key found
            return _simple_similarity_grading(model_answer_text, student_text, note="⚠️ No API key found. Using simple grading.")

        prompt = f"""
You are an academic grader. 
Grade the following student essay based on the teacher's model answer. 
Give a score out of 100 and provide short feedback.

Model Answer:
{model_answer_text}

Student Essay:
{student_text}

Return result in this JSON format:
{{
  "score": <number>,
  "feedback": "<short feedback>"
}}
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # ✅ lightweight + fast
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            result = json.loads(response.choices[0].message["content"])
            score = result.get("score", 0)
            feedback = result.get("feedback", "No feedback generated.")

        except Exception as e:
            # fallback if API call fails
            score, feedback = _simple_similarity_grading(model_answer_text, student_text, note=f"⚠️ AI grading failed: {e}")

    else:
        # offline similarity mode
        score, feedback = _simple_similarity_grading(model_answer_text, student_text)

    return score, feedback


# ------------------------
# SIMPLE SIMILARITY FALLBACK
# ------------------------

def _simple_similarity_grading(model_answer_text, student_text, note=""):
    """Fallback essay grading using simple text similarity."""
    key = re.sub(r'\s+', ' ', model_answer_text.lower())
    student = re.sub(r'\s+', ' ', student_text.lower())

    ratio = SequenceMatcher(None, key, student).ratio()
    score = round(ratio * 100, 2)

    if score > 85:
        feedback = "✅ Excellent coverage of key ideas."
    elif score > 65:
        feedback = "⚠️ Partial match — student covered some important points but missed details."
    else:
        feedback = "❌ Weak match — student missed most of the key points."

    if note:
        feedback = f"{note}\n{feedback}"

    return score, feedback
