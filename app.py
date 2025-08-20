# ---------- app.py (Complete Full Version with Fast Batch Grading & Analytics) ----------
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import os
import hashlib
from auto_grader import grade_with_answer_key, grade_mcq, parse_mcq_answers as parse_student_answers
import plotly.express as px

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- UI Styles + Dark Mode ----------
st.markdown("""
<style>
/* --- Default Light Theme --- */
.stApp { background:#ffffff; color:#000000; }
section[data-testid="stSidebar"] { background:#f1f3f6; }
section[data-testid="stSidebar"] * { color:#000000; }

h1,h2,h3,h4,h5,h6 { color:#000000; font-weight:700; }

/* Buttons */
div.stButton > button {
  background:#007bff; color:#ffffff!important;
  border-radius:8px; padding:6px 16px;
}
div.stButton > button:hover { background:#0056b3; }

/* Inputs */
input, textarea, select,
div[data-baseweb="input"] input,
div[data-baseweb="input"] textarea,
div[data-baseweb="select"] select {
  background:#ffffff!important; color:#000000!important;
  border:1px solid #ccc!important;
  border-radius:6px;
}
input::placeholder, textarea::placeholder { color:#555!important; }

/* Tables */
table { border:2px solid #007bff!important; color:#000000!important; }
thead th { background:#007bff!important; color:#ffffff!important; }
tbody tr:nth-child(odd) { background:#f9f9f9!important; }
tbody tr:nth-child(even) { background:#e9ecef!important; }
tbody td { color:#000000!important; border:1px solid #ccc!important; }

/* OCR Text Box */
.ocr-box {
  background:#f8f9fa;
  border:1px solid #ddd;
  padding:10px;
  border-radius:6px;
  font-family:monospace;
  color:#000000!important;
}

/* Feedback styles */
.feedback-correct { background:#28a745; color:#fff!important; padding:6px; border-radius:5px; }
.feedback-partial { background:#ffc107; color:#000!important; padding:6px; border-radius:5px; }
.feedback-wrong   { background:#dc3545; color:#fff!important; padding:6px; border-radius:5px; }
</style>
""", unsafe_allow_html=True)

# ---------- Dark Mode Toggle ----------
dark_mode = st.sidebar.checkbox("🌙 Dark Mode")
if dark_mode:
    st.markdown("""
    <style>
    .stApp { background:#121212; color:#f5f5f5!important; }
    section[data-testid="stSidebar"] { background:#1e1e1e; }
    section[data-testid="stSidebar"] * { color:#f5f5f5!important; }
    h1,h2,h3,h4,h5,h6 { color:#f5f5f5!important; }
    div.stButton > button { background:#bb86fc; color:#000!important; }
    div.stButton > button:hover { background:#9a67ea; }
    input, textarea, select,
    div[data-baseweb="input"] input,
    div[data-baseweb="input"] textarea,
    div[data-baseweb="select"] select {
      background:#1e1e1e!important; color:#f5f5f5!important; border:1px solid #bb86fc!important;
    }
    input::placeholder, textarea::placeholder { color:#bbb!important; opacity:1!important; }
    table { border:2px solid #bb86fc!important; color:#f5f5f5!important; }
    thead th { background:#bb86fc!important; color:#000!important; }
    tbody tr:nth-child(odd) { background:#2c2c2c!important; }
    tbody tr:nth-child(even) { background:#1e1e1e!important; }
    tbody td { color:#f5f5f5!important; border:1px solid #444!important; }
    .ocr-box { background:#2c2c2c; border:1px solid #555; color:#f5f5f5!important; }
    .feedback-correct { background:#4caf50; color:#fff!important; }
    .feedback-partial { background:#ff9800; color:#fff!important; }
    .feedback-wrong   { background:#f44336; color:#fff!important; }
    </style>
    """, unsafe_allow_html=True)

# ---------- App Title ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def hash_password(password): 
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path,"r") as f: 
                return json.load(f)
        except: 
            return {}
    return {}

def save_json(path, data):
    with open(path,"w") as f:
        json.dump(data, f)

def load_teachers(): return load_json("teachers.json")
def save_teachers(data): save_json("teachers.json", data)
def load_pending_teachers(): return load_json("pending_teachers.json")
def save_pending_teachers(data): save_json("pending_teachers.json", data)
def load_answer_key():
    try: return json.load(open("answer_key.json","r")).get("key","")
    except: return ""
def save_answer_key(text): json.dump({"key":text}, open("answer_key.json","w"))
def extract_text_from_image(image):
    try: return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""
def color_rows(val):
    if val>=85: color='#d4edda'
    elif val>=60: color='#fff3cd'
    else: color='#f8d7da'
    return f'background-color:{color}'

