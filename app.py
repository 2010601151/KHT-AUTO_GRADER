# ---------- app.py (Full App with Accounts, Admin, Per-Teacher Data, Global Analytics & Downloads) ----------
import os
import io
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import streamlit as st
import hashlib

# Your grading function
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
        animation: fadeIn 0.6s ease-in-out; background: #f3e5f5;
    }
    @keyframes fadeIn {
        from {opacity:0; transform: translateY(-10px);}
        to {opacity:1; transform: translateY(0);}
    }

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

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helpers ----------
USERS_FILE = "teachers.json"
ANSWER_KEYS_DIR = "answer_keys"
RESULTS_DIR = "results"
os.makedirs(ANSWER_KEYS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def list_teacher_usernames(include_admin=False):
    users = load_users()
    names = []
    for u, meta in users.items():
        role = meta.get("role", "teacher")
        if role == "teacher" or (include_admin and role == "admin"):
            names.append(u)
    return sorted(names)

def ensure_admin_user():
    users = load_users()
    if "admin" not in users:
        users["admin"] = {"password": hash_password("admin123"), "role": "admin"}
        save_users(users)

def load_answer_key(username: str) -> str:
    path = os.path.join(ANSWER_KEYS_DIR, f"{username}.json")
    try:
        with open(path, "r") as f:
            return json.load(f).get("key", "")
    except:
        return ""

def save_answer_key(username: str, text: str):
    path = os.path.join(ANSWER_KEYS_DIR, f"{username}.json")
    with open(path, "w") as f:
        json.dump({"key": text}, f, indent=2)

def extract_text_from_image(image):
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""

def color_rows(val):
    try:
        v = float(val)
    except:
        return ''
    if v >= 85: color = '#d4edda'
    elif v >= 60: color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

def teacher_results_path(username: str, department: str, subject: str) -> str:
    department = department.strip().replace("/", "-")
    subject = subject.strip().replace("/", "-")
    return f"{RESULTS_DIR}/{username}/{department}/{subject}/results.csv"

# ---------- Authentication ----------
ensure_admin_user()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

users = load_users()

if not st.session_state.authenticated:
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher/Admin Access")

    choice = st.sidebar.radio("Select Option", ["Login", "Create Teacher Account"])

    if choice == "Create Teacher Account":
        new_user = st.sidebar.text_input("Choose Username")
        new_pass = st.sidebar.text_input("Choose Password", type="password")
        confirm_pass = st.sidebar.text_input("Confirm Password", type="password")
        if st.sidebar.button("Create Account"):
            if not new_user or not new_pass:
                st.sidebar.markdown("<p class='notification'>⚠️ Username and password required.</p>", unsafe_allow_html=True)
            elif new_user in users:
                st.sidebar.markdown("<p class='notification'>⚠️ Username already exists.</p>", unsafe_allow_html=True)
            elif new_pass != confirm_pass:
                st.sidebar.markdown("<p class='notification'>⚠️ Passwords do not match.</p>", unsafe_allow_html=True)
            else:
                users[new_user] = {"password": hash_password(new_pass), "role": "teacher"}
                save_users(users)
                st.sidebar.markdown("<p class='notification'>✅ Teacher account created! Please login.</p>", unsafe_allow_html=True)

    if choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.role = users[username].get("role", "teacher")
                st.session_state.username = username
                st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
                st.rerun()
            else:
                st.sidebar.markdown("<p class='notification'>❌ Invalid credentials.</p>", unsafe_allow_html=True)

    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.stop()
else:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# ---------- Sidebar Navigation ----------
page = st.sidebar.selectbox("📂 Select Page", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
])

# Small helper: when Admin is doing teacher-specific actions, let them pick a target teacher
def pick_target_teacher(default_to_self=True) -> str:
    if st.session_state.role == "admin":
        teachers = list_teacher_usernames(include_admin=False)
        if not teachers:
            st.warning("No teacher accounts found yet.")
            return None
        return st.selectbox("Select Teacher Account", teachers)
    else:
        return st.session_state.username if default_to_self else None

