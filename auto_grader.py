# ---------- auto_grader.py (Updated & Fixed MCQ + Semantic Grading) ----------
import os
import streamlit as st
from sentence_transformers import SentenceTransformer, util
import re
from PIL import Image  # For future OCR support if needed

# ---------- MCQ Helpers ----------
def normalize_choice(answer):
    """Normalize student answer to single capital letter A-E"""
    if not answer:
        return ""
    ans = str(answer).strip().upper()
    if len(ans) == 1 and ans in ["A","B","C","D","E"]:
        return ans
    if ans[0] in ["A","B","C","D","E"]:
        return ans[0]
    return ans

def parse_mcq_answers(answer_text):
    """Parse MCQ student answers line by line, ignore numbering/punctuation"""
    answers = []
    for line in answer_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove numbering or punctuation (e.g., "1. A" -> "A")
        line = re.sub(r'^\d+\s*[\.\)-]*\s*', '', line)
        answers.append(normalize_choice(line))
    return answers

def grade_mcq(teacher_key, student_answers):
    """Grade multiple choice answers"""
    feedback = []
    score = 0
    for i, correct in enumerate(teacher_key):
        student = student_answers[i] if i < len(student_answers) else ""
        if normalize_choice(student) == normalize_choice(correct):
            score += 1
            feedback.append(f"Q{i+1}: ✅ Correct")
        else:
            feedback.append(f"Q{i+1}: ❌ Incorrect (Expected {correct}, got {student})")
    final_score = round((score / len(teacher_key)) * 100, 2) if teacher_key else 0
    return final_score, "\n".join(feedback)

# ---------- SBERT / Semantic Grading Setup ----------
os.environ['HF_HOME'] = '/mount/src/.cache/huggingface'

@st.cache_resource(show_spinner="🔍 Loading AI model for grading...")
def load_sbert_model():
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        st.success("✅ SBERT model loaded successfully!")
        return model
    except Exception as e:
        st.error(f"⚠️ Failed to load SBERT model: {str(e)}")
        return None

sbert_model = load_sbert_model()

# ---------- Essay / Semantic Grading Helpers ----------
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def parse_answer_key(key_text):
    """Parse teacher's key into cleaned list"""
    key_text = key_text.strip()
    if "\n" in key_text:
        answers = [clean_text(a) for a in key_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in key_text.split(",") if a.strip()]
    return answers

def parse_essay_answers(answer_text):
    """Parse student essay answers into cleaned list"""
    answer_text = answer_text.strip()
    if "\n" in answer_text:
        answers = [clean_text(a) for a in answer_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in answer_text.split(",") if a.strip()]
    return answers

def grade_with_answer_key(answer_key_text, student_answer_text):
    """Grade essay / semantic answers using SBERT"""
    teacher_answers = parse_answer_key(answer_key_text)
    student_answers = parse_essay_answers(student_answer_text)

    total_questions = len(teacher_answers)
    correct_count = 0
    feedback_list = []

    for i, correct_answer in enumerate(teacher_answers):
        if i < len(student_answers):
            student_ans = student_answers[i]
            if student_ans == correct_answer:
                correct_count += 1
                feedback_list.append(f"Q{i+1}: ✅ Correct")
            else:
                if sbert_model:
                    score, fb = grade_answer_bert(correct_answer, student_ans)
                    if score >= 80:
                        correct_count += 1
                        feedback_list.append(f"Q{i+1}: ⚠️ Partially Correct (Similarity: {score}%)")
                    else:
                        feedback_list.append(f"Q{i+1}: ❌ Incorrect (Expected: {correct_answer})")
                else:
                    feedback_list.append(f"Q{i+1}: ❌ Incorrect (Model unavailable)")
        else:
            feedback_list.append(f"Q{i+1}: ❌ No answer provided")

    final_score = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0
    return final_score, "\n".join(feedback_list)

def grade_answer_bert(model_answer, student_answer):
    """Compute semantic similarity score and provide feedback"""
    try:
        model_answer = clean_text(model_answer)
        student_answer = clean_text(student_answer)
        embeddings = sbert_model.encode([student_answer, model_answer], convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
        score = round(similarity * 100, 2)

        if score >= 85:
            feedback = "✅ Excellent! Your answer is very close in meaning."
        elif score >= 60:
            feedback = "⚠️ Fair. You understood part of the answer."
        else:
            feedback = "❌ Needs improvement. Try reviewing the topic."

        return score, feedback
    except Exception as e:
        return 0, f"⚠️ Error in BERT grading: {str(e)}"