# ---------- Session State ----------
for key in ["authenticated","role","remove_teacher","approve_teacher"]:
    if key not in st.session_state: st.session_state[key]=None

# ---------- Sidebar Header ----------
st.sidebar.markdown("<h1 style='color:#ffffff; text-align:center;'>KHT AI AUTO GRADER</h1>", unsafe_allow_html=True)

# ---------- Login ----------
login_type = st.sidebar.radio("Login as:", ["Admin","Teacher"])
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH=hash_password("admin123")

if not st.session_state.authenticated:
    if login_type=="Admin":
        st.sidebar.subheader("🔐 Admin Login")
        admin_user=st.sidebar.text_input("Username")
        admin_pass=st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login as Admin"):
            if admin_user==ADMIN_USERNAME and hash_password(admin_pass)==ADMIN_PASSWORD_HASH:
                st.session_state.authenticated=True
                st.session_state.role="Admin"
                st.rerun()
            else:
                st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
        st.stop()
    if login_type=="Teacher":
        st.sidebar.subheader("🔐 Teacher Login / Register")
        teachers = load_teachers()
        pending_teachers = load_pending_teachers()
        teacher_user = st.sidebar.text_input("Username")
        teacher_pass = st.sidebar.text_input("Password", type="password")
        login_btn = st.sidebar.button("Login as Teacher")
        register_btn = st.sidebar.button("Register Teacher")
        if login_btn:
            if teacher_user in teachers and teachers[teacher_user]==hash_password(teacher_pass):
                st.session_state.authenticated=True
                st.session_state.role="Teacher"
                st.rerun()
            else:
                st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
        if register_btn:
            if teacher_user in teachers or teacher_user in pending_teachers:
                st.sidebar.markdown("<p class='notification'>❌ Username already exists.</p>", unsafe_allow_html=True)
            elif teacher_user and teacher_pass:
                pending_teachers[teacher_user]=hash_password(teacher_pass)
                save_pending_teachers(pending_teachers)
                st.sidebar.markdown("<p class='notification'>✅ Registration submitted for admin approval!</p>", unsafe_allow_html=True)
            else:
                st.sidebar.markdown("<p class='notification'>⚠️ Enter username and password to register.</p>", unsafe_allow_html=True)
        st.stop()

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated=False
    st.session_state.role=None
    st.rerun()

# ---------- Page Selection ----------
if st.session_state.role=="Admin":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📊 Admin Dashboard",
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📈 Analytics"
    ])
elif st.session_state.role=="Teacher":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📊 View Dashboard",
        "📈 Analytics"
    ])
else:
    st.stop()

