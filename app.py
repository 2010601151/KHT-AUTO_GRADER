# ---------- app.py (Full KHT AI Auto-Grader with Batch Grading) ----------
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import os
import hashlib
from auto_grader import grade_with_answer_key
import plotly.express as px

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- CSS Styling ----------
# ---------- CSS Styling ----------
st.markdown("""
<style>
/* Main app background & text */
.stApp { background-color:#4a0072; color: #000000 !important; }

/* Sidebar background & text */
section[data-testid="stSidebar"] { background-color: #ffffff; padding-top: 2rem; }
section[data-testid="stSidebar"] * { color: #000000 !important; }

/* Login card */
.login-card { background-color: #4a0072; color: #ffffff !important; padding: 1.5rem; border-radius: 10px;
box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out; }

/* Animations */
@keyframes slideBounce { 0% { transform: translateX(-150%); opacity: 0; }
70% { transform: translateX(10px); opacity: 1; } 100% { transform: translateX(0); opacity: 1; } }

.notification { color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
animation: fadeIn 0.6s ease-in-out; }

@keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }

/* Headings */
h1,h2,h3,h4,h5,h6 { color: #000000 !important; font-weight:bold; }

/* Buttons */
div.stButton > button { background-color:#6a1b9a; color:black !important; font-weight:bold; border:none; border-radius:5px; padding:0.4em 1em; }
div.stButton > button:hover { background-color:#4a0072; color:black !important; }

/* Inputs, selects, textareas, labels */
input,textarea,select { border:1px solid #6a1b9a !important; color:#000000 !important; font-weight:bold; }
label,.stFileUploader label { color:#000000 !important; font-weight:bold; }

/* Tables */
table { border:2px solid #6a1b9a !important; border-collapse:collapse !important; color:#000000 !important; }
thead tr th { background-color:#6a1b9a !important; color:black !important; font-weight:bold !important; }
tbody tr:nth-child(odd) { background-color:#f3e5f5 !important; }
tbody tr:nth-child(even) { background-color:#ffffff !important; }
tbody tr td { color:#000000 !important; font-weight:500 !important; border:1px solid #ddd !important; }

/* OCR box */
.ocr-box { background-color:#f7f7f7; color:#000000 !important; border:1px solid #ccc; padding:10px; border-radius:5px; max-height:300px; overflow:auto; font-size:14px; }

/* Feedback badges */
.feedback-correct { background-color:#28a745; color:black !important; font-weight:bold; padding:2px 4px; border-radius:3px; }
.feedback-partial { background-color:#ffc107; color:black !important; font-weight:bold; padding:2px 4px; border-radius:3px; }
.feedback-wrong { background-color:#dc3545; color:black !important; font-weight:bold; padding:2px 4px; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ---------- App Title ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def load_teachers(): return json.load(open("teachers.json","r")) if os.path.exists("teachers.json") else {}
def save_teachers(data): json.dump(data, open("teachers.json","w"))
def load_pending_teachers(): return json.load(open("pending_teachers.json","r")) if os.path.exists("pending_teachers.json") else {}
def save_pending_teachers(data): json.dump(data, open("pending_teachers.json","w"))
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
if "authenticated" not in st.session_state: st.session_state.authenticated=False
if "role" not in st.session_state: st.session_state.role=None
if "remove_teacher" not in st.session_state: st.session_state.remove_teacher=None
if "approve_teacher" not in st.session_state: st.session_state.approve_teacher=None

# ---------- Sidebar Header ----------
st.sidebar.markdown(
    "<h1 style='color:#ffffff; text-align:center;'>KHT AI AUTO GRADER</h1>",
    unsafe_allow_html=True
)

# ---------- Login ----------
login_type = st.sidebar.radio("Login as:", ["Admin","Teacher"])

# ---------- Admin Login ----------
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH=hash_password("admin123")
if login_type=="Admin":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Admin Login")
    admin_user=st.sidebar.text_input("Username")
    admin_pass=st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if admin_user==ADMIN_USERNAME and hash_password(admin_pass)==ADMIN_PASSWORD_HASH:
            st.session_state.authenticated=True
            st.session_state.role="Admin"
            st.sidebar.markdown("<p class='notification'>✅ Admin login successful!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Teacher Login/Register ----------
if login_type=="Teacher":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
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
            st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
    if register_btn:
        if teacher_user in teachers or teacher_user in pending_teachers:
            st.sidebar.markdown("<p class='notification'>❌ Username already exists.</p>", unsafe_allow_html=True)
        elif teacher_user and teacher_pass:
            pending_teachers[teacher_user]=teacher_pass
            save_pending_teachers(pending_teachers)
            st.sidebar.markdown("<p class='notification'>✅ Registration submitted for admin approval!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>⚠️ Enter username and password to register.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated=False
    st.session_state.role=None
    st.experimental_rerun()

# ---------- Pages ----------
if st.session_state.role=="Admin":
    page = st.sidebar.selectbox("📂 Select Page", [
        "📊 Admin Dashboard",
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📈 Analytics"
    ])
else:
    page = st.sidebar.selectbox("📂 Select Page", [
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📊 View Dashboard",
        "📈 Analytics"
    ])

# ---------- Admin Dashboard ----------
if page=="📊 Admin Dashboard":
    st.subheader("👤 Manage Teachers & Approvals")
    teachers = load_teachers()
    pending_teachers = load_pending_teachers()

    # Approved Teachers
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
        st.experimental_rerun()

    # Pending Teachers
    st.markdown("### ⏳ Pending Teacher Registrations")
    for username, pwd in pending_teachers.items():
        col1,col2,col3=st.columns([2,2,1])
        col1.write(f"Username: {username}")
        col2.write(f"Password Hash: {hash_password(pwd)}")
        if col3.button("Approve", key=f"approve_{username}"):
            st.session_state.approve_teacher=username

    # Safe Approve Logic
    teacher_to_approve = st.session_state.get("approve_teacher", None)
    if teacher_to_approve and teacher_to_approve in pending_teachers:
        teachers[teacher_to_approve] = hash_password(pending_teachers[teacher_to_approve])
        save_teachers(teachers)
        pending_teachers.pop(teacher_to_approve)
        save_pending_teachers(pending_teachers)
        st.session_state.approve_teacher = None
        st.experimental_rerun()

    # Display Teacher Results
    st.markdown("### 📊 Teacher Results")
    if os.path.exists("results"):
        for dept in os.listdir("results"):
            dept_path=f"results/{dept}"
            if os.path.isdir(dept_path):
                for sub in os.listdir(dept_path):
                    sub_path=f"{dept_path}/{sub}/results.csv"
                    if os.path.exists(sub_path):
                        st.markdown(f"#### Department/Subject: {dept} / {sub}")
                        df=pd.read_csv(sub_path)
                        st.dataframe(df.style.applymap(color_rows, subset=["Score"]))

# ---------- Upload Answer Key ----------
if page=="📥 Upload Answer Key":
    st.subheader("Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader("Upload Answer Key", type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"): key_text = key_file.read().decode("utf-8")
        else: key_text = extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

# ---------- Upload & Grade Student Exam (Single or Batch) ----------
if page=="📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exams for Grading (Single or Multiple)")
    model_answer = load_answer_key()
    if not model_answer: st.markdown("<p class='notification'>⚠️ Please upload the answer key first.</p>", unsafe_allow_html=True)

    batch_mode = st.checkbox("Enable Batch Grading (Upload multiple files)")
    department = st.text_input("Department", value="General").strip().replace("/","-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/","-")

    if not batch_mode:
        student_name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg","png","jpeg"])
        if exam_file:
            image = Image.open(exam_file)
            student_answer = extract_text_from_image(image)
            st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)
            if st.button("Grade Answer"):
                if not all([student_name,student_id,department,subject]):
                    st.markdown("<p class='notification'>⚠️ Fill all student details before grading.</p>", unsafe_allow_html=True)
                else:
                    score, feedback = grade_with_answer_key(model_answer, student_answer)
                    st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                    st.markdown("<p class='notification'>Detailed Feedback below:</p>", unsafe_allow_html=True)
                    for line in feedback.split("\n"):
                        cls="feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                        st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)
                    result={"Student ID":student_id,"Name":student_name,"Department":department,
                            "Subject":subject,"Answer":student_answer,"Score":score,
                            "Feedback":feedback,"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    save_path=f"results/{department}/{subject}/results.csv"
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    try: df=pd.read_csv(save_path); df=pd.concat([df,pd.DataFrame([result])], ignore_index=True)
                    except: df=pd.DataFrame([result])
                    df.to_csv(save_path,index=False)
                    st.markdown("<p class='notification'>Result saved to dashboard!</p>", unsafe_allow_html=True)

    else:  # Batch Mode
        batch_files = st.file_uploader("Upload Multiple Exams (Images)", type=["jpg","png","jpeg"], accept_multiple_files=True)
        if batch_files and st.button("Grade All Exams"):
            results=[]
            for file in batch_files:
                image = Image.open(file)
                student_answer = extract_text_from_image(image)
                student_name, student_id = os.path.splitext(file.name)[0].split("_")[:2]  # filename format: ID_Name.jpg
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                results.append({"Student ID":student_id,"Name":student_name,"Department":department,
                                "Subject":subject,"Answer":student_answer,"Score":score,
                                "Feedback":feedback,"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.markdown(f"<p class='notification'>Graded {student_name} ({student_id}) → Score: {score}%</p>", unsafe_allow_html=True)
            save_path=f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            try: df=pd.read_csv(save_path); df=pd.concat([df,pd.DataFrame(results)], ignore_index=True)
            except: df=pd.DataFrame(results)
            df.to_csv(save_path,index=False)
            st.markdown("<p class='notification'>All batch results saved successfully!</p>", unsafe_allow_html=True)



