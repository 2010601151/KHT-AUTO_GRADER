# ---------- app.py (Full KHT AI Auto-Grader with Batch Grading & Role Permissions) ----------
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
input,textarea,select { border:1px solid #6a1b9a !important; color:#ffffff !important; font-weight:bold; }
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
/* Make radio buttons bold and black */
div[role="radiogroup"] label { color: black !important; font-weight: bold !important; }
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
                st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
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
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated=False
    st.session_state.role=None
    st.rerun()

# ---------- Page Selection Based on Role ----------
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

# ---------- Teacher/Admin Shared Page: Upload & Grade ----------
if page in ["📥 Upload Answer Key", "📤 Upload & Grade Student Exam"]:
    st.subheader("Upload & Grade Student Exam")

    # ---------- Select Section ----------
    st.markdown("<b style='color:black;'>Select Exam Section</b>", unsafe_allow_html=True)
    mode = st.radio(
        label="",
        options=["Multiple Choice", "Essay"]
    )
