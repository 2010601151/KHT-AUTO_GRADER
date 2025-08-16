# ---------- auto_grader.py (Fixed & Debug Version) ----------
import os
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ✅ Ensure Hugging Face cache is stored in a persistent folder on Streamlit Cloud
os.environ['HF_HOME'] = '/mount/src/.cache/huggingface'

# ✅ Load SBERT model for semantic grading
@st.cache_resource(show_spinner="🔍 Loading AI model for grading...")
def load_sbert_model():
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        st.success("✅ SBERT model loaded successfully!")
        return model
    except Exception as e:
        st.error(f"⚠️ Failed to load SBERT model: {str(e)}")
        return None  # Fallback if model fails to load

sbert_model = load_sbert_model()

# ✅ Clean text for better matching
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    return text

# ✅ Parse teacher answer key into a list
def parse_answer_key(key_text):
    key_text = key_text.strip()
    if "\n" in key_text:
        answers = [clean_text(a) for a in key_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in key_text.split(",") if a.strip()]
    return answers

# ✅ Parse student answers into a list
def parse_student_answers(answer_text):
    answer_text = answer_text.strip()
    if "\n" in answer_text:
        answers = [clean_text(a) for a in answer_text.split("\n") if a.strip()]
    else:
        answers = [clean_text(a) for a in answer_text.split(",") if a.strip()]
    return answers

# ✅ Main grading function (step-by-step)
def grade_with_answer_key(answer_key_text, student_answer_text):
    teacher_answers = parse_answer_key(answer_key_text)
    student_answers = parse_student_answers(student_answer_text)

    total_questions = len(teacher_answers)
    correct_count = 0
    feedback_list = []

    for i, correct_answer in enumerate(teacher_answers):
        if i < len(student_answers):
            student_ans = student_answers[i]

            # For MCQs and True/False: exact match
            if student_ans == correct_answer:
                correct_count += 1
                feedback_list.append(f"Q{i+1}: ✅ Correct")
            else:
                # For short/long answers: semantic similarity (only if model loaded)
                if sbert_model:
                    score, _ = grade_answer_bert(correct_answer, student_ans)
                    st.write(f"Debug: Q{i+1} similarity = {score}%")  # 🔍 Debug output
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

# ✅ BERT semantic grading function
def grade_answer_bert(model_answer, student_answer):
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
