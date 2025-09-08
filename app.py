# === app_professional.py ===
# Polished KHT AI Auto-Grader (preserves original behavior; improved structure & helpers)
import os
import re
import json
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image
import pytesseract

# optional essay grader imported from your module (keeps original behavior)
try:
    from auto_grader import grade_with_answer_key
except Exception:
    # If unavailable, provide a placeholder that returns neutral feedback
    def grade_with_answer_key(model, student_text):
        return 0, "⚠️ Essay grading module not available."

# =============================
# Configuration & Page Setup
# =============================
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# Secure-ish admin password: read from env var if present, else fallback to test default
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# =============================
# Minimal CSS (kept visually similar)
# =============================
st.markdown("""
<style>
.stApp { 
    background-color:#ffffff; 
    color:#000000 !important; 
}
section[data-testid="stSidebar"] { 
    background-color: #4a0072; 
    padding-top: 2rem; 
}
section[data-testid="stSidebar"] * { 
    color:#ffffff !important; 
}
.login-card { 
    background-color:#ffffff; 
    color:#000000 !important; 
    padding: 1.25rem; 
    border-radius: 10px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.12); 
    max-width: 320px; 
    margin: 1.5rem auto; 
}
.notification { 
    color:black; 
    font-weight:600; 
    font-size:15px; 
    padding:6px 10px; 
    border-radius:6px; 
}
.ocr-box { 
    background:#f7f7f7; 
    padding:10px; 
    border-radius:6px; 
    max-height:300px; 
    overflow:auto; 
    font-size:14px; 
}
.feedback-correct { 
    background-color:#28a745; 
    color:black; 
    font-weight:700; 
    padding:3px 6px; 
    border-radius:4px; 
}
.feedback-partial { 
    background-color:#ffc107; 
    color:black; 
    font-weight:700; 
    padding:3px 6px; 
    border-radius:4px; 
}
.feedback-wrong { 
    background-color:#dc3545; 
    color:black; 
    font-weight:700; 
    padding:3px 6px; 
    border-radius:4px; 
}

/* ✅ Make ALL buttons purple with white text */
div.stButton > button {
    background-color:#6a1b9a !important; /* purple */
    color:#ffffff !important;            /* white text */
    font-weight:bold;
    border:none;
    border-radius:6px;
    padding:0.5em 1em;
}
div.stButton > button:hover {
    background-color:#4a0072 !important; /* darker purple on hover */
    color:#ffffff !important;
}
</style>

# =============================
# App Header
# =============================
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# =============================
# Helper utilities
# =============================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_text_from_image(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""

def load_teachers() -> dict:
    return load_json("teachers.json")

def save_teachers(data: dict) -> None:
    save_json("teachers.json", data)

def load_pending_teachers() -> dict:
    return load_json("pending_teachers.json")

def save_pending_teachers(data: dict) -> None:
    save_json("pending_teachers.json", data)

def load_answer_key() -> str:
    try:
        return json.load(open("answer_key.json", "r")).get("key", "")
    except Exception:
        return ""

def save_answer_key(text: str) -> None:
    save_json("answer_key.json", {"key": text})

def color_rows(val: float) -> str:
    if val >= 85:
        return 'background-color:#d4edda'
    if val >= 60:
        return 'background-color:#fff3cd'
    return 'background-color:#f8d7da'

# =============================
# MCQ Parsing & Grading Helpers
# =============================
def parse_student_answers(text: str) -> dict:
    """
    Convert OCR/text answers into {qnum: answer}.
    Handles:
      - Numbered lines: "1. A", "2) B", "3: C"
      - Single-line tokens: "A B C D" -> mapped to 1..n
      - Fallback: return {1: raw_text}
    """
    text = (text or "").strip()
    if not text:
        return {}

    qdict = {}
    lines = [ln.strip() for ln in re.split(r'[\r\n]+', text) if ln.strip()]
    number_answer_pattern = re.compile(r'^\s*(\d{1,3})\s*[\.\:\)\-]?\s*([A-Za-z0-9]+)\s*$')

    for ln in lines:
        m = number_answer_pattern.match(ln)
        if m:
            qdict[int(m.group(1))] = m.group(2).upper().strip()

    if qdict:
        return qdict

    tokens = re.split(r'[\s,;]+', text)
    tokens = [t.strip() for t in tokens if t.strip()]
    if len(tokens) > 1 and all(re.match(r'^[A-Za-z0-9]$', t) for t in tokens):
        return {i+1: tokens[i].upper() for i in range(len(tokens))}

    pairs = re.findall(r'(\d{1,3})\s*[:\.\)\-]?\s*([A-Za-z0-9])', text)
    if pairs:
        return {int(q): a.upper() for q, a in pairs}

    return {1: text.strip()}

def grade_mcq(model_lines: list, student_answers) -> tuple:
    """
    Grade MCQ answers against model lines (list of strings).
    Returns (score_percent, feedback_text)
    """
    pattern = re.compile(r'^\s*(\d{1,3})\s*[\.\:\)\-]?\s*([A-Za-z0-9]+)\s*$')
    model_key = {}

    lines = [ln.strip() for ln in model_lines if ln and ln.strip()]
    for ln in lines:
        m = pattern.match(ln)
        if m:
            model_key[int(m.group(1))] = m.group(2).upper().strip()

    if not model_key:
        # maybe the model is single-line tokens (A B C D)
        tokens = []
        for ln in lines:
            tokens += re.split(r'[\s,;]+', ln)
        tokens = [t for t in tokens if t.strip()]
        if tokens:
            model_key = {i+1: tokens[i].upper() for i in range(len(tokens))}

    if not model_key:
        return 0, "❌ Unable to parse model answer key."

    if not isinstance(student_answers, dict):
        student_answers = parse_student_answers(student_answers)

    total = len(model_key)
    correct = 0
    feedback = []

    for q in sorted(model_key.keys()):
        correct_answer = model_key[q]
        s_ans = student_answers.get(q, "").upper().strip()
        if not s_ans:
            feedback.append(f"Q{q}: ⚠️ Missing answer (Correct: {correct_answer})")
        elif s_ans == correct_answer:
            correct += 1
            feedback.append(f"Q{q}: ✅ {s_ans} (Correct)")
        else:
            feedback.append(f"Q{q}: ❌ {s_ans} (Correct: {correct_answer})")

    score_pct = round((correct / total) * 100, 2) if total else 0.0
    return score_pct, "\n".join(feedback)

# =============================
# Session State
# =============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "remove_teacher" not in st.session_state:
    st.session_state.remove_teacher = None
if "approve_teacher" not in st.session_state:
    st.session_state.approve_teacher = None

# =============================
# Sidebar (Login & Navigation)
# =============================
st.sidebar.markdown("<h2 style='color:#ffffff; text-align:center;'>KHT AI AUTO GRADER</h2>", unsafe_allow_html=True)
login_type = st.sidebar.radio("Login as:", ["Admin", "Teacher"])

if not st.session_state.authenticated:
    if login_type == "Admin":
        st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.sidebar.subheader("🔐 Admin Login")
        admin_user = st.sidebar.text_input("Username")
        admin_pass = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login as Admin"):
            if admin_user == ADMIN_USERNAME and hash_password(admin_pass) == ADMIN_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

    if login_type == "Teacher":
        st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.sidebar.subheader("🔐 Teacher Login / Register")
        teachers = load_teachers()
        pending_teachers = load_pending_teachers()
        teacher_user = st.sidebar.text_input("Username")
        teacher_pass = st.sidebar.text_input("Password", type="password")
        login_btn = st.sidebar.button("Login as Teacher")
        register_btn = st.sidebar.button("Register Teacher")
        if login_btn:
            if teacher_user in teachers and teachers[teacher_user] == hash_password(teacher_pass):
                st.session_state.authenticated = True
                st.session_state.role = "Teacher"
                st.rerun()
            else:
                st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
        if register_btn:
            if teacher_user in teachers or teacher_user in pending_teachers:
                st.sidebar.markdown("<p class='notification'>❌ Username already exists.</p>", unsafe_allow_html=True)
            elif teacher_user and teacher_pass:
                pending_teachers[teacher_user] = hash_password(teacher_pass)
                save_pending_teachers(pending_teachers)
                st.sidebar.markdown("<p class='notification'>✅ Registration submitted for admin approval!</p>", unsafe_allow_html=True)
            else:
                st.sidebar.markdown("<p class='notification'>⚠️ Enter username and password to register.</p>", unsafe_allow_html=True)
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

# Navigation pages (different for Admin vs Teacher)
if st.session_state.role == "Admin":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📊 Admin Dashboard",
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📈 Analytics"
    ])
elif st.session_state.role == "Teacher":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📊 View Dashboard",
        "📈 Analytics"
    ])
else:
    st.stop()

# =============================
# Admin Dashboard
# =============================
if page == "📊 Admin Dashboard" and st.session_state.role == "Admin":
    teachers = load_teachers()
    pending_teachers = load_pending_teachers()
    st.subheader("👤 Manage Teachers & Approvals")
    st.markdown("### ✅ Approved Teachers")
    for username, pwd_hash in teachers.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {pwd_hash}")
        if col3.button("Remove", key=f"remove_{username}"):
            st.session_state.remove_teacher = username

    # remove action
    if st.session_state.remove_teacher:
        rm = st.session_state.remove_teacher
        if rm in teachers:
            teachers.pop(rm)
            save_teachers(teachers)
            st.success(f"Removed teacher: {rm}")
        st.session_state.remove_teacher = None
        st.rerun()

    st.markdown("### ⏳ Pending Teacher Registrations")
    for username, pwd_hash in pending_teachers.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {pwd_hash}")
        if col3.button("Approve", key=f"approve_{username}"):
            st.session_state.approve_teacher = username

    teacher_to_approve = st.session_state.get("approve_teacher", None)
    if teacher_to_approve and teacher_to_approve in pending_teachers:
        teachers[teacher_to_approve] = pending_teachers.pop(teacher_to_approve)
        save_teachers(teachers)
        save_pending_teachers(pending_teachers)
        st.success(f"Approved teacher: {teacher_to_approve}")
        st.session_state.approve_teacher = None
        st.rerun()

# =============================
# Upload & Grade (Shared)
# =============================
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"]:
    st.subheader("Upload & Grade Student Exam")

    mode = st.radio("Select Exam Section", ["Multiple Choice", "Essay"])
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    batch_mode = st.checkbox("Enable Batch Grading (Upload multiple files)")

    if mode == "Multiple Choice":
        key_file_label = "Upload Teacher's MCQ Key"
        student_file_label = "Upload Student MCQ Answers (scan or text)"
    else:
        key_file_label = "Upload Teacher's Essay Key"
        student_file_label = "Upload Student Essay (scan or text)"

    st.markdown("### Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader(key_file_label, type=["txt", "jpg", "jpeg", "png"])
    if key_file:
        if key_file.type.startswith("text"):
            teacher_key = key_file.read().decode("utf-8").strip()
        else:
            teacher_key = extract_text_from_image(Image.open(key_file))
        save_answer_key(teacher_key)
        st.markdown(f"<div class='ocr-box'><pre>{teacher_key}</pre></div>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

    model_answer = load_answer_key()
    if not model_answer:
        st.markdown("<p class='notification'>⚠️ Please upload the answer key first.</p>", unsafe_allow_html=True)
        st.stop()

    # Single student grading
    if not batch_mode:
        student_name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        student_file = st.file_uploader(student_file_label, type=["txt", "jpg", "jpeg", "png"])

        if student_file and st.button("Grade Student"):
            if student_file.type.startswith("text"):
                student_answer = student_file.read().decode("utf-8").strip()
            else:
                student_answer = extract_text_from_image(Image.open(student_file))

            if mode == "Multiple Choice":
                student_answers = parse_student_answers(student_answer)
                score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)

            st.markdown(f"<p class='notification'>Score: {score}</p>", unsafe_allow_html=True)
            st.markdown("<p class='notification'>Detailed Feedback:</p>", unsafe_allow_html=True)
            for line in feedback.split("\n"):
                cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

            # Save result
            result = {
                "Student ID": student_id or "Unknown",
                "Name": student_name or "Unknown",
                "Department": department,
                "Subject": subject,
                "Answer": student_answer,
                "Score": score,
                "Feedback": feedback,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_path = f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            try:
                df = pd.read_csv(save_path)
                df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
            except Exception:
                df = pd.DataFrame([result])
            df.to_csv(save_path, index=False)
            st.success("Result saved successfully!")

    # Batch grading
    else:
        batch_files = st.file_uploader(f"Upload Multiple {mode} Files", type=["txt", "jpg", "jpeg", "png"], accept_multiple_files=True)
        if batch_files and st.button("Grade All Exams"):
            results = []
            for file in batch_files:
                if file.type.startswith("text"):
                    student_answer = file.read().decode("utf-8").strip()
                else:
                    student_answer = extract_text_from_image(Image.open(file))

                student_name, student_id = "Unknown", "0000"
                try:
                    for line in student_answer.splitlines():
                        lc = line.strip()
                        if lc.lower().startswith("name:"):
                            student_name = lc.split(":", 1)[1].strip()
                        elif lc.lower().startswith("id:"):
                            student_id = lc.split(":", 1)[1].strip()
                    parts = os.path.splitext(file.name)[0].split("_")
                    if (student_name == "Unknown" or student_id == "0000") and len(parts) >= 2:
                        student_name, student_id = parts[0], parts[1]
                except Exception:
                    pass

                if mode == "Multiple Choice":
                    student_answers = parse_student_answers(student_answer)
                    score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
                else:
                    score, feedback = grade_with_answer_key(model_answer, student_answer)

                results.append({
                    "Student ID": student_id or "Unknown",
                    "Name": student_name or "Unknown",
                    "Department": department,
                    "Subject": subject,
                    "Answer": student_answer,
                    "Score": score,
                    "Feedback": feedback,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                st.markdown(f"<p class='notification'>Graded {student_name} ({student_id}) → Score: {score}</p>", unsafe_allow_html=True)

            save_path = f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            try:
                df = pd.read_csv(save_path)
                df = pd.concat([df, pd.DataFrame(results)], ignore_index=True)
            except Exception:
                df = pd.DataFrame(results)
            df.to_csv(save_path, index=False)
            st.success("All batch results saved successfully!")

# =============================
# Teacher Dashboard (View)
# =============================
if page == "📊 View Dashboard" and st.session_state.role == "Teacher":
    st.subheader("📊 Your Graded Results")
    if os.path.exists("results"):
        all_results = []
        for dept in os.listdir("results"):
            dept_path = f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path = f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        df = pd.read_csv(sub_path)
                        all_results.append(df)
        if all_results:
            df_all = pd.concat(all_results, ignore_index=True)
            st.write(df_all.style.applymap(lambda v: color_rows(v) if isinstance(v, (int, float)) else "", subset=["Score"]))
        else:
            st.markdown("<p class='notification'>No results found.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='notification'>No results folder found.</p>", unsafe_allow_html=True)

# =============================
# Analytics
# =============================
if page == "📈 Analytics":
    st.subheader("📈 Score Analytics")
    if os.path.exists("results"):
        all_results = []
        for dept in os.listdir("results"):
            dept_path = f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path = f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        df = pd.read_csv(sub_path)
                        df["Department"] = dept
                        df["Subject"] = sub
                        all_results.append(df)
        if all_results:
            df_all = pd.concat(all_results, ignore_index=True)
            avg_dept = df_all.groupby("Department")["Score"].mean().reset_index()
            fig1 = px.bar(avg_dept, x="Department", y="Score", title="Average Score by Department", text="Score")
            st.plotly_chart(fig1, use_container_width=True)
            avg_sub = df_all.groupby("Subject")["Score"].mean().reset_index()
            fig2 = px.bar(avg_sub, x="Subject", y="Score", title="Average Score by Subject", text="Score")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("<p class='notification'>No results found for analytics.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='notification'>No results folder found for analytics.</p>", unsafe_allow_html=True)

