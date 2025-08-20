# ---------- app.py (Fully Professional KHT AI Auto-Grader - Fixed for Image Recognition) ----------
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import os
import hashlib
from auto_grader import grade_with_answer_key, parse_mcq_answers, grade_mcq
import plotly.express as px

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- CSS Styling ----------
st.markdown("""
<style>
.stApp { background-color:#ffffff; color: #000000 !important; }
section[data-testid="stSidebar"] { background-color: #4a0072; padding-top: 2rem; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
.login-card { background-color:#ffffff; color:#000000 !important; padding: 1.5rem; border-radius: 10px;
box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out; }
@keyframes slideBounce { 0% { transform: translateX(-150%); opacity: 0; }
70% { transform: translateX(10px); opacity: 1; } 100% { transform: translateX(0); opacity: 1; } }
.notification { color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
animation: fadeIn 0.6s ease-in-out; }
@keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }
h1,h2,h3,h4,h5,h6 { color: #000000 !important; font-weight:bold; }
div.stButton > button { background-color:#6a1b9a; color:black !important; font-weight:bold; border:none; border-radius:5px; padding:0.4em 1em; }
div.stButton > button:hover { background-color:#4a0072; color:black !important; }
input,textarea,select { border:1px solid #6a1b9a !important; color:#000000 !important; font-weight:bold; }
label,.stFileUploader label { color:#000000 !important; font-weight:bold; }
table { border:2px solid #6a1b9a !important; border-collapse:collapse !important; color:#000000 !important; }
thead tr th { background-color:#6a1b9a !important; color:black !important; font-weight:bold !important; }
tbody tr:nth-child(odd) { background-color:#f3e5f5 !important; }
tbody tr:nth-child(even) { background-color:#ffffff !important; }
tbody tr td { color:#000000 !important; font-weight:500 !important; border:1px solid #ddd !important; }
.ocr-box { background-color:#f7f7f7; color:#000000 !important; border:1px solid #ccc; padding:10px; border-radius:5px; max-height:300px; overflow:auto; font-size:14px; }
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

def load_teachers(): 
    return load_json("teachers.json")

def save_teachers(data): 
    save_json("teachers.json", data)

def load_pending_teachers(): 
    return load_json("pending_teachers.json")

def save_pending_teachers(data): 
    save_json("pending_teachers.json", data)

def load_answer_key():
    try: 
        return json.load(open("answer_key.json","r")).get("key","")
    except: 
        return ""

def save_answer_key(text): 
    json.dump({"key":text}, open("answer_key.json","w"))

def extract_text_from_image(image):
    try: 
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.warning(f"OCR Error: {e}")
        return ""

# ---------- Unified Student File Reader ----------
def read_student_file(file):
    """
    Reads a student file (text or image) and returns the extracted string.
    Works for txt, jpg, jpeg, png.
    """
    try:
        if file.type.startswith("text"):
            return file.read().decode("utf-8").strip()
        else:
            img = Image.open(file)
            img = img.convert("RGB")
            return extract_text_from_image(img)
    except Exception as e:
        st.warning(f"Error reading student file '{file.name}': {e}")
        return ""

def color_rows(val):
    if val>=85: color='#d4edda'
    elif val>=60: color='#fff3cd'
    else: color='#f8d7da'
    return f'background-color:{color}'

def load_results(department, subject):
    path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()

# ---------- Session State ----------
if "authenticated" not in st.session_state: st.session_state.authenticated=False
if "role" not in st.session_state: st.session_state.role=None
if "remove_teacher" not in st.session_state: st.session_state.remove_teacher=None
if "approve_teacher" not in st.session_state: st.session_state.approve_teacher=None

# ---------- Sidebar Header ----------
st.sidebar.markdown("<h1 style='color:#ffffff; text-align:center;'>KHT AI AUTO GRADER</h1>", unsafe_allow_html=True)

# ---------- Login ----------
login_type = st.sidebar.radio("Login as:", ["Admin","Teacher"])
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH=hash_password("admin123")

if not st.session_state.authenticated:
    if login_type=="Admin":
        st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.sidebar.subheader("🔐 Admin Login")
        admin_user=st.sidebar.text_input("Username")
        admin_pass=st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login as Admin"):
            if admin_user==ADMIN_USERNAME and hash_password(admin_pass)==ADMIN_PASSWORD_HASH:
                st.session_state.authenticated=True
                st.session_state.role="Admin"
                st.rerun()
            else:
                st.sidebar.warning("❌ Incorrect admin credentials.")
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

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
                st.rerun()
            else:
                st.sidebar.warning("❌ Incorrect username or password.")
        if register_btn:
            if teacher_user in teachers or teacher_user in pending_teachers:
                st.sidebar.warning("❌ Username already exists.")
            elif teacher_user and teacher_pass:
                pending_teachers[teacher_user]=hash_password(teacher_pass)
                save_pending_teachers(pending_teachers)
                st.sidebar.success("✅ Registration submitted for admin approval!")
            else:
                st.sidebar.info("⚠️ Enter username and password to register.")
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
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
else:
    page = st.sidebar.selectbox("📂 Select Page", [
        "📥 Upload Answer Key",
        "📤 Upload & Grade Student Exam",
        "🔍 Search Results (ID or Name)",
        "📊 View Dashboard",
        "📈 Analytics",
        "🖊️ Teacher Help Grading"
    ])

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
        teachers.pop(st.session_state.remove_teacher, None)
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
    if teacher_to_approve:
        teachers[teacher_to_approve] = pending_teachers.pop(teacher_to_approve)
        save_teachers(teachers)
        save_pending_teachers(pending_teachers)
        st.session_state.approve_teacher=None
        st.rerun()

# ---------- Shared Upload & Grade ----------
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"]:
    st.subheader("Upload & Grade Student Exam")
    mode = st.radio("Select Exam Section", ["Multiple Choice", "Essay"])
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    batch_mode = st.checkbox("Enable Batch Grading (Upload multiple files)")
    
    key_file_label = "Upload Teacher's MCQ Key" if mode=="Multiple Choice" else "Upload Teacher's Essay Key"
    student_file_label = "Upload Student MCQ Answers (scan or text)" if mode=="Multiple Choice" else "Upload Student Essay (scan or text)"
    
    # ---------- Upload Answer Key ----------
    st.markdown("### Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader(key_file_label, type=["txt","jpg","jpeg","png"])
    if key_file:
        teacher_key = key_file.read().decode("utf-8").strip() if key_file.type.startswith("text") else extract_text_from_image(Image.open(key_file))
        save_answer_key(teacher_key)
        st.markdown(f"<div class='ocr-box'><pre>{teacher_key}</pre></div>", unsafe_allow_html=True)
        st.success("✅ Answer Key saved successfully!")

    # ---------- Load model answer ----------
    model_answer = load_answer_key()
    if not model_answer:
        st.warning("⚠️ Please upload the answer key first.")
        st.stop()
    
    # ---------- Single Student ----------
    if not batch_mode:
        student_name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        student_file = st.file_uploader(student_file_label, type=["txt","jpg","jpeg","png"])
        if student_file and st.button("Grade Student"):
            student_answer = read_student_file(student_file)
            if mode=="Multiple Choice":
                student_answers = parse_mcq_answers(student_answer)
                score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
            
            st.markdown(f"<p class='notification'>Score: {score}</p>", unsafe_allow_html=True)
            st.markdown("<p class='notification'>Detailed Feedback:</p>", unsafe_allow_html=True)
            for line in feedback.split("\n"):
                cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)
            
            result = {
                "Student ID": student_id,
                "Name": student_name,
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
            except:
                df = pd.DataFrame([result])
            df.to_csv(save_path, index=False)
            st.success("✅ Result saved successfully!")

    # ---------- Batch Grading ----------
    else:
        batch_files = st.file_uploader(f"Upload Multiple {mode} Files", type=["txt","jpg","jpeg","png"], accept_multiple_files=True)
        if batch_files and st.button("Grade All Exams"):
            results=[]
            for file in batch_files:
                student_answer = read_student_file(file)
                student_name, student_id = "Unknown","0000"
                try:
                    for line in student_answer.splitlines():
                        line_clean=line.strip()
                        if line_clean.lower().startswith("name:"): student_name=line_clean.split(":",1)[1].strip()
                        if line_clean.lower().startswith("id:"): student_id=line_clean.split(":",1)[1].strip()
                    parts=os.path.splitext(file.name)[0].split("_")
                    if (student_name=="Unknown" or student_id=="0000") and len(parts)>=2:
                        student_name, student_id=parts[0], parts[1]
                except: pass
                if mode=="Multiple Choice":
                    student_answers=parse_mcq_answers(student_answer)
                    score,feedback=grade_mcq(model_answer.splitlines(), student_answers)
                else:
                    score,feedback=grade_with_answer_key(model_answer, student_answer)
                results.append({
                    "Student ID": student_id,
                    "Name": student_name,
                    "Department": department,
                    "Subject": subject,
                    "Answer": student_answer,
                    "Score": score,
                    "Feedback": feedback,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.markdown(f"<p class='notification'>Graded {student_name} ({student_id}) → Score: {score}</p>", unsafe_allow_html=True)
            
            save_path=f"results/{department}/{subject}/results.csv"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            try:
                df=pd.read_csv(save_path)
                df=pd.concat([df,pd.DataFrame(results)], ignore_index=True)
            except:
                df=pd.DataFrame(results)
            df.to_csv(save_path,index=False)
            st.success("✅ All batch results saved successfully!")

# ---------- Search Results ----------
if page=="🔍 Search Results (ID or Name)":
    st.subheader("🔎 Search Student Results")
    search_dept = st.text_input("Department to Search", value="General").strip().replace("/", "-")
    search_subj = st.text_input("Subject to Search", value="Misc").strip().replace("/", "-")
    search_query = st.text_input("Enter Student ID or Name").strip().lower()
    if st.button("Search"):
        df=load_results(search_dept, search_subj)
        if df.empty:
            st.info("No results found for this department/subject.")
        else:
            filtered=df[df["Student ID"].str.lower().str.contains(search_query) | df["Name"].str.lower().str.contains(search_query)]
            if filtered.empty: st.warning("No matching student found.")
            else: st.dataframe(filtered.style.applymap(lambda x: 'background-color: #d4edda' if isinstance(x,int) and x>=85 else '', subset=["Score"]))

# ---------- Analytics ----------
if page=="📈 Analytics":
    st.subheader("📊 Analytics & Performance Charts")
    dept = st.text_input("Department", value="General").strip().replace("/", "-")
    subj = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    df=load_results(dept,subj)
    if df.empty: st.info("No results available for this department/subject.")
    else:
        st.markdown("### Score Distribution")
        fig=px.histogram(df,x="Score",nbins=10,color_discrete_sequence=['#6a1b9a'])
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("### Top Performers")
        top_df=df.sort_values(by="Score",ascending=False).head(5)
        st.table(top_df[["Student ID","Name","Score"]])

# ---------- Teacher Help Grading ----------
if page=="🖊️ Teacher Help Grading" and st.session_state.role=="Teacher":
    st.subheader("📝 Teacher Help Grading (Optional AI Assistance)")
    essay_file=st.file_uploader("Upload Student Essay (Text/Image)", type=["txt","jpg","jpeg","png"])
    if essay_file and st.button("Grade Essay"):
        essay_text = read_student_file(essay_file)
        teacher_key=load_answer_key()
        if not teacher_key: st.warning("Upload answer key first."); st.stop()
        score,feedback=grade_with_answer_key(teacher_key,essay_text)
        st.markdown(f"<p class='notification'>Score: {score}</p>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Detailed Feedback:</p>", unsafe_allow_html=True)
        for line in feedback.split("\n"):
            cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
            st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)
