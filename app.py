# === app_professional.py ===
# Polished KHT AI Auto-Grader (fully fixed)
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

# Import grading logic from auto_grader.py
from auto_grader import grade_with_answer_key, grade_mcq, parse_student_answers

# =============================
# Configuration & Page Setup
# =============================
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# =============================
# Minimal CSS
# =============================
st.markdown("""<style>
.stApp { background-color:#ffffff; color:#000000 !important; }
section[data-testid="stSidebar"] { background-color: #4a0072; padding-top: 2rem; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
.login-card { background-color:#ffffff; color:#000000 !important; padding:1.25rem; border-radius:10px;
box-shadow:0px 6px 18px rgba(0,0,0,0.12); max-width:320px; margin:1.5rem auto; }
.notification { color:black; font-weight:600; font-size:15px; padding:6px 10px; border-radius:6px; }
.ocr-box { background:#f7f7f7; padding:10px; border-radius:6px; max-height:300px; overflow:auto; font-size:14px; }
.feedback-correct { background-color:#28a745; color:black; font-weight:700; padding:3px 6px; border-radius:4px; }
.feedback-partial { background-color:#ffc107; color:black; font-weight:700; padding:3px 6px; border-radius:4px; }
.feedback-wrong { background-color:#dc3545; color:black; font-weight:700; padding:3px 6px; border-radius:4px; }
div.stButton > button { background-color:#6a1b9a !important; color:#ffffff !important; font-weight:bold;
border:none; border-radius:6px; padding:0.5em 1em; transition: all 0.2s ease-in-out; }
div.stButton > button:hover { background-color:#4a0072 !important; transform: scale(1.02); }
input[type="text"], input[type="password"], textarea { background-color:#ffffff !important; color:#000000 !important;
border:1px solid #ccc !important; border-radius:6px !important; padding:0.5em; font-size:14px; }
input[type="text"]:focus, input[type="password"]:focus, textarea:focus { border-color:#6a1b9a !important;
outline:none !important; box-shadow:0 0 4px rgba(106, 27, 154, 0.5); }
</style>""", unsafe_allow_html=True)

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
    if val >= 85: return 'background-color:#d4edda'
    if val >= 60: return 'background-color:#fff3cd'
    return 'background-color:#f8d7da'

# =============================
# Session State
# =============================
for key in ["authenticated","role","remove_teacher","approve_teacher"]:
    if key not in st.session_state:
        st.session_state[key] = None
st.session_state.authenticated = st.session_state.authenticated or False

# =============================
# Sidebar Login & Navigation
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

# =============================
# Navigation Pages
# =============================
if st.session_state.role == "Admin":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📊 Admin Dashboard","📘 Answer Key & Student Grading","🔍 Search Results (ID or Name)","📈 Analytics"
    ])
elif st.session_state.role == "Teacher":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📘 Answer Key & Student Grading","🔍 Search Results (ID or Name)","📊 View Dashboard","📈 Analytics"
    ])
