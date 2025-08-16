# ---------- app.py (Professional Update, Slide + Bounce Login + Floating Mobile Login Left) ----------
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import os
from auto_grader import grade_with_answer_key

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- CSS & Animations ----------
st.markdown("""
<style>
    /* App background and colors */
    .stApp { background-color: #ffffff; color:#000000; }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #6a1b9a;
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] * { color: white !important; }

    /* Login card with slide-in and bounce */
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

    /* Notifications */
    .notification {
        color:black; font-weight:bold; font-size:16px; padding:5px 10px; border-radius:5px;
        animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }

    h1, h2, h3, h4 { color: #000000; font-weight: bold; }

    /* Buttons */
    div.stButton > button { 
        background-color: #6a1b9a; color: white; font-weight: bold; border: none; border-radius: 5px; padding: 0.4em 1em; 
    }
    div.stButton > button:hover { background-color: #4a0072; }

    /* Inputs */
    input, textarea, select { border: 1px solid #6a1b9a !important; color:#ffffff !important; font-weight:bold; }
    label, .stFileUploader label { color: #6a1b9a !important; font-weight: bold; }

    /* Tables */
    table { border: 2px solid #6a1b9a !important; border-collapse: collapse !important; }
    thead tr th { background-color: #6a1b9a !important; color: white !important; font-weight: bold !important; }
    tbody tr:nth-child(odd) { background-color: #f3e5f5 !important; }
    tbody tr:nth-child(even) { background-color: #ffffff !important; }
    tbody tr td { color: #000000 !important; font-weight: 500 !important; border: 1px solid #ddd !important; }

    /* OCR box */
    .ocr-box { background-color: #f7f7f7; color: #000000; border:1px solid #ccc; padding:10px; border-radius:5px; max-height:300px; overflow:auto; font-size:14px; }

    /* Feedback */
    .feedback-correct { background-color:#28a745; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-partial { background-color:#ffc107; color:black; font-weight:bold; padding:2px 4px; border-radius:3px; }
    .feedback-wrong { background-color:#dc3545; color:white; font-weight:bold; padding:2px 4px; border-radius:3px; }

    /* Floating login button (mobile, left slide-in + bounce) */
    @media (max-width: 768px) {
        .floating-login {
            display: block;
            position: fixed;
            top: 1rem;
            left: -150px; /* Start off-screen left */
            background-color: #6a1b9a;
            color: white;
            font-weight: bold;
            padding: 0.8em 1.2em;
            border-radius: 50px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            z-index: 1000;
            cursor: pointer;
            animation: slideBounceLeft 1s forwards, bounce 1.2s 1s infinite;
        }
        @keyframes slideBounceLeft {
            0% { left: -150px; opacity:0; }
            70% { left: 10px; opacity:1; }
            100% { left: 1rem; opacity:1; }
        }
    }
    @media (min-width: 769px) { .floating-login { display:none; } }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-8px); }
        60% { transform: translateY(-4px); }
    }
</style>
""", unsafe_allow_html=True)

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Authentication ----------
VALID_TEACHER_PASSWORD = "kht2025"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

# ---------- Floating Login Button ----------
if not st.session_state.authenticated:
    st.markdown("""
    <div class="floating-login" onclick="document.getElementById('sidebar-login').click();">
        🔐 Login
    </div>
    <script>
        const btn = document.createElement('button');
        btn.style.display = 'none';
        btn.id = 'sidebar-login';
        document.body.appendChild(btn);
    </script>
    """, unsafe_allow_html=True)

# ---------- Sidebar Login ----------
if not st.session_state.authenticated:
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher Login Required")
    password = st.sidebar.text_input("Enter Teacher Password", type="password")
    if st.sidebar.button("Login"):
        if password == VALID_TEACHER_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.role = "Teacher"
            st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>❌ Incorrect password.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.stop()
else:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.experimental_rerun()

# ---------- Sidebar Navigation ----------
page = st.sidebar.selectbox("📂 Select Page", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
])

# ---------- Helper Functions ----------
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



# ---------- Page: Upload Answer Key ----------
if page == "📥 Upload Answer Key":
    st.subheader("Upload Teacher Answer Key (Text or Image)")
    key_file = st.file_uploader("Upload Answer Key", type=["txt", "jpg", "jpeg", "png"])
    if key_file:
        key_text = key_file.read().decode("utf-8") if key_file.type.startswith("text") else extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
        st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

