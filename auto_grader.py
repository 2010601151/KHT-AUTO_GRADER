# ---------- auto_grader.py ----------
import difflib

# ------------------ MCQ Functions ------------------
def parse_mcq_answers(text):
    """
    Parse student MCQ answers from text.
    Expects lines like "1. A", "2) B", "3-C" etc.
    Returns a list of answers in order.
    """
    answers = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Try to find letter answer
        for part in line.split():
            if part.upper() in ["A","B","C","D","E"]:
                answers.append(part.upper())
                break
    return answers

def grade_mcq(answer_key, student_answers):
    """
    Grade MCQ.
    answer_key: list of correct letters ["A","C","B",...]
    student_answers: list of student letters ["A","C","D",...]
    Returns score (percentage) and feedback string.
    """
    total = len(answer_key)
    correct_count = 0
    feedback_lines = []
    for i, correct in enumerate(answer_key):
        try:
            student = student_answers[i]
        except IndexError:
            student = ""
        if student.upper() == correct.upper():
            correct_count += 1
            feedback_lines.append(f"{i+1}. ✅ Correct ({student})")
        elif student == "":
            feedback_lines.append(f"{i+1}. ❌ No Answer (Expected {correct})")
        else:
            feedback_lines.append(f"{i+1}. ❌ Wrong ({student}, Expected {correct})")
    score = round((correct_count/total)*100,2) if total>0 else 0
    feedback = "\n".join(feedback_lines)
    return score, feedback

# ------------------ Essay / Text Functions ------------------
def grade_with_answer_key(answer_key_text, student_text):
    """
    Simple essay / free-text grading using similarity.
    Returns a percentage score and basic feedback.
    """
    # Split lines and normalize
    key_lines = [line.strip().lower() for line in answer_key_text.splitlines() if line.strip()]
    student_lines = [line.strip().lower() for line in student_text.splitlines() if line.strip()]

    # If empty student text, score 0
    if not student_lines:
        feedback = "❌ No answer provided."
        return 0, feedback

    # Compute similarity line by line
    total = len(key_lines)
    if total == 0:
        return 0, "⚠️ No answer key to grade."

    matched_count = 0
    feedback_lines = []
    for i, key in enumerate(key_lines):
        # Get corresponding student line if exists
        try:
            student_line = student_lines[i]
        except IndexError:
            student_line = ""
        ratio = difflib.SequenceMatcher(None, key, student_line).ratio()
        percent = int(ratio*100)
        if ratio > 0.85:
            feedback_lines.append(f"{i+1}. ✅ Excellent match ({percent}%)")
            matched_count += 1
        elif ratio > 0.6:
            feedback_lines.append(f"{i+1}. ⚠️ Partial match ({percent}%)")
            matched_count += 0.5
        else:
            feedback_lines.append(f"{i+1}. ❌ Low match ({percent}%)")
    score = round((matched_count/total)*100,2)
    feedback = "\n".join(feedback_lines)
    return score, feedback
