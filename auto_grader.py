# ---------- auto_grader.py (Optimized MCQ + Semantic Grading) ----------
import os
import streamlit as st
from sentence_transformers import SentenceTransformer, util
import re
from PIL import Image  # OCR support if needed

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
    return SentenceTransformer('all-MiniLM-L6-v2')

sbert_model = load_sbert_model()

# ---------- Text Helpers ----------
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def parse_answer_key(key_text):
    key_text = key_text.strip()
    if "\n" in key_text:
        answers = [clean_text(a) for a in key_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in key_text.split(",") if a.strip()]
    return answers

def parse_essay_answers(answer_text):
    answer_text = answer_text.strip()
    if "\n" in answer_text:
        answers = [clean_text(a) for a in answer_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in answer_text.split(",") if a.strip()]
    return answers

# ---------- Optimized Semantic Grading ----------
def grade_with_answer_key(answer_key_text, student_answer_text):
    teacher_answers = parse_answer_key(answer_key_text)
    student_answers = parse_essay_answers(student_answer_text)
    
    if not sbert_model:
        # Fallback: exact match only
        feedback_list = []
        correct_count = 0
        for i, correct_answer in enumerate(teacher_answers):
            if i < len(student_answers) and student_answers[i] == correct_answer:
                correct_count += 1
                feedback_list.append(f"Q{i+1}: ✅ Correct")
            else:
                feedback_list.append(f"Q{i+1}: ❌ Incorrect")
        final_score = round((correct_count / len(teacher_answers)) * 100, 2)
        return final_score, "\n".join(feedback_list)
    
    # Precompute teacher embeddings once
    teacher_embeddings = sbert_model.encode(teacher_answers, convert_to_tensor=True)
    student_embeddings = sbert_model.encode(student_answers, convert_to_tensor=True)
    
    feedback_list = []
    correct_count = 0
    for i, teacher_emb in enumerate(teacher_embeddings):
        if i < len(student_answers):
            student_emb = student_embeddings[i]
            similarity = util.pytorch_cos_sim(student_emb, teacher_emb).item()
            score_pct = round(similarity * 100, 2)
            if score_pct >= 85:
                correct_count += 1
                feedback_list.append(f"Q{i+1}: ✅ Excellent! Similarity: {score_pct}%")
            elif score_pct >= 60:
                correct_count += 0.5  # partial credit
                feedback_list.append(f"Q{i+1}: ⚠️ Partially Correct. Similarity: {score_pct}%")
            else:
                feedback_list.append(f"Q{i+1}: ❌ Incorrect. Similarity: {score_pct}%")
        else:
            feedback_list.append(f"Q{i+1}: ❌ No answer provided")
    
    final_score = round((correct_count / len(teacher_answers)) * 100, 2)
    return final_score, "\n".join(feedback_list)