# ---------- Page: Upload & Grade ----------
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    model_answer = load_answer_key()
    if not model_answer:
        st.markdown("<p class='notification'>⚠️ Please upload the teacher's answer key before grading.</p>", unsafe_allow_html=True)

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
                st.markdown("<p class='notification'>⚠️ Cannot grade: Answer key missing.</p>", unsafe_allow_html=True)
            elif not all([student_name, student_id, department, subject]):
                st.markdown("<p class='notification'>⚠️ Fill all student details before grading.</p>", unsafe_allow_html=True)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                st.markdown("<p class='notification'>Detailed Feedback below:</p>", unsafe_allow_html=True)
                for line in feedback.split("\n"):
                    cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                    st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

                # Save result
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
                st.markdown("<p class='notification'>Result saved to dashboard!</p>", unsafe_allow_html=True)

# ---------- Page: Search Results ----------
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
                st.markdown("<p class='notification'>No results found for this search.</p>", unsafe_allow_html=True)
        else:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.markdown("<p class='notification'>No results found. Upload student exams first.</p>", unsafe_allow_html=True)

# ---------- Page: Dashboard ----------
if page == "📊 View Dashboard":
    st.subheader("Department/Subject Dashboard")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    dashboard_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(dashboard_path):
        df = pd.read_csv(dashboard_path)
        st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.markdown("<p class='notification'>No results available for this department/subject.</p>", unsafe_allow_html=True)

# ---------- Page: Analytics ----------
if page == "📈 Analytics":
    st.markdown("<h2 style='color:#000000; font-weight:bold;'>📊 Analytics Overview</h2>", unsafe_allow_html=True)
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    analytics_path = f"results/{department}/{subject}/results.csv"

    if os.path.exists(analytics_path):
        df = pd.read_csv(analytics_path)
        if df.empty:
            st.markdown("<p style='color:#000000; font-weight:bold;'>⚠️ No student results yet for this department/subject.</p>", unsafe_allow_html=True)
        else:
            import plotly.express as px

            # Score Distribution
            st.markdown("<h3 style='color:#000000; font-weight:bold;'>Score Distribution</h3>", unsafe_allow_html=True)
            fig_dist = px.histogram(df, x="Score", nbins=10, title="Score Distribution", labels={"Score":"Score (%)"}, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_dist, use_container_width=True)

            # Key Metrics
            avg_score, max_score, min_score = df['Score'].mean(), df['Score'].max(), df['Score'].min()
            st.markdown("<h3 style='color:#000000; font-weight:bold;'>Key Metrics</h3>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Average Score<br>{avg_score:.2f}%</p>", unsafe_allow_html=True)
            col2.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Highest Score<br>{max_score}%</p>", unsafe_allow_html=True)
            col3.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Lowest Score<br>{min_score}%</p>", unsafe_allow_html=True)

            # Score Trend
            st.markdown("<h3 style='color:#000000; font-weight:bold;'>Score Trend Over Time</h3>", unsafe_allow_html=True)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df_sorted = df.sort_values('Timestamp')
            fig_trend = px.line(df_sorted, x='Timestamp', y='Score', title="Student Scores Over Time", markers=True, color_discrete_sequence=["#6a1b9a"])
            st.plotly_chart(fig_trend, use_container_width=True)

            # Pass/Fail Pie Chart
            st.markdown("<h3 style='color:#000000; font-weight:bold;'>Pass / Fail Breakdown</h3>", unsafe_allow_html=True)
            pass_threshold = 50
            df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= pass_threshold else 'Fail')
            fig_pie = px.pie(df, names='Result', title='Pass vs Fail', color='Result', color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
            st.plotly_chart(fig_pie, use_container_width=True)

            # Top Performers
            st.markdown("<h3 style='color:#000000; font-weight:bold;'>Top Performers</h3>", unsafe_allow_html=True)
            top_df = df.sort_values('Score', ascending=False).head(10)[['Student ID', 'Name', 'Score']]
            st.table(top_df.reset_index(drop=True))
    else:
        st.markdown("<p style='color:#000000; font-weight:bold;'>ℹ️ No results available yet. Upload and grade exams first.</p>", unsafe_allow_html=True)

