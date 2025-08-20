# ---------- auto_grader.py ----------

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
            feedback += f"Q{idx+1}: ⚠️ Partially Correct ({student})\n"
        else:
            feedback += f"Q{idx+1}: ❌ Missing\n"

    final_score = round(score / total * 100, 2) if total > 0 else 0
    return final_score, feedback

def grade_with_answer_key(model_answer_text, student_text):
    """
    Placeholder for essay grading. For now, just returns 0.
    Can be replaced with AI scoring.
    """
    # Simple example: just dummy score
    score = 0
    feedback = "Essay grading not implemented yet."
    return score, feedback