# ---------- Page 1: Upload Answer Key ----------
if page == "📥 Upload Answer Key":
    st.subheader("Upload Teacher Answer Key (Text or Image)")
    target_user = pick_target_teacher()  # admin can choose, teacher uses own
    if target_user is None:
        st.stop()

    # Show existing key (if any)
    existing_key = load_answer_key(target_user)
    if existing_key:
        st.markdown("**Current Saved Answer Key:**")
        st.markdown(f"<div class='ocr-box'><pre>{existing_key}</pre></div>", unsafe_allow_html=True)

    key_file = st.file_uploader("Upload Answer Key", type=["txt", "jpg", "jpeg", "png"])
    manual_text = st.text_area("Or paste/edit Answer Key here")

    if key_file or manual_text:
        if st.button("Save Answer Key"):
            if key_file:
                if key_file.type.startswith("text"):
                    key_text = key_file.read().decode("utf-8")
                else:
                    key_text = extract_text_from_image(Image.open(key_file))
            else:
                key_text = manual_text
            save_answer_key(target_user, key_text)
            st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
            st.markdown("<p class='notification'>✅ Answer Key saved successfully!</p>", unsafe_allow_html=True)

# ---------- Page 2: Upload & Grade ----------
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    target_user = pick_target_teacher()
    if target_user is None:
        st.stop()

    model_answer = load_answer_key(target_user)
    if not model_answer:
        st.markdown("<p class='notification'>⚠️ Please upload the teacher's answer key before grading.</p>", unsafe_allow_html=True)

    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General")
    subject = st.text_input("Subject", value="Misc")
    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg", "png", "jpeg"])

    if exam_file:
        image = Image.open(exam_file)
        student_answer = extract_text_from_image(image)
        st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)

        if st.button("Grade Answer"):
            if not model_answer:
                st.markdown("<p class='notification'>⚠️ Cannot grade: Answer key missing.</p>", unsafe_allow_html=True)
            elif not all([student_name, student_id, department.strip(), subject.strip()]):
                st.markdown("<p class='notification'>⚠️ Fill all student details before grading.</p>", unsafe_allow_html=True)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                st.markdown("<p class='notification'>Detailed Feedback below:</p>", unsafe_allow_html=True)
                for line in feedback.split("\n"):
                    if "✅" in line: cls = "feedback-correct"
                    elif "⚠️" in line: cls = "feedback-partial"
                    elif "❌" in line: cls = "feedback-wrong"
                    else: cls = ""
                    st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

                result = {
                    "Teacher": target_user,
                    "Student ID": student_id,
                    "Name": student_name,
                    "Department": department.strip().replace("/", "-"),
                    "Subject": subject.strip().replace("/", "-"),
                    "Answer": student_answer,
                    "Score": score,
                    "Feedback": feedback,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                save_path = teacher_results_path(target_user, department, subject)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                try:
                    df = pd.read_csv(save_path)
                    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                except:
                    df = pd.DataFrame([result])
                df.to_csv(save_path, index=False)
                st.markdown("<p class='notification'>✅ Result saved to dashboard!</p>", unsafe_allow_html=True)

# ---------- Page 3: Search Results ----------
if page == "🔍 Search Results (ID or Name)":
    st.subheader("Search Student Results")
    target_user = pick_target_teacher()
    if target_user is None:
        st.stop()

    department = st.text_input("Department to Search", value="General")
    subject = st.text_input("Subject to Search", value="Misc")
    search_term = st.text_input("Student ID or Name")
    search_path = teacher_results_path(target_user, department, subject)

    if os.path.exists(search_path):
        df = pd.read_csv(search_path)
        if search_term:
            term = search_term.lower().strip()
            filtered = df[df.apply(
                lambda x: term in str(x.get("Student ID","")).lower() or term in str(x.get("Name","")).lower(),
                axis=1
            )]
            if not filtered.empty:
                st.dataframe(filtered.style.applymap(color_rows, subset=["Score"]))
            else:
                st.markdown("<p class='notification'>No results found for this search.</p>", unsafe_allow_html=True)
        else:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else:
        st.markdown("<p class='notification'>No results found. Upload student exams first.</p>", unsafe_allow_html=True)

# ---------- Page 4: View Dashboard ----------
if page == "📊 View Dashboard":
    st.subheader("Department/Subject Dashboard")
    target_user = pick_target_teacher()
    if target_user is None:
        st.stop()

    department = st.text_input("Department", value="General")
    subject = st.text_input("Subject", value="Misc")
    dashboard_path = teacher_results_path(target_user, department, subject)

    if os.path.exists(dashboard_path):
        df = pd.read_csv(dashboard_path)
        if not df.empty:
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
        else:
            st.markdown("<p class='notification'>No results available for this department/subject yet.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='notification'>No results available for this department/subject.</p>", unsafe_allow_html=True)

# ---------- Page 5: Analytics ----------
if page == "📈 Analytics":
    st.markdown("<h2 style='color:#000000; font-weight:bold;'>📊 Analytics Overview</h2>", unsafe_allow_html=True)

    # --- Admin Mode: Global Dashboard Across All Teachers ---
    if st.session_state.role == "admin":
        st.subheader("🌍 Global Admin Dashboard")

        all_results = []
        base_dir = RESULTS_DIR
        if os.path.exists(base_dir):
            for teacher in os.listdir(base_dir):
                teacher_dir = os.path.join(base_dir, teacher)
                if os.path.isdir(teacher_dir):
                    for root, _, files in os.walk(teacher_dir):
                        for f in files:
                            if f.endswith("results.csv"):
                                try:
                                    df_temp = pd.read_csv(os.path.join(root, f))
                                    df_temp["Teacher"] = teacher
                                    all_results.append(df_temp)
                                except Exception as e:
                                    st.write(f"Skipping {os.path.join(root, f)} due to error: {e}")

        if all_results:
            df = pd.concat(all_results, ignore_index=True)

            # Filters
            teacher_filter = st.multiselect("Filter by Teacher(s)", sorted(df["Teacher"].unique()),
                                            default=list(sorted(df["Teacher"].unique())))
            df = df[df["Teacher"].isin(teacher_filter)]

            if df.empty:
                st.warning("⚠️ No results available for selected teacher(s).")
            else:
                import plotly.express as px

                # Score Distribution (all teachers)
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Global Score Distribution</h3>", unsafe_allow_html=True)
                fig_dist = px.histogram(df, x="Score", nbins=10, color="Teacher", barmode="overlay")
                st.plotly_chart(fig_dist, use_container_width=True)

                # Key Metrics
                avg_score = df['Score'].mean()
                max_score = df['Score'].max()
                min_score = df['Score'].min()
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Key Metrics (All Teachers)</h3>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Score", f"{avg_score:.2f}%")
                col2.metric("Highest Score", f"{max_score}%")
                col3.metric("Lowest Score", f"{min_score}%")

                # Scores Over Time
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Global Score Trend</h3>", unsafe_allow_html=True)
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df_sorted = df.sort_values('Timestamp')
                fig_trend = px.line(df_sorted, x='Timestamp', y='Score', color='Teacher', markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)

                # Pass/Fail Pie Chart (All Teachers)
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Pass / Fail Breakdown</h3>", unsafe_allow_html=True)
                pass_threshold = 50
                df['Result'] = df['Score'].apply(lambda x: 'Pass' if float(x) >= pass_threshold else 'Fail')
                fig_pie = px.pie(df, names='Result', title='Pass vs Fail (All Teachers)', color='Result',
                                 color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
                st.plotly_chart(fig_pie, use_container_width=True)

                # Top Performers (Global)
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Top Performers (All Teachers)</h3>", unsafe_allow_html=True)
                top_df = df.sort_values('Score', ascending=False).head(10)[['Teacher','Student ID','Name','Score']]
                st.table(top_df.reset_index(drop=True))

                # --- Download Options for Admin ---
                st.markdown("### 📥 Download Data")
                # CSV
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download as CSV",
                    data=csv_data,
                    file_name="all_results.csv",
                    mime="text/csv"
                )
                # Excel
                try:
                    # Try openpyxl engine
                    output = io.BytesIO()
                    df.to_excel(output, index=False, engine="openpyxl")
                    st.download_button(
                        label="⬇️ Download as Excel",
                        data=output.getvalue(),
                        file_name="all_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception:
                    # Fallback to xlsxwriter
                    try:
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                            df.to_excel(writer, index=False, sheet_name="Results")
                        st.download_button(
                            label="⬇️ Download as Excel (fallback)",
                            data=output.getvalue(),
                            file_name="all_results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.info(f"Excel export unavailable ({e}). Use CSV instead.")
        else:
            st.warning("ℹ️ No results available yet across teachers.")

    # --- Teacher Mode: Per-Teacher Analytics ---
    else:
        department = st.text_input("Department", value="General")
        subject = st.text_input("Subject", value="Misc")
        analytics_path = teacher_results_path(st.session_state.username, department, subject)

        if os.path.exists(analytics_path):
            df = pd.read_csv(analytics_path)
            if df.empty:
                st.markdown("<p style='color:#000000; font-weight:bold;'>⚠️ No student results yet for this department/subject.</p>", unsafe_allow_html=True)
            else:
                import plotly.express as px

                # Score Distribution Histogram
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Score Distribution</h3>", unsafe_allow_html=True)
                fig_dist = px.histogram(df, x="Score", nbins=10,
                                        title="Score Distribution",
                                        labels={"Score":"Score (%)"},
                                        color_discrete_sequence=["#6a1b9a"])
                st.plotly_chart(fig_dist, use_container_width=True)

                # Key Metrics
                avg_score = df['Score'].mean()
                max_score = df['Score'].max()
                min_score = df['Score'].min()
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Key Metrics</h3>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Average Score<br>{avg_score:.2f}%</p>", unsafe_allow_html=True)
                col2.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Highest Score<br>{max_score}%</p>", unsafe_allow_html=True)
                col3.markdown(f"<p style='color:#000000; font-weight:bold; font-size:18px;'>Lowest Score<br>{min_score}%</p>", unsafe_allow_html=True)

                # Scores Over Time
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Score Trend Over Time</h3>", unsafe_allow_html=True)
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df_sorted = df.sort_values('Timestamp')
                fig_trend = px.line(df_sorted, x='Timestamp', y='Score',
                                    title="Student Scores Over Time",
                                    markers=True, color_discrete_sequence=["#6a1b9a"])
                st.plotly_chart(fig_trend, use_container_width=True)

                # Pass/Fail Pie Chart
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Pass / Fail Breakdown</h3>", unsafe_allow_html=True)
                pass_threshold = 50
                df['Result'] = df['Score'].apply(lambda x: 'Pass' if float(x) >= pass_threshold else 'Fail')
                fig_pie = pd.DataFrame(df['Result'].value_counts()).reset_index()
                import plotly.express as px
                fig_pf = px.pie(df, names='Result', title='Pass vs Fail',
                                color='Result',
                                color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
                st.plotly_chart(fig_pf, use_container_width=True)

                # Top Performers Leaderboard
                st.markdown("<h3 style='color:#000000; font-weight:bold;'>Top Performers</h3>", unsafe_allow_html=True)
                top_df = df.sort_values('Score', ascending=False).head(10)[['Student ID', 'Name', 'Score']]
                st.table(top_df.reset_index(drop=True))

        else:
            st.markdown("<p style='color:#000000; font-weight:bold;'>ℹ️ No results available for this department/subject yet. Upload and grade exams first.</p>", unsafe_allow_html=True)
