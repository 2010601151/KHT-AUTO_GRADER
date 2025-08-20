# ---------- auto_grader.py ----------

def normalize_choice(ans):
    """Normalize multiple choice answer to A-E or return empty string if invalid."""
    if not ans:           # empty string check
        return ""
    ans = ans.strip().upper()
    if ans and ans[0] in ["A","B","C","D","E"]:
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
    Essay grading based on keyword matching, ignoring common stopwords.
    Returns (score_percent, feedback_string)
    """
    import re

    # Basic stopwords list
    stopwords = {
        "the","is","and","a","an","in","on","at","of","to","for","with",
        "by","as","from","that","this","these","those","it","its","be","are","was","were"
    }

    # Extract keywords from model answer
    keywords = set(
        word for word in re.findall(r"\b\w+\b", model_answer_text.lower())
        if word not in stopwords
    )

    # Extract words from student text
    student_words = set(
        word for word in re.findall(r"\b\w+\b", student_text.lower())
        if word not in stopwords
    )

    if not keywords:
        return 0, "No keywords in answer key to grade."

    matched = keywords & student_words
    score = round(len(matched) / len(keywords) * 100, 2)

    feedback_lines = [
        f"Matched keywords: {', '.join(sorted(matched)) if matched else 'None'}",
        f"Missing keywords: {', '.join(sorted(keywords - matched)) if keywords - matched else 'None'}"
    ]
    feedback = "\n".join(feedback_lines)

    return score, feedback
