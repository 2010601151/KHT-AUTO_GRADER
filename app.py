# ---------- app.py (KHT AI Auto-Grader Full App with Admin + Teacher) ----------
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
st.markdown("""
<style>
.stApp { background-color: #ffffff; color:#800080; }
section[data-testid="stSidebar"] { background-color: #6a1b9a; padding-top: 2rem; }
section[data-testid="stSidebar"] * { color: white !important; }
.login-card { background-color: #000000; color: #ffffff; padding: 1.5rem; border-radius: 10px;
box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out; }
@keyframes slideBounce { 0% { transform: translateX(-150%); opacity: 0; }
70% { transform: translateX(10px); opacity: 1; } 100% { transform: translateX(0); opacity: 1; } }
.notification { color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
animation: fadeIn 0.6s ease-in-out; }
@keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }
h1,h2,h3,h4 { color:#000000; font-weight:bold; }
div.stButton > button { background-color:#6a1b9a; color:white; font-weight:bold; border:none; border-radius:5px; padding:0.4em 1em; }
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
    """
    <h1 style='color:#ffffff; text-align:center;'>
        KHT AI AUTO GRADER
    </h1>
    """,
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

# ---------- Admin Panel ----------
if st.session_state.role=="Admin":
    st.subheader("📋 Admin Dashboard")

    # Approve Pending Teachers
    st.markdown("### 👥 Pending Teacher Approvals")
    pending_teachers=load_pending_teachers()
    teachers=load_teachers()
    if pending_teachers:
        for user,pw in pending_teachers.items():
            col1,col2=st.columns([3,1])
            col1.write(user)
            if col2.button(f"Approve {user}"):
                teachers[user]=hash_password(pw)
                save_teachers(teachers)
                del pending_teachers[user]
                save_pending_teachers(pending_teachers)
                st.success(f"✅ Teacher {user} approved.")
                st.rerun()
    else:
        st.info("No pending teachers.")

    # Remove Teachers
    st.markdown("### ❌ Remove Teachers")
    if teachers:
        user_to_remove=st.selectbox("Select teacher to remove", list(teachers.keys()))
        if st.button("Remove Teacher"):
            del teachers[user_to_remove]
            save_teachers(teachers)
            st.success(f"✅ Teacher {user_to_remove} removed.")
            st.rerun()
    else:
        st.info("No teachers registered.")

    # Upload / Edit Answer Key
    st.markdown("### 📝 Answer Key Management")
    answer_key=load_answer_key()
    new_answer_key=st.text_area("Enter or update answer key:", answer_key)
    if st.button("Save Answer Key"):
        save_answer_key(new_answer_key)
        st.success("✅ Answer key updated successfully!")

# ---------- Teacher Panel ----------
if st.session_state.role=="Teacher":
    st.subheader("📚 Teacher Dashboard")

    # Upload Student Papers
    st.markdown("### 📤 Upload Student Papers for Auto-Grading")
    uploaded_files=st.file_uploader("Upload scanned student papers", type=["jpg","jpeg","png"], accept_multiple_files=True)
    if uploaded_files:
        results=[]
        answer_key=load_answer_key()
        if not answer_key:
            st.error("❌ No answer key found. Please contact Admin to upload one.")
        else:
            for file in uploaded_files:
                image=Image.open(file)
                extracted_text=extract_text_from_image(image)
                st.markdown(f"#### 📄 Extracted Text from {file.name}")
                st.markdown(f"<div class='ocr-box'>{extracted_text}</div>", unsafe_allow_html=True)

                # Grade Paper
                graded=grade_with_answer_key(extracted_text, answer_key)
                graded["Student"]=file.name
                results.append(graded)

            if results:
                df=pd.DataFrame(results)
                styled_df=df.style.applymap(color_rows, subset=["Score"])
                st.markdown("### 📊 Grading Results")
                st.dataframe(styled_df, use_container_width=True)

                # Export Results
                if st.button("📥 Download Results as CSV"):
                    timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename=f"grading_results_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    st.success(f"✅ Results saved as {filename}")

                # Visualize
                fig=px.bar(df, x="Student", y="Score", color="Score", title="Student Scores", text="Score")
                st.plotly_chart(fig, use_container_width=True)
