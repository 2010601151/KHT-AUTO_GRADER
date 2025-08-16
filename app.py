# ---------- app.py (Professional Update with Admin + Teacher Accounts) ----------
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

# ---------- Theme & Sidebar Animation ----------
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color:#000000; }

    /* Sidebar fixed background */
    section[data-testid="stSidebar"] {
        background-color: #6a1b9a;
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] * { color: white !important; }

    /* Centered login card with slide-in + bounce */
    .login-card {
        background-color: #ffffff;
        color: #000000;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        max-width: 280px;
        margin: 2rem auto;
        transform: translateX(-150%);
        opacity: 0;
        animation: slideBounce 0.8s forwards ease-out;
    }

    @keyframes slideBounce {
        0% { transform: translateX(-150%); opacity: 0; }
        70% { transform: translateX(10px); opacity: 1; }
        100% { transform: translateX(0); opacity: 1; }
    }

    /* Notification animation */
    .notification {
        color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
        animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn {
        from {opacity:0; transform: translateY(-10px);}
        to {opacity:1; transform: translateY(0);}
    }

    h1, h2, h3, h4 { color: #000000; font-weight: bold; }
    div.stButton > button { background-color: #6a1b9a; color: white; font-weight: bold; border: none; border-radius: 5px; padding: 0.4em 1em; }
    div.stButton > button:hover { background-color: #4a0072; color: white; }
    input, textarea, select { border: 1px solid #6a1b9a !important; color:  #ffffff !important; font-weight:bold; }
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

# ---------- App Title ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)

# ---------- Logo ----------
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Utility Functions ----------
TEACHERS_FILE = "teachers.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_teachers():
    if os.path.exists(TEACHERS_FILE):
        with open(TEACHERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_teachers(data):
    with open(TEACHERS_FILE, "w") as f:
        json.dump(data, f)

# ---------- Authentication ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

teachers = load_teachers()
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hash_password("admin2025")  # Change this password for real deployments

if not st.session_state.authenticated:
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Login")

    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username_input == ADMIN_USERNAME and hash_password(password_input) == ADMIN_PASSWORD_HASH:
            st.session_state.authenticated = True
            st.session_state.role = "Admin"
            st.session_state.username = ADMIN_USERNAME
            st.sidebar.success("✅ Admin login successful!")
        elif username_input in teachers and hash_password(password_input) == teachers[username_input]:
            st.session_state.authenticated = True
            st.session_state.role = "Teacher"
            st.session_state.username = username_input
            st.sidebar.success(f"✅ Teacher '{username_input}' logged in!")
        else:
            st.sidebar.error("❌ Incorrect username or password.")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.stop()
else:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.experimental_rerun()

# ---------- Sidebar Navigation ----------
page_options = [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
]

# Admin only page
if st.session_state.role == "Admin":
    page_options.append("🛠 Manage Teachers")

page = st.sidebar.selectbox("📂 Select Page", page_options)

# ---------- Load/Save Answer Key ----------
def load_answer_key():
    try:
        with open("answer_key.json", "r") as f:
            return json.load(f).get("key", "")
    except:
        return ""

def save_answer_key(text):
    with open("answer_key.json", "w") as f:
        json.dump({"key": text}, f)

# ---------- OCR Helper ----------
def extract_text_from_image(image):
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""

# ---------- Color Score Rows ----------
def color_rows(val):
    if val >= 85: color = '#d4edda'
    elif val >= 60: color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

# ---------- Page: Manage Teachers (Admin Only) ----------
if page == "🛠 Manage Teachers" and st.session_state.role == "Admin":
    st.subheader("👤 Admin: Manage Teacher Accounts")
    st.markdown("### Registered Teachers")
    
    if teachers:
        for username in list(teachers.keys()):
            col1, col2 = st.columns([3,1])
            col1.text(username)
            if col2.button(f"Delete {username}", key=f"del_{username}"):
                del teachers[username]
                save_teachers(teachers)
                st.success(f"✅ Teacher '{username}' deleted successfully.")
                st.experimental_rerun()
    else:
        st.info("No teachers registered yet.")
    
    st.markdown("### Add New Teacher")
    new_user = st.text_input("New Teacher Username", key="new_teacher_user")
    new_pass = st.text_input("New Teacher Password", type="password", key="new_teacher_pass")
    if st.button("Add Teacher"):
        if new_user in teachers:
            st.warning("Username already exists.")
        elif new_user and new_pass:
            teachers[new_user] = hash_password(new_pass)
            save_teachers(teachers)
            st.success(f"✅ Teacher '{new_user}' added successfully.")
            st.experimental_rerun()
        else:
            st.warning("Enter both username and password.")

# ---------- Page 1: Upload Answer Key ----------
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
        st.success("Answer Key saved successfully!")

# ---------- Page 2: Upload & Grade Student Exam ----------
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
                st.markdown("<p class='notification'>Detailed Feedback:</p>", unsafe_allow_html=True)
                for line in feedback.split("\n"):
                    if "✅" in line: cls = "feedback-correct"
                    elif "⚠️" in line: cls = "feedback-partial"
                    elif "❌" in line: cls = "feedback-wrong"
                    else: cls = ""
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
                st.success("Result saved to dashboard!")

# ---------- Page 3: Search Results ----------
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
                st.info("No results found for this search.")
        else:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.info("No results found. Upload student exams first.")

# ---------- Page 4: Dashboard ----------
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

# ---------- Page 5: Analytics ----------
if page == "📈 Analytics":
    st.subheader("📊 Analytics Overview")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    analytics_path = f"results/{department}/{subject}/results.csv"

    if os.path.exists(analytics_path):
        df = pd.read_csv(analytics_path)
        if df.empty:
            st.warning("⚠️ No student results yet for this department/subject.")
        else:
            import plotly.express as px
            st.markdown("### Score Distribution")
            fig_dist = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_dist, use_container_width=True)

            # Key metrics
            avg_score = df['Score'].mean()
            max_score = df['Score'].max()
            min_score = df['Score'].min()
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Score", f"{avg_score:.2f}%")
            col2.metric("Highest Score", f"{max_score}%")
            col3.metric("Lowest Score", f"{min_score}%")

            # Scores Over Time
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df_sorted = df.sort_values('Timestamp')
            fig_trend = px.line(df_sorted, x='Timestamp', y='Score', markers=True, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_trend, use_container_width=True)

            # Pass/Fail Pie Chart
            df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= 50 else 'Fail')
            fig_pie = px.pie(df, names='Result', color='Result', color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
            st.plotly_chart(fig_pie, use_container_width=True)

            # Top Performers
            top_df = df.sort_values('Score', ascending=False).head(10)[['Student ID', 'Name', 'Score']]
            st.table(top_df.reset_index(drop=True))
    else:
        st.info("No results available yet. Upload and grade exams first.")
