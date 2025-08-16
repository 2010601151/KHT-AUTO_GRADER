# ---------- app.py (Professional Full KHT AI Auto-Grader with Admin Teacher Management) ----------
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import os
import hashlib
from auto_grader import grade_with_answer_key

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- Theme & Styles ----------
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color:#000000; }
    section[data-testid="stSidebar"] { background-color: #6a1b9a; padding-top: 2rem; transition: transform 0.5s ease, opacity 0.5s ease;}
    section[data-testid="stSidebar"].collapsed { transform: translateX(-100%); opacity: 0;}
    section[data-testid="stSidebar"] * { color: white !important; }
    .login-card { background-color: #ffffff; color: #000000; padding: 1.5rem; border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
        transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out;}
    @keyframes slideBounce { 0% {transform:translateX(-150%);opacity:0;} 70% {transform:translateX(10px);opacity:1;} 100% {transform:translateX(0);opacity:1;} }
    .notification { color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px; animation: fadeIn 0.6s ease-in-out;}
    @keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }
    h1,h2,h3,h4 { color: #000000; font-weight: bold; }
    div.stButton > button { background-color: #6a1b9a; color:white; font-weight:bold; border:none; border-radius:5px; padding:0.4em 1em; }
    div.stButton > button:hover { background-color:#4a0072; color:white; }
    input,textarea,select { border:1px solid #6a1b9a !important; color:#ffffff !important; font-weight:bold; }
    label,.stFileUploader label { color:#6a1b9a !important; font-weight:bold; }
    table { border:2px solid #6a1b9a !important; border-collapse:collapse !important; }
    thead tr th { background-color:#6a1b9a !important; color:white !important; font-weight:bold !important; }
    tbody tr:nth-child(odd) { background-color:#f3e5f5 !important; }
    tbody tr:nth-child(even) { background-color:#ffffff !important; }
    tbody tr td { color:#000000 !important; font-weight:500 !important; border:1px solid #ddd !important; }
    .ocr-box { background-color:#f7f7f7; color:#000000; border:1px solid #ccc; padding:10px; border-radius:5px; max-height:300px; overflow:auto; font-size:14px; }
    .feedback-correct { background-color:#28a745; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-partial { background-color:#ffc107; color:black; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-wrong { background-color:#dc3545; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }
    /* Sidebar animations for mobile */
    .stSidebar .block-container { animation: fadeSlide 0.6s ease forwards;}
    @keyframes fadeSlide {0% {opacity:0; transform: translateX(-20px);} 100% {opacity:1; transform: translateX(0);} }
    .stSidebar button, .stSidebar select { font-size:16px !important; padding:0.6rem 1rem !important; border-radius:6px;}
</style>
""", unsafe_allow_html=True)

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def load_teachers(): return json.load(open("teachers.json")) if os.path.exists("teachers.json") else {}
def save_teachers(data): json.dump(data, open("teachers.json","w"))
def load_answer_key(): 
    try: return json.load(open("answer_key.json")).get("key","")
    except: return ""
def save_answer_key(text): json.dump({"key": text}, open("answer_key.json","w"))
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

# ---------- Authentication ----------
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "role" not in st.session_state: st.session_state.role = None

login_type = st.sidebar.radio("Login as:", ["Admin","Teacher"])

# ---------- Admin Login ----------
ADMIN_USERNAME, ADMIN_PASSWORD_HASH = "admin", hash_password("admin123")
if login_type=="Admin":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Admin Login")
    admin_user = st.sidebar.text_input("Username")
    admin_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if admin_user==ADMIN_USERNAME and hash_password(admin_pass)==ADMIN_PASSWORD_HASH:
            st.session_state.authenticated=True
            st.session_state.role="Admin"
            st.sidebar.markdown("<p class='notification'>✅ Admin login successful!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Teacher Login/Register ----------
if login_type=="Teacher":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher Login / Register")
    teachers = load_teachers()
    teacher_user = st.sidebar.text_input("Username")
    teacher_pass = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login as Teacher")
    register_btn = st.sidebar.button("Register Teacher")
    if login_btn:
        if teacher_user in teachers and teachers[teacher_user]==hash_password(teacher_pass):
            st.session_state.authenticated=True
            st.session_state.role="Teacher"
            st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
    if register_btn:
        if teacher_user in teachers: st.sidebar.markdown("<p class='notification'>❌ Username already exists.</p>", unsafe_allow_html=True)
        elif teacher_user and teacher_pass:
            teachers[teacher_user]=hash_password(teacher_pass)
            save_teachers(teachers)
            st.sidebar.markdown("<p class='notification'>✅ Teacher registered successfully!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>⚠️ Enter username and password to register.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated=False
    st.session_state.role=None
    st.rerun()

# ---------- Mobile Sidebar Toggle ----------
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = True
if st.sidebar.button("☰ Toggle Menu"): st.session_state.sidebar_visible = not st.session_state.sidebar_visible
st.markdown(f"""
<script>
let sidebar = document.querySelector('section[data-testid="stSidebar"]');
if({str(st.session_state.sidebar_visible).lower()}) {{ sidebar.classList.remove('collapsed'); }}
else {{ sidebar.classList.add('collapsed'); }}
</script>
""", unsafe_allow_html=True)

# ---------- Admin: Teacher Account Management ----------
if st.session_state.role=="Admin":
    st.subheader("🛠 Teacher Account Management")
    teachers = load_teachers()

    # Show all registered teachers
    st.markdown("### Current Teachers")
    if teachers:
        teacher_table = pd.DataFrame([{"Username": u, "Password Hash": teachers[u]} for u in teachers])
        st.dataframe(teacher_table)
    else:
        st.markdown("<p class='notification'>No teachers registered yet.</p>", unsafe_allow_html=True)

    # Add new teacher
    st.markdown("### Add New Teacher")
    new_teacher_user = st.text_input("New Teacher Username", key="admin_new_user")
    new_teacher_pass = st.text_input("New Teacher Password", type="password", key="admin_new_pass")
    if st.button("Add Teacher"):
        if new_teacher_user in teachers:
            st.markdown("<p class='notification'>❌ Username already exists.</p>", unsafe_allow_html=True)
        elif new_teacher_user and new_teacher_pass:
            teachers[new_teacher_user] = hash_password(new_teacher_pass)
            save_teachers(teachers)
            st.markdown(f"<p class='notification'>✅ Teacher '{new_teacher_user}' added successfully!</p>", unsafe_allow_html=True)
            st.experimental_rerun()
        else:
            st.markdown("<p class='notification'>⚠️ Enter both username and password.</p>", unsafe_allow_html=True)

    # Delete teacher
    st.markdown("### Delete Teacher")
    if teachers:
        teacher_to_delete = st.selectbox("Select Teacher to Delete", options=list(teachers.keys()), key="delete_teacher_select")
        if st.button("Delete Selected Teacher"):
            if teacher_to_delete in teachers:
                del teachers[teacher_to_delete]
                save_teachers(teachers)
                st.markdown(f"<p class='notification'>✅ Teacher '{teacher_to_delete}' deleted successfully!</p>", unsafe_allow_html=True)
                st.experimental_rerun()
            else:
                st.markdown("<p class='notification'>❌ Teacher not found.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='notification'>No teachers to delete.</p>", unsafe_allow_html=True)

# ---------- Sidebar Navigation ----------
page = st.sidebar.selectbox("📂 Select Page", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
])

# ---------- Page 1: Upload Answer Key ----------
if page=="📥 Upload Answer Key":
    st.subheader("Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader("Upload Answer Key", type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"): key_text = key_file.read().decode("utf-8")
        else: key_text = extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

# ---------- Page 2: Upload & Grade Student Exam ----------
if page=="📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    model_answer = load_answer_key()
    if not model_answer: st.markdown("<p class='notification'>⚠️ Please upload the teacher's answer key before grading.</p>", unsafe_allow_html=True)
    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg","png","jpeg"])
    if exam_file:
        image = Image.open(exam_file)
        student_answer = extract_text_from_image(image)
        st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)
        if st.button("Grade Answer"):
            if not model_answer: st.markdown("<p class='notification'>⚠️ Cannot grade: Answer key missing.</p>", unsafe_allow_html=True)
            elif not all([student_name, student_id, department, subject]): st.markdown("<p class='notification'>⚠️ Fill all student details before grading.</p>", unsafe_allow_html=True)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                st.markdown("<p class='notification'>Detailed Feedback below:</p>", unsafe_allow_html=True)
                for line in feedback.split("\n"):
                    cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                    st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)
                result = {"Student ID":student_id,"Name":student_name,"Department":department,
                          "Subject":subject,"Answer":student_answer,"Score":score,
                          "Feedback":feedback,"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_path = f"results/{department}/{subject}/results.csv"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                try: df=pd.read_csv(save_path); df=pd.concat([df,pd.DataFrame([result])], ignore_index=True)
                except: df=pd.DataFrame([result])
                df.to_csv(save_path,index=False)
                st.markdown("<p class='notification'>Result saved to dashboard!</p>", unsafe_allow_html=True)

# ---------- Page 3, 4, 5 remain the same ----------
# (Search Results, Dashboard, Analytics)...
