# ---------- app.py (Full KHT AI Auto-Grader with Top Navbar + Latest Features) ----------
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
    .stApp { background-color: #ffffff; color:#000000; }
    section[data-testid="stSidebar"] { background-color: #6a1b9a; padding-top: 2rem; }
    section[data-testid="stSidebar"] * { color: white !important; }
    .login-card { background-color: #ffffff; color: #000000; padding: 1.5rem; border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
        transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out; }
    @keyframes slideBounce { 0% { transform: translateX(-150%); opacity: 0; }
        70% { transform: translateX(10px); opacity: 1; } 100% { transform: translateX(0); opacity: 1; } }
    .notification { color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
        animation: fadeIn 0.6s ease-in-out; }
    @keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }
    h1, h2, h3, h4 { color: #000000; font-weight: bold; }
    div.stButton > button { background-color: #6a1b9a; color: white; font-weight: bold; border: none; border-radius: 5px; padding: 0.4em 1em; }
    div.stButton > button:hover { background-color: #4a0072; color: white; }
    input, textarea, select { border: 1px solid #6a1b9a !important; color:  #000000 !important; font-weight:bold; }
    label, .stFileUploader label { color: #6a1b9a !important; font-weight: bold; }
    table { border: 2px solid #6a1b9a !important; border-collapse: collapse !important; }
    thead tr th { background-color: #6a1b9a !important; color: white !important; font-weight: bold !important; }
    tbody tr:nth-child(odd) { background-color: #f3e5f5 !important; }
    tbody tr:nth-child(even) { background-color: #ffffff !important; }
    tbody tr td { color: #000000 !important; font-weight: 500 !important; border: 1px solid #ddd !important; }
    .ocr-box { background-color: #f7f7f7; color: #000000; border:1px solid #ccc; padding:10px; border-radius:5px; max-height:300px; overflow:auto; font-size:14px; }
    .feedback-correct { background-color:#28a745; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-partial { background-color:#ffc107; color:black; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-wrong { background-color:#dc3545; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }
    /* Top Navbar */
    .topnav { overflow: hidden; background-color: #6a1b9a; padding: 12px; border-radius: 8px; margin-bottom: 20px; }
    .topnav a { float: left; color: white; text-align: center; padding: 10px 16px; text-decoration: none; font-size: 16px; font-weight: 500; }
    .topnav a.active { background-color: #4a0072; color: white; border-radius: 6px; }
    .topnav a:hover { background-color: #9b30ff; color: white; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------- Navbar ----------
pages = ["Home", "Upload Answer Key", "Upload & Grade Student Exam", "Search Results", "Dashboard", "Analytics"]
if "page" not in st.session_state: st.session_state.page = "Home"
st.markdown('<div class="topnav">' + "".join([f'<a href="#"{ " class=active" if p==st.session_state.page else ""}>{p}</a>' for p in pages]) + '</div>', unsafe_allow_html=True)
page = st.selectbox("Select Page", pages, index=pages.index(st.session_state.page))
st.session_state.page = page

# ---------- App Title ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"): st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def load_teachers(): return json.load(open("teachers.json","r")) if os.path.exists("teachers.json") else {}
def save_teachers(data): json.dump(data, open("teachers.json","w"))
def load_answer_key(): 
    try: return json.load(open("answer_key.json","r")).get("key","")
    except: return ""
def save_answer_key(text): json.dump({"key": text}, open("answer_key.json","w"))
def extract_text_from_image(image):
    try: return pytesseract.image_to_string(image)
    except Exception as e: st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True); return ""
def color_rows(val): return 'background-color: #d4edda' if val>=85 else 'background-color: #fff3cd' if val>=60 else 'background-color: #f8d7da'

# ---------- Authentication ----------
if "authenticated" not in st.session_state: st.session_state.authenticated=False; st.session_state.role=None
login_type = st.sidebar.radio("Login as:", ["Admin", "Teacher"])
ADMIN_USERNAME, ADMIN_PASSWORD_HASH = "admin", hashlib.sha256("admin123".encode()).hexdigest()

# ---------- Admin ----------
if login_type=="Admin":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Admin Login")
    user, pwd = st.sidebar.text_input("Username"), st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if user==ADMIN_USERNAME and hashlib.sha256(pwd.encode()).hexdigest()==ADMIN_PASSWORD_HASH:
            st.session_state.authenticated=True; st.session_state.role="Admin"
            st.sidebar.markdown("<p class='notification'>✅ Admin login successful!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Teacher ----------
if login_type=="Teacher":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher Login / Register")
    teachers = load_teachers()
    user, pwd = st.sidebar.text_input("Username"), st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"): 
        if user in teachers and teachers[user]==hashlib.sha256(pwd.encode()).hexdigest():
            st.session_state.authenticated=True; st.session_state.role="Teacher"
            st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
    if st.sidebar.button("Register"):
        if user in teachers: st.sidebar.markdown("<p class='notification'>❌ Username exists.</p>", unsafe_allow_html=True)
        elif user and pwd: teachers[user]=hashlib.sha256(pwd.encode()).hexdigest(); save_teachers(teachers); st.sidebar.markdown("<p class='notification'>✅ Registered!</p>", unsafe_allow_html=True)
        else: st.sidebar.markdown("<p class='notification'>⚠️ Enter username & password.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"): st.session_state.authenticated=False; st.session_state.role=None; st.rerun()

# ---------- Pages ----------
# Implement all previous functionality for: Upload Answer Key, Grade Student, Search Results, Dashboard, Analytics
# [Use code from previous version, but page selection now uses `st.session_state.page`]