else: st.stop()
# =============================
# Admin Dashboard
# =============================
if page == "📊 Admin Dashboard" and st.session_state.role == "Admin":
    teachers = load_teachers()
    pending_teachers = load_pending_teachers()
    st.subheader("👤 Manage Teachers & Approvals")
    st.markdown("### ✅ Approved Teachers")
    for username, pwd_hash in teachers.items():
        col1, col2, col3 = st.columns([2,2,1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {pwd_hash}")
        if col3.button("Remove", key=f"remove_{username}"):
            st.session_state.remove_teacher = username
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
        col1, col2, col3 = st.columns([2,2,1])
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
# Answer Key & Student Grading
# =============================
if page == "📘 Answer Key & Student Grading":
    st.subheader("📄 Answer Key & Student Grading")
    mode = st.radio("Select Exam Section", ["Multiple Choice","Essay"])
    department = st.text_input("Department", value="General").strip().replace("/","-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/","-")
    batch_mode = st.checkbox("Enable Batch Grading (Upload multiple files)")

    # Upload Teacher Answer Key
    st.markdown("### 📝 Teacher Answer Key")
    key_file = st.file_uploader("Upload Teacher Answer Key (Text or Image)", type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"):
            teacher_key = key_file.read().decode("utf-8").strip()
        else:
            teacher_key = extract_text_from_image(Image.open(key_file))
        save_answer_key(teacher_key)
        st.markdown(f"<div class='ocr-box'><pre>{teacher_key}</pre></div>", unsafe_allow_html=True)
    else:
        teacher_key = load_answer_key()
        if teacher_key:
            st.markdown(f"<div class='ocr-box'><pre>{teacher_key}</pre></div>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='notification'>⚠️ No answer key uploaded yet.</p>", unsafe_allow_html=True)
            st.stop()

    # Single Student Grading
    if not batch_mode:
        student_name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        student_file = st.file_uploader("Upload Student Exam (Text or Image)", type=["txt","jpg","jpeg","png"])
        if student_file and st.button("Grade Student"):
            if student_file.type.startswith("text"):
                student_answer = student_file.read().decode("utf-8").strip()
            else:
                student_answer = extract_text_from_image(Image.open(student_file))

            # --- Grading Logic ---
            if mode=="Multiple Choice":
                student_answers = parse_student_answers(student_answer)
                score, feedback, wrong_questions = grade_mcq(teacher_key.splitlines(), student_answers, return_wrong=True)
            else:  # Essay
                score, feedback, missing_points = grade_with_answer_key(teacher_key, student_answer)

            # --- Display Results ---
            st.markdown(f"<p class='notification'>Score: {score}</p>", unsafe_allow_html=True)
            st.markdown("<p class='notification'>Detailed Feedback:</p>", unsafe_allow_html=True)
            for line in feedback.split("\n"):
                cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong"
                st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

            if mode=="Multiple Choice" and wrong_questions:
                st.markdown("<p class='notification'>❗ Questions to Improve:</p>", unsafe_allow_html=True)
                for qnum, correct_ans in wrong_questions.items():
                    st.markdown(f"<span class='feedback-wrong'>Q{qnum}: Correct Answer → {correct_ans}</span>", unsafe_allow_html=True)
            elif mode=="Essay" and missing_points:
                st.markdown("<p class='notification'>❗ Points to Improve:</p>", unsafe_allow_html=True)
                for point in missing_points:
                    st.markdown(f"<span class='feedback-wrong'>❌ {point}</span>", unsafe_allow_html=True)

            # --- Save Result ---
            save_path = f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            result = {"Student ID":student_id or "Unknown","Name":student_name or "Unknown","Department":department,
                      "Subject":subject,"Answer":student_answer,"Score":score,"Feedback":feedback,
                      "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            try:
                df = pd.read_csv(save_path)
                df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
            except Exception:
                df = pd.DataFrame([result])
            df.to_csv(save_path, index=False)
            st.success(f"Student {student_name} ({student_id}) graded and saved successfully!")

    # Batch Mode Grading
    else:
        batch_files = st.file_uploader(f"Upload Multiple {mode} Files", type=["txt","jpg","jpeg","png"], accept_multiple_files=True)
        if batch_files and st.button("Grade All Exams"):
            results = []
            for file in batch_files:
                if file.type.startswith("text"): student_answer = file.read().decode("utf-8").strip()
                else: student_answer = extract_text_from_image(Image.open(file))

                student_name, student_id = "Unknown", "0000"
                for line in student_answer.splitlines():
                    lc = line.strip()
                    if lc.lower().startswith("name:"): student_name = lc.split(":",1)[1].strip()
                    elif lc.lower().startswith("id:"): student_id = lc.split(":",1)[1].strip()
                parts = os.path.splitext(file.name)[0].split("_")
                if (student_name=="Unknown" or student_id=="0000") and len(parts)>=2: student_name, student_id = parts[0], parts[1]

                # --- Grading Logic ---
                if mode=="Multiple Choice": student_answers = parse_student_answers(student_answer); score, feedback = grade_mcq(teacher_key.splitlines(), student_answers)
                else: score, feedback, missing_points = grade_with_answer_key(teacher_key, student_answer)

                results.append({"Student ID":student_id or "Unknown","Name":student_name or "Unknown","Department":department,
                                "Subject":subject,"Answer":student_answer,"Score":score,"Feedback":feedback,
                                "Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.markdown(f"<p class='notification'>Graded {student_name} ({student_id}) → Score: {score}</p>", unsafe_allow_html=True)

            save_path = f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            try: df = pd.read_csv(save_path); df = pd.concat([df, pd.DataFrame(results)], ignore_index=True)
            except Exception: df = pd.DataFrame(results)
            df.to_csv(save_path, index=False)
            st.success("All batch results saved successfully!")

# =============================
# Teacher Dashboard
# =============================
if page == "📊 View Dashboard" and st.session_state.role == "Teacher":
    st.subheader("📊 Your Graded Results")
    if os.path.exists("results"):
        all_results=[]
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        df=pd.read_csv(sub_path)
                        all_results.append(df)
        if all_results:
            df_all = pd.concat(all_results, ignore_index=True)
            st.write(df_all.style.applymap(lambda v: color_rows(v) if isinstance(v,(int,float)) else "", subset=["Score"]))
        else: st.markdown("<p class='notification'>No results found.</p>", unsafe_allow_html=True)
    else: st.markdown("<p class='notification'>No results folder found.</p>", unsafe_allow_html=True)

# =============================
# Analytics
# =============================
if page == "📈 Analytics":
    st.subheader("📈 Score Analytics")
    if os.path.exists("results"):
        all_results=[]
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        df=pd.read_csv(sub_path)
                        df["Department"]=dept
                        df["Subject"]=sub
                        all_results.append(df)
        if all_results:
            df_all = pd.concat(all_results, ignore_index=True)
            avg_dept = df_all.groupby("Department")["Score"].mean().reset_index()
            fig1 = px.bar(avg_dept, x="Department", y="Score", title="Average Score by Department", text="Score")
            st.plotly_chart(fig1, use_container_width=True)
            avg_sub = df_all.groupby("Subject")["Score"].mean().reset_index()
            fig2 = px.bar(avg_sub, x="Subject", y="Score", title="Average Score by Subject", text="Score")
            st.plotly_chart(fig2, use_container_width=True)
        else: st.markdown("<p class='notification'>No results available for analytics.</p>", unsafe_allow_html=True)
    else: st.markdown("<p class='notification'>No results folder found for analytics.</p>", unsafe_allow_html=True)

# =============================
# Search Student Results
# =============================
if page == "🔍 Search Results (ID or Name)":
    st.subheader("🔍 Search Student Results")
    student_query = st.text_input("Enter Student Name or ID").strip()
    if student_query and os.path.exists("results"):
        all_results=[]
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        df=pd.read_csv(sub_path)
                        all_results.append(df)
        if all_results:
            df_all = pd.concat(all_results, ignore_index=True)
            df_filtered = df_all[df_all["Name"].str.contains(student_query, case=False, na=False) |
                                 df_all["Student ID"].astype(str).str.contains(student_query)]
            if not df_filtered.empty:
                st.write(df_filtered.style.applymap(lambda v: color_rows(v) if isinstance(v,(int,float)) else "", subset=["Score"]))
            else:
                st.markdown("<p class='notification'>No matching student found.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='notification'>No results found.</p>", unsafe_allow_html=True)
    elif not os.path.exists("results"):
        st.markdown("<p class='notification'>No results folder found.</p>", unsafe_allow_html=True)
