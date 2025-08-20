# ---------- auto_grader.py ----------
def normalize_choice(ans):
    """Normalize multiple choice answer to uppercase A-E or empty string if invalid."""
    if not ans:
        return ""
    ans = ans.strip().upper()
    if ans and ans[0] in ["A","B","C","D","E"]:
        return ans[0]
    return ans

def grade_mcq(model_answers, student_answers):
    """
    model_answers: list of strings like "Q1: A"
    student_answers: dict { "Q1": "A", "Q2": "C", ... }
    Returns: score (0-100), feedback string
    """
    score = 0
    feedback = ""
    total = len(model_answers)

    for idx, line in enumerate(model_answers):
        if ":" in line:
            q, correct = line.split(":", 1)
            correct = normalize_choice(correct)
            student = normalize_choice(student_answers.get(q.strip(), ""))
            if student == correct and student != "":
                score += 1
                feedback += f"Q{idx+1}: ✅ Correct\n"
            elif student and student != correct:
                feedback += f"Q{idx+1}: ⚠️ Partially Correct ({student})\n"
            else:
                feedback += f"Q{idx+1}: ❌ Missing\n"
    final_score = round(score / total * 100, 2) if total > 0 else 0
    return final_score, feedback

def grade_with_answer_key(model_answer_text, student_text):
    """
    For essays: simply compare strings (placeholder for actual NLP grading)
    Returns: score (0-100), feedback string
    """
    if not student_text.strip():
        return 0, "❌ No answer provided."
    # Example: 100 if exact match, else 50
    score = 100 if student_text.strip() == model_answer_text.strip() else 50
    feedback = "✅ Exact match." if score == 100 else "⚠️ Partial match."
    return score, feedback
