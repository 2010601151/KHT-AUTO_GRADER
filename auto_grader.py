# auto_grader.py
import re

# --- Parse student answers for MCQs ---
def parse_student_answers(student_text):
    """
    Converts student answers into a dict: {Q1: 'A', Q2: 'B', ...}
    """
    answers = {}
    lines = student_text.splitlines()
    for line in lines:
        line = line.strip()
        match = re.match(r"Q?(\d+)\s*[:.-]?\s*([A-D])", line, re.IGNORECASE)
        if match:
            qnum = int(match.group(1))
            ans = match.group(2).upper()
            answers[qnum] = ans
    return answers

# --- Grade MCQs ---
def grade_mcq(answer_key_lines, student_answers, return_wrong=False):
    """
    Returns score and feedback for MCQ.
    answer_key_lines: list of 'Q1: A' strings
    student_answers: dict {Q1: 'A'}
    """
    total = len(answer_key_lines)
    correct = 0
    feedback_lines = []
    wrong_questions = {}

    for idx, line in enumerate(answer_key_lines, start=1):
        match = re.match(r"Q?(\d+)\s*[:.-]?\s*([A-D])", line.strip(), re.IGNORECASE)
        if match:
            qnum = int(match.group(1))
            correct_ans = match.group(2).upper()
            student_ans = student_answers.get(qnum)
            if student_ans == correct_ans:
                feedback_lines.append(f"✅ Q{qnum}: Correct")
                correct += 1
            elif student_ans is None:
                feedback_lines.append(f"❌ Q{qnum}: No answer provided (Correct: {correct_ans})")
                wrong_questions[qnum] = correct_ans
            else:
                feedback_lines.append(f"❌ Q{qnum}: Wrong answer ({student_ans}) → Correct: {correct_ans}")
                wrong_questions[qnum] = correct_ans

    score = round((correct / total) * 100, 2) if total > 0 else 0

    if return_wrong:
        return score, "\n".join(feedback_lines), wrong_questions
    return score, "\n".join(feedback_lines)

# --- Grade Essay ---
def grade_with_answer_key(answer_key_text, student_text):
    """
    Returns score, feedback, and missing points.
    """
    key_points = [line.strip() for line in answer_key_text.splitlines() if line.strip()]
    student_lines = [line.strip() for line in student_text.splitlines() if line.strip()]

    matched = 0
    feedback = []
    missing_points = []

    for point in key_points:
        if any(point.lower() in s.lower() for s in student_lines):
            feedback.append(f"✅ Point covered: {point}")
            matched += 1
        else:
            feedback.append(f"❌ Missing: {point}")
            missing_points.append(point)

    score = round((matched / len(key_points)) * 100, 2) if key_points else 0
    return score, "\n".join(feedback), missing_points
