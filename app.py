# ---------- app.py (Full KHT AI Auto-Grader with Styled Menu & Pages) ----------
import streamlit as st
import streamlit.components.v1 as components
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

# ---------- Style & Floating Menu ----------
menu_html = """
<style>
/* Floating Menu Button */
.menu-btn {
    position: fixed;
    top: 20px;
    left: 20px;
    background: linear-gradient(135deg, #6a1b9a 0%, #ffffff 100%);
    color: white;
    padding: 10px 16px;
    border-radius: 30px;
    font-weight: bold;
    font-size: 14px;
    cursor: pointer;
    z-index: 9999;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
}
.menu-btn:hover {
    background: linear-gradient(135deg, #ffffff 0%, #6a1b9a 100%);
    color: #6a1b9a;
}

/* Menu container */
.menu-nav {
    position: fixed;
    top: 70px;
    left: 20px;
    background-color: #6a1b9a;
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    display: none;
    flex-direction: column;
    z-index: 9998;
}
.menu-nav button {
    background-color: white;
    color: #6a1b9a;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    padding: 8px 12px;
    margin-bottom: 10px;
    cursor: pointer;
}
.menu-nav button:hover {
    background-color: #ffc107;
    color: #6a1b9a;
}
.menu-nav.show { display: flex; }

/* Notifications */
.notification { padding:10px; margin:5px 0; border-radius:5px; }
.feedback-correct { color:green; font-weight:bold; }
.feedback-partial { color:orange; font-weight:bold; }
.feedback-wrong { color:red; font-weight:bold; }
.ocr-box { background:#f3f3f3; padding:10px; border-radius:5px; }
</style>

<div class="menu-btn" onclick="document.querySelector('.menu-nav').classList.toggle('show')">
📂 Menu
</div>

<div class="menu-nav">
    <button onclick="window.parent.postMessage({funcName:'home'}, '*')">Home</button>
    <button onclick="window.parent.postMessage({funcName:'profile'}, '*')">Profile</button>
    <button onclick="window.parent.postMessage({funcName:'settings'}, '*')">Settings</button>
    <button onclick="window.parent.postMessage({funcName:'help'}, '*')">Help</button>
</div>
"""

components.html(menu_html, height=300)

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
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""

def color_rows(val):
    if val >= 85: color = '#d4edda'
    elif val >= 60: color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

# ---------- Authentication ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

login_type = st.sidebar.radio("Login as:", ["Admin", "Teacher"])

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hash_password("admin123")

# ---------- Admin Login ----------
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

# ---------- Teacher Login ----------
if login_type == "Teacher":
    st.sidebar.subheader("🔐 Teacher Login / Register")
    teachers = load_teachers()
    teacher_user = st.sidebar.text_input("Username")
    teacher_pass = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login as Teacher")
    register_btn = st.sidebar.button("Register Teacher")
    
    if login_btn:
        if teacher_user in teachers and teachers[teacher_user] == hash_password(teacher_pass):
            st.session_state.authenticated = True
            st.session_state.role = "Teacher"
            st.sidebar.success("✅ Login successful!")
        else:
            st.sidebar.error("❌ Incorrect username or password.")
    
    if register_btn:
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

# ---------- Logout ----------
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.experimental_rerun()

# ---------- Sidebar Page Selection ----------
page = st.sidebar.selectbox("📂 Select Page", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
])

# ---------- Page 1 ----------
if page == "📥 Upload Answer Key":
    st.subheader("Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader("Upload Answer Key", type=["txt", "jpg", "jpeg", "png"])
    if key_file:
        if key_file.type.startswith("text"):
            key_text = key_file.read().decode("utf-8")
        else:
            key_text = extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
        st.success("✅ Answer Key saved successfully!")

# ---------- Page 2 ----------
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    model_answer = load_answer_key()
    if not model_answer:
        st.warning("⚠️ Please upload the teacher's answer key before grading.")

    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg", "png", "jpeg"])

    if exam_file:
        image = Image.open(exam_file)
        student_answer = extract_text_from_image(image)
        st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)

        if st.button("Grade Answer"):
            if not model_answer:
                st.warning("⚠️ Cannot grade: Answer key missing.")
            elif not all([student_name, student_id, department, subject]):
                st.warning("⚠️ Fill all student details before grading.")
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.success(f"Final Score: {score}%")
                for line in feedback.split("\n"):
                    cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                    st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

                result = {
                    "Student ID": student_id, "Name": student_name, "Department": department,
                    "Subject": subject, "Answer": student_answer, "Score": score,
                    "Feedback": feedback, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                save_path = f"results/{department}/{subject}/results.csv"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                try:
                    df = pd.read_csv(save_path)
                    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                except:
                    df = pd.DataFrame([result])
                df.to_csv(save_path, index=False)
                st.success("Result saved to dashboard!")

# ---------- Page 3 ----------
if page == "🔍 Search Results (ID or Name)":
    st.subheader("Search Student Results")
    department = st.text_input("Department to Search", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject to Search", value="Misc").strip().replace("/", "-")
    search_term = st.text_input("Student ID or Name")
    search_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(search_path):
        df = pd.read_csv(search_path)
        if search_term:
            filtered = df[df.apply(lambda x: search_term.lower() in str(x["Student ID"]).lower() or search_term.lower() in str(x["Name"]).lower(), axis=1)]
            if not filtered.empty:
                st.dataframe(filtered.style.applymap(color_rows, subset=["Score"]))
            else:
                st.warning("No results found for this search.")
        else:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.warning("No results found. Upload student exams first.")

# ---------- Page 4 ----------
if page == "📊 View Dashboard":
    st.subheader("Department/Subject Dashboard")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    dashboard_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(dashboard_path):
        df = pd.read_csv(dashboard_path)
        st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.info("No results available for this department/subject.")

# ---------- Page 5 ----------
if page == "📈 Analytics":
    st.header("📊 Analytics Overview")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    analytics_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(analytics_path):
        df = pd.read_csv(analytics_path)
        if df.empty:
            st.warning("⚠️ No student results yet for this department/subject.")
        else:
            import plotly.express as px
            st.subheader("Score Distribution")
            fig_dist = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_dist, use_container_width=True)

            avg_score, max_score, min_score = df['Score'].mean(), df['Score'].max(), df['Score'].min()
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Score", f"{avg_score:.2f}%")
            col2.metric("Highest Score", f"{max_score}%")
            col3.metric("Lowest Score", f"{min_score}%")

            st.subheader("Score Trend Over Time")
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df_sorted = df.sort_values('Timestamp')
            fig_trend = px.line(df_sorted, x='Timestamp', y='Score', markers=True, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_trend, use_container_width=True)

            st.subheader("Pass / Fail Breakdown")
            df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= 50 else 'Fail')
            fig_pie = px.pie(df, names='Result', color='Result', color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
            st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("Top Performers")
            top_df = df.sort_values('Score', ascending=False).head(10)[['Student ID', 'Name', 'Score']]
            st.table(top_df.reset_index(drop=True))
    else:
        st.info("ℹ️ No results available yet. Upload and grade exams first.")
