# ---------- app.py (Full KHT AI Auto-Grader with Floating Top-Left Menu) ----------
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

# ---------- Session State ----------
if "menu_choice" not in st.session_state:
    st.session_state.menu_choice = "home"
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

# ---------- Helper Functions ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_teachers():
    if os.path.exists("teachers.json"):
        with open("teachers.json", "r") as f:
            return json.load(f)
    return {}

def save_teachers(data):
    with open("teachers.json", "w") as f:
        json.dump(data, f)

def load_answer_key():
    try:
        with open("answer_key.json", "r") as f:
            return json.load(f).get("key", "")
    except:
        return ""

def save_answer_key(text):
    with open("answer_key.json", "w") as f:
        json.dump({"key": text}, f)

def extract_text_from_image(image):
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p style='color:red;'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""

def color_rows(val):
    if val >= 85: color = '#d4edda'
    elif val >= 60: color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

# ---------- Floating Menu CSS ----------
st.markdown("""
<style>
.menu-btn {
    position: fixed; top: 20px; left: 20px;
    background: linear-gradient(135deg, #6a1b9a 0%, #ffffff 100%);
    color: white; padding: 10px 16px; border-radius: 30px;
    font-weight: bold; font-size: 14px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    cursor: pointer; z-index: 9999; transition: 0.3s;
}
.menu-btn:hover { background: linear-gradient(135deg, #ffffff 0%, #6a1b9a 100%); color: #6a1b9a; transform: scale(1.05);}
.menu-nav {
    position: fixed; top: 70px; left: 20px; background-color: #6a1b9a;
    color: white; padding: 15px 20px; border-radius: 10px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.3); display: none; flex-direction: column;
    z-index: 9998; transition: transform 0.3s ease, opacity 0.3s ease; transform: translateX(-200px); opacity: 0;
}
.menu-nav.show { display: flex; transform: translateX(0px); opacity: 1; }
.menu-nav button {
    background-color: white; color: #6a1b9a; font-weight: bold;
    border: none; border-radius: 5px; padding: 8px 12px; margin-bottom: 10px; cursor: pointer; transition: 0.2s;
}
.menu-nav button:hover { background-color: #ffc107; color: #6a1b9a; }
</style>
""", unsafe_allow_html=True)

# ---------- Floating Menu HTML ----------
st.markdown("""
<div class="menu-btn" onclick="document.querySelector('.menu-nav').classList.toggle('show')">📂 Menu</div>
<div class="menu-nav">
    <button onclick="window.parent.postMessage({funcName:'home'}, '*')">🏠 Home</button>
    <button onclick="window.parent.postMessage({funcName:'upload_key'}, '*')">📥 Upload Answer Key</button>
    <button onclick="window.parent.postMessage({funcName:'grade_exam'}, '*')">📤 Grade Exam</button>
    <button onclick="window.parent.postMessage({funcName:'search_results'}, '*')">🔍 Search Results</button>
    <button onclick="window.parent.postMessage({funcName:'dashboard'}, '*')">📊 Dashboard</button>
    <button onclick="window.parent.postMessage({funcName:'analytics'}, '*')">📈 Analytics</button>
</div>
""", unsafe_allow_html=True)

# ---------- Detect JS Menu Click ----------
st.components.v1.html("""
<script>
window.addEventListener("message", (event) => {
    const funcName = event.data.funcName;
    if(funcName) {
        fetch('/?menu_choice=' + funcName).then(()=>{window.location.reload()});
    }
});
</script>
""", height=0)

# ---------- Update menu_choice from query params ----------
if st.experimental_get_query_params().get("menu_choice"):
    st.session_state.menu_choice = st.experimental_get_query_params().get("menu_choice")[0]

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#6a1b9a;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Authentication ----------
login_type = st.sidebar.radio("Login as:", ["Admin", "Teacher"])

# Admin Login
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hash_password("admin123")
if login_type == "Admin":
    st.sidebar.subheader("🔐 Admin Login")
    admin_user = st.sidebar.text_input("Username")
    admin_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if admin_user == ADMIN_USERNAME and hash_password(admin_pass) == ADMIN_PASSWORD_HASH:
            st.session_state.authenticated = True
            st.session_state.role = "Admin"
            st.sidebar.success("✅ Admin login successful!")
        else:
            st.sidebar.error("❌ Incorrect admin credentials.")
    if not st.session_state.authenticated:
        st.stop()

# Teacher Login/Register
if login_type == "Teacher":
    st.sidebar.subheader("🔐 Teacher Login / Register")
    teachers = load_teachers()
    teacher_user = st.sidebar.text_input("Username")
    teacher_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Teacher"):
        if teacher_user in teachers and teachers[teacher_user] == hash_password(teacher_pass):
            st.session_state.authenticated = True
            st.session_state.role = "Teacher"
            st.sidebar.success("✅ Login successful!")
        else:
            st.sidebar.error("❌ Incorrect username or password.")
    if st.sidebar.button("Register Teacher"):
        if teacher_user in teachers:
            st.sidebar.error("❌ Username already exists.")
        elif teacher_user and teacher_pass:
            teachers[teacher_user] = hash_password(teacher_pass)
            save_teachers(teachers)
            st.sidebar.success("✅ Teacher registered successfully!")
        else:
            st.sidebar.warning("⚠️ Enter username and password to register.")
    if not st.session_state.authenticated:
        st.stop()

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.experimental_rerun()