# ---------- Admin Dashboard ----------
if page=="📊 Admin Dashboard" and st.session_state.role=="Admin":
    teachers = load_teachers()
    pending_teachers = load_pending_teachers()
    st.subheader("👤 Manage Teachers & Approvals")
    st.markdown("### ✅ Approved Teachers")
    for username, pwd_hash in teachers.items():
        col1,col2,col3=st.columns([2,2,1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {pwd_hash}")
        if col3.button("Remove", key=f"remove_{username}"):
            st.session_state.remove_teacher=username
    if st.session_state.remove_teacher:
        if st.session_state.remove_teacher in teachers:
            teachers.pop(st.session_state.remove_teacher)
            save_teachers(teachers)
        st.session_state.remove_teacher=None
        st.rerun()
    st.markdown("### ⏳ Pending Teacher Registrations")
    for username, pwd_hash in pending_teachers.items():
        col1,col2,col3=st.columns([2,2,1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {pwd_hash}")
        if col3.button("Approve", key=f"approve_{username}"):
            st.session_state.approve_teacher=username
    teacher_to_approve = st.session_state.get("approve_teacher", None)
    if teacher_to_approve and teacher_to_approve in pending_teachers:
        teachers[teacher_to_approve] = pending_teachers[teacher_to_approve]
        save_teachers(teachers)
        pending_teachers.pop(teacher_to_approve)
        save_pending_teachers(pending_teachers)
        st.session_state.approve_teacher = None
        st.rerun()

# ---------- Shared Page: Upload & Grade ----------
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"]:
    st.subheader("Upload & Grade Student Exam")
    mode = st.radio("Select Exam Section", ["Multiple Choice", "Essay"])
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    batch_mode = st.checkbox("Enable Batch Grading (Upload multiple files)")

    key_file_label = "Upload Teacher's MCQ Key" if mode=="Multiple Choice" else "Upload Teacher's Essay Key"
    student_file_label = "Upload Student MCQ Answers (scan or text)" if mode=="Multiple Choice" else "Upload Student Essay (scan or text)"

    st.markdown("### Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader(key_file_label, type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"): teacher_key = key_file.read().decode("utf-8").strip()
        else: teacher_key = extract_text_from_image(Image.open(key_file))
        save_answer_key(teacher_key)
        st.markdown(f"<div class='ocr-box'><pre>{teacher_key}</pre></div>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

    model_answer = load_answer_key()
    if not model_answer:
        st.markdown("<p class='notification'>⚠️ Please upload the answer key first.</p>", unsafe_allow_html=True)
        st.stop()

# ---------- Single Student Grading ----------
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"] and not batch_mode:
    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    student_file = st.file_uploader(student_file_label, type=["txt","jpg","jpeg","png"])
    if student_file and st.button("Grade Student"):
        if student_file.type.startswith("text"):
            student_answer = student_file.read().decode("utf-8").strip()
        else:
            student_answer = extract_text_from_image(Image.open(student_file))

        if mode=="Multiple Choice":
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
        result = {"Student ID": student_id, "Name": student_name, "Department": department, "Subject": subject,
                  "Answer": student_answer, "Score": score, "Feedback": feedback,
                  "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_path = f"results/{department}/{subject}/results.csv"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try: df = pd.read_csv(save_path); df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
        except: df = pd.DataFrame([result])
        df.to_csv(save_path, index=False)
        st.markdown("<p class='notification'>Result saved successfully!</p>", unsafe_allow_html=True)

# ---------- Batch Grading ----------
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"] and batch_mode:
    batch_files = st.file_uploader(f"Upload Multiple {mode} Files", type=["txt","jpg","jpeg","png"], accept_multiple_files=True)
    if batch_files and st.button("Grade All Exams"):
        student_texts, file_infos = [], []
        for file in batch_files:
            if file.type.startswith("text"): student_answer = file.read().decode("utf-8").strip()
            else: student_answer = extract_text_from_image(Image.open(file))
            student_name, student_id = "Unknown", "0000"
            try:
                for line in student_answer.splitlines():
                    if line.lower().startswith("name:"): student_name = line.split(":",1)[1].strip()
                    if line.lower().startswith("id:"): student_id = line.split(":",1)[1].strip()
                parts = os.path.splitext(file.name)[0].split("_")
                if (student_name=="Unknown" or student_id=="0000") and len(parts)>=2: student_name, student_id = parts[0], parts[1]
            except: pass
            student_texts.append(student_answer)
            file_infos.append({"Name": student_name, "ID": student_id, "Answer": student_answer})

        results=[]
        if mode=="Multiple Choice":
            for info in file_infos:
                student_answers = parse_student_answers(info["Answer"])
                score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
                results.append({**info,"Score":score,"Feedback":feedback})
        else:
            for info in file_infos:
                score, feedback = grade_with_answer_key(model_answer, info["Answer"])
                results.append({**info,"Score":score,"Feedback":feedback})

        save_path = f"results/{department}/{subject}/results.csv"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try: df = pd.read_csv(save_path); df = pd.concat([df, pd.DataFrame(results)], ignore_index=True)
        except: df = pd.DataFrame(results)
        df.to_csv(save_path, index=False)

        for res in results:
            st.markdown(f"<p class='notification'>Graded {res['Name']} ({res['ID']}) → Score: {res['Score']}</p>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>All batch results saved successfully!</p>", unsafe_allow_html=True)

# ---------- Teacher Dashboard ----------
if page=="📊 View Dashboard" and st.session_state.role=="Teacher":
    st.subheader("📊 Your Graded Results")
    if os.path.exists("results"):
        all_results=[]
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path): all_results.append(pd.read_csv(sub_path))
        if all_results: df_all=pd.concat(all_results, ignore_index=True); st.dataframe(df_all.style.applymap(color_rows, subset=["Score"]))
        else: st.markdown("<p class='notification'>No results found.</p>", unsafe_allow_html=True)
    else: st.markdown("<p class='notification'>No results folder found.</p>", unsafe_allow_html=True)

# ---------- Analytics ----------
if page=="📈 Analytics":
    st.subheader("📈 Score Analytics")
    if os.path.exists("results"):
        all_results=[]
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path): all_results.append(pd.read_csv(sub_path))
        if all_results:
            df_all=pd.concat(all_results, ignore_index=True)
            fig=px.histogram(df_all, x="Score", nbins=20, color="Department", title="Score Distribution by Department")
            st.plotly_chart(fig)
        else: st.markdown("<p class='notification'>No results found for analytics.</p>", unsafe_allow_html=True)
    else: st.markdown("<p class='notification'>No results folder found for analytics.</p>", unsafe_allow_html=True)
