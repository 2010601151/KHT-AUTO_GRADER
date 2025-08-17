# ---------- app.py (Full KHT AI Auto-Grader with Sidebar Toggle - Top Left) ----------
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

# ---------- Theme & Sidebar Animation + Toggle ----------
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color:#000000; }
    section[data-testid="stSidebar"] { background-color: #6a1b9a; padding-top: 2rem; transition: all 0.3s ease-in-out; }
    section[data-testid="stSidebar"] * { color: white !important; }
    .collapsedSidebar { margin-left: -300px !important; }
    .toggle-btn {
        position: fixed; top: 15px; left: 15px; z-index: 9999;
        background-color: #6a1b9a; color: white; border: none;
        border-radius: 8px; padding: 8px 14px; cursor: pointer; font-weight: bold;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3); font-size: 14px;
    }
    .login-card {
        background-color: #ffffff; color: #000000; padding: 1.5rem; border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3); max-width: 280px; margin: 2rem auto;
        transform: translateX(-150%); opacity: 0; animation: slideBounce 0.8s forwards ease-out;
    }
    @keyframes slideBounce {
        0% { transform: translateX(-150%); opacity: 0; }
        70% { transform: translateX(10px); opacity: 1; }
        100% { transform: translateX(0); opacity: 1; }
    }
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
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar Toggle Button ----------
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

toggle_label = "☰ Open Sidebar" if st.session_state.sidebar_collapsed else "✖ Close Sidebar"

st.markdown(f"""
    <button onclick="fetch('/?sidebar_toggle=true')" class="toggle-btn">{toggle_label}</button>
""", unsafe_allow_html=True)

if st.query_params.get("sidebar_toggle"):
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    st.query_params.clear()

if st.session_state.sidebar_collapsed:
    st.markdown("<style>section[data-testid='stSidebar'] {margin-left: -300px;}</style>", unsafe_allow_html=True)

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- User Database ----------
USER_DB = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "teach123", "role": "teacher"},
    "student": {"password": "stud123", "role": "student"}
}

# ---------- Helpers ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ocr_from_image(image):
    return pytesseract.image_to_string(image)

def load_results():
    if os.path.exists("results.json"):
        with open("results.json", "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open("results.json", "w") as f:
        json.dump(results, f, indent=4)

# ---------- Login ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.logged_in:
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.subheader("🔐 Login to KHT Auto-Grader")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_DB and USER_DB[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = USER_DB[username]["role"]
            st.success(f"✅ Logged in as {st.session_state.role.capitalize()}")
        else:
            st.error("❌ Invalid username or password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------- Student Dashboard ----------
if st.session_state.role == "student":
    st.subheader("📤 Upload Your Exam Paper")
    uploaded = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded:
        image = Image.open(uploaded)
        st.image(image, caption="Uploaded Paper", use_container_width=True)
        if st.button("Run OCR + Grade"):
            extracted = ocr_from_image(image)
            st.subheader("📝 OCR Extracted Text")
            st.markdown(f"<div class='ocr-box'>{extracted}</div>", unsafe_allow_html=True)
            # Demo grading
            answer_key = {"Q1": "A", "Q2": "B", "Q3": "C"}
            student_answers = {"Q1": "A", "Q2": "C", "Q3": "C"}
            score, feedback = grade_with_answer_key(answer_key, student_answers)
            st.subheader("📊 Results")
            st.write(f"Final Score: {score}")
            st.json(feedback)
            # Save
            results = load_results()
            results.append({
                "username": "student",
                "score": score,
                "feedback": feedback,
                "timestamp": str(datetime.now())
            })
            save_results(results)

# ---------- Teacher Dashboard ----------
elif st.session_state.role == "teacher":
    st.subheader("📂 Uploaded Results")
    results = load_results()
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df)
    else:
        st.info("No student results yet.")

# ---------- Admin Dashboard ----------
elif st.session_state.role == "admin":
    st.subheader("⚙️ Admin Panel")
    st.write("Manage system settings, users, and reports here.")