# ---------- Pages based on menu_choice ----------
menu_choice = st.session_state.menu_choice

# ----- Home -----
if menu_choice == "home":
    st.header("🏠 Home Page")
    st.markdown("Welcome to the KHT AI Auto-Grader!")

# ----- Upload Answer Key -----
elif menu_choice == "upload_key":
    st.header("📥 Upload Teacher Answer Key")
    key_file = st.file_uploader("Upload Answer Key (Text or Image)", type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"):
            key_text = key_file.read().decode("utf-8")
        else:
            key_text = extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<pre>{key_text}</pre>", unsafe_allow_html=True)
        st.success("✅ Answer Key saved successfully!")

# ----- Grade Exam -----
elif menu_choice == "grade_exam":
    st.header("📤 Upload & Grade Student Exam")
    model_answer = load_answer_key()
    if not model_answer:
        st.warning("⚠️ Please upload the teacher's answer key first.")
    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg","png","jpeg"])
    if exam_file:
        student_answer = extract_text_from_image(Image.open(exam_file))
        st.markdown(f"<pre>{student_answer}</pre>", unsafe_allow_html=True)
        if st.button("Grade Answer"):
            if not all([student_name, student_id, department, subject]):
                st.warning("⚠️ Fill all student details before grading.")
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.success(f"Final Score: {score}%")
                st.markdown("<b>Feedback:</b>")
                st.markdown(f"<pre>{feedback}</pre>")
                save_path = f"results/{department}/{subject}/results.csv"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                try:
                    df = pd.read_csv(save_path)
                    df = pd.concat([df, pd.DataFrame([{
                        "Student ID": student_id, "Name": student_name,
                        "Department": department, "Subject": subject,
                        "Answer": student_answer, "Score": score,
                        "Feedback": feedback, "Timestamp": datetime.now()
                    }])], ignore_index=True)
                except:
                    df = pd.DataFrame([{
                        "Student ID": student_id, "Name": student_name,
                        "Department": department, "Subject": subject,
                        "Answer": student_answer, "Score": score,
                        "Feedback": feedback, "Timestamp": datetime.now()
                    }])
                df.to_csv(save_path, index=False)
                st.success("Result saved to dashboard!")

# ----- Search Results -----
elif menu_choice == "search_results":
    st.header("🔍 Search Student Results")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    search_term = st.text_input("Student ID or Name")
    search_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(search_path):
        df = pd.read_csv(search_path)
        if search_term:
            filtered = df[df.apply(lambda x: search_term.lower() in str(x["Student ID"]).lower() or search_term.lower() in str(x["Name"]).lower(), axis=1)]
            if not filtered.empty:
                st.dataframe(filtered.style.applymap(color_rows, subset=["Score"]))
            else:
                st.info("No results found for this search.")
        else:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.info("No results found. Upload student exams first.")

# ----- Dashboard -----
elif menu_choice == "dashboard":
    st.header("📊 Department/Subject Dashboard")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    dashboard_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(dashboard_path):
        df = pd.read_csv(dashboard_path)
        st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.info("No results available for this department/subject.")

# ----- Analytics -----
elif menu_choice == "analytics":
    st.header("📈 Analytics Overview")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    analytics_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(analytics_path):
        df = pd.read_csv(analytics_path)
        if df.empty:
            st.warning("No student results yet for this department/subject.")
        else:
            # Score Distribution
            st.subheader("Score Distribution")
            fig_dist = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_dist, use_container_width=True)
            # Key Metrics
            st.subheader("Key Metrics")
            avg_score, max_score, min_score = df['Score'].mean(), df['Score'].max(), df['Score'].min()
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Score", f"{avg_score:.2f}%")
            col2.metric("Highest Score", f"{max_score}%")
            col3.metric("Lowest Score", f"{min_score}%")
            # Score Trend
            st.subheader("Score Trend Over Time")
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            fig_trend = px.line(df.sort_values('Timestamp'), x='Timestamp', y='Score', markers=True, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_trend, use_container_width=True)
            # Pass/Fail Pie
            st.subheader("Pass / Fail Breakdown")
            pass_threshold = 50
            df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= pass_threshold else 'Fail')
            fig_pie = px.pie(df, names='Result', color='Result', color_discrete_map={'Pass':'#28a745','Fail':'#dc3545'})
            st.plotly_chart(fig_pie, use_container_width=True)
            # Top Performers
            st.subheader("Top Performers")
            st.table(df.sort_values('Score', ascending=False).head(10)[['Student ID','Name','Score']])
    else:
        st.info("No results available yet. Upload and grade exams first.")
