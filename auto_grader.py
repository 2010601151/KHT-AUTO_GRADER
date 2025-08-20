# ---------- auto_grader.py ----------
import difflib
from sentence_transformers import SentenceTransformer, util

# ------------------ MCQ Functions ------------------
def parse_mcq_answers(text):
    answers = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for part in line.split():
            if part.upper() in ["A","B","C","D","E"]:
                answers.append(part.upper())
                break
    return answers

def grade_mcq(answer_key, student_answers):
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

# ------------------ Semantic Essay Grader ------------------
model = SentenceTransformer('all-MiniLM-L6-v2')  # lightweight & fast

def grade_with_answer_key(answer_key_text, student_text):
    key_lines = [line.strip() for line in answer_key_text.splitlines() if line.strip()]
    student_lines = [line.strip() for line in student_text.splitlines() if line.strip()]

    if not student_lines:
        return 0, "❌ No answer provided."
    if not key_lines:
        return 0, "⚠️ No answer key to grade."

    # Embed sentences
    key_embeddings = model.encode(key_lines, convert_to_tensor=True)
    student_embeddings = model.encode(student_lines, convert_to_tensor=True)

    feedback_lines = []
    total_score = 0
    matched_sentences = []  # keep track for highlights

    for i, key_emb in enumerate(key_embeddings):
        similarities = util.cos_sim(key_emb, student_embeddings)[0]
        max_idx = int(similarities.argmax())
        sim_score = float(similarities[max_idx])
        percent = round(sim_score * 100, 2)

        if sim_score > 0.85:
            feedback_lines.append(f"{i+1}. ✅ Excellent match ({percent}%) → {student_lines[max_idx]}")
            total_score += 1
            matched_sentences.append(student_lines[max_idx])
        elif sim_score > 0.6:
            feedback_lines.append(f"{i+1}. ⚠️ Partial match ({percent}%) → {student_lines[max_idx]}")
            total_score += 0.5
            matched_sentences.append(student_lines[max_idx])
        else:
            feedback_lines.append(f"{i+1}. ❌ Low match ({percent}%) → {student_lines[max_idx]}")

    score = round((total_score / len(key_lines)) * 100, 2)
    feedback = "\n".join(feedback_lines)
    return score, feedback, matched_sentences

# ------------------ Batch Essay Grader ------------------
def grade_essay_batch(answer_key_text, student_files):
    """
    Grades multiple essays at once, returns a list of dicts:
    [{'Name':..., 'ID':..., 'Score':..., 'Feedback':..., 'Matched':...}, ...]
    """
    results = []
    for info in student_files:
        student_answer = info['Answer']
        student_name = info.get('Name', 'Unknown')
        student_id = info.get('ID', '0000')
        score, feedback, matched = grade_with_answer_key(answer_key_text, student_answer)
        results.append({
            'Name': student_name,
            'ID': student_id,
            'Answer': student_answer,
            'Score': score,
            'Feedback': feedback,
            'Matched': matched
        })
    return results
