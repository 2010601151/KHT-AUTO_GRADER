# ---------- app.py ----------
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
import io
from openpyxl import Workbook
import plotly.express as px

st.set_page_config(page_title="KHT Auto Grader", layout="wide")

# ---------- Authentication ----------
USERS_FILE = "teachers.json"

# Load users
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save users
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

users = load_users()

# Ensure admin account always exists
if "admin" not in users:
    users["admin"] = {"password": "admin123", "role": "admin"}
    save_users(users)

if not st.session_state.authenticated:
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher/Admin Access")

    auth_choice = st.sidebar.radio("Select Option", ["Login", "Create Teacher Account"])

    # --- Teacher account creation ---
    if auth_choice == "Create Teacher Account":
        new_user = st.sidebar.text_input("Choose Username")
        new_pass = st.sidebar.text_input("Choose Password", type="password")
        confirm_pass = st.sidebar.text_input("Confirm Password", type="password")

        if st.sidebar.button("Create Account"):
            if not new_user or not new_pass:
                st.sidebar.warning("⚠️ Username and password required.")
            elif new_user in users:
                st.sidebar.warning("⚠️ Username already exists.")
            elif new_pass != confirm_pass:
                st.sidebar.warning("⚠️ Passwords do not match.")
            else:
                users[new_user] = {"password": new_pass, "role": "teacher"}
                save_users(users)
                st.sidebar.success("✅ Teacher account created! Please login.")

    # --- Login Section ---
    elif auth_choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            if username in users and users[username]["password"] == password:
                st.session_state.authenticated = True
                st.session_state.role = users[username].get("role", "teacher")
                st.session_state.username = username
                st.sidebar.success("✅ Login successful!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid credentials.")

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
page = st.sidebar.radio("📌 Navigate", ["🏠 Home", "📤 Upload Exam", "📝 Search Results", "📈 Analytics"])

# ---------- Home ----------
if page == "🏠 Home":
    st.title("KHT Auto Grader")
    st.write("Welcome to the Automated Exam Grading & Analytics System!")

# ---------- Upload Exam ----------
if page == "📤 Upload Exam":
    st.subheader("Upload & Grade Exam")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")

    uploaded_file = st.file_uploader("Upload Student Results CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Required columns check
        required_cols = {"Student ID", "Name", "Score"}
        if not required_cols.issubset(df.columns):
            st.error("❌ CSV must contain: Student ID, Name, Score")
        else:
            save_path = f"results/{st.session_state.username}/{department}/{subject}"
            os.makedirs(save_path, exist_ok=True)
            file_path = os.path.join(save_path, "results.csv")
            df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.to_csv(file_path, index=False)
            st.success(f"✅ Results uploaded and saved for {subject} in {department}!")

# ---------- Search Results ----------
if page == "📝 Search Results":
    st.subheader("Search Student Results")
    student_id = st.text_input("Enter Student ID")

    if student_id:
        found = False
        if st.session_state.role == "teacher":
            base_path = f"results/{st.session_state.username}"
        else:  # admin
            base_path = "results"

        for root, _, files in os.walk(base_path):
            for f in files:
                if f.endswith("results.csv"):
                    df = pd.read_csv(os.path.join(root, f))
                    if student_id in df["Student ID"].astype(str).values:
                        result = df[df["Student ID"].astype(str) == student_id]
                        st.write(result)
                        found = True
        if not found:
            st.warning("⚠️ Student ID not found.")

# ---------- Analytics ----------
if page == "📈 Analytics":
    st.subheader("Analytics Overview")

    if st.session_state.role == "admin":
        st.markdown("### 🌍 Global Admin Dashboard")

        all_results = []
        base_dir = "results"
        if os.path.exists(base_dir):
            for teacher in os.listdir(base_dir):
                teacher_dir = os.path.join(base_dir, teacher)
                if os.path.isdir(teacher_dir):
                    for root, _, files in os.walk(teacher_dir):
                        for f in files:
                            if f.endswith("results.csv"):
                                df_temp = pd.read_csv(os.path.join(root, f))
                                df_temp["Teacher"] = teacher
                                all_results.append(df_temp)

        if all_results:
            df = pd.concat(all_results, ignore_index=True)

            # Teacher filter
            teacher_filter = st.multiselect("Filter by Teacher(s)", sorted(df["Teacher"].unique()), default=list(df["Teacher"].unique()))
            df = df[df["Teacher"].isin(teacher_filter)]

            if df.empty:
                st.warning("⚠️ No results available for selected teacher(s).")
            else:
                # Score Distribution
                fig_dist = px.histogram(df, x="Score", nbins=10, color="Teacher", barmode="overlay")
                st.plotly_chart(fig_dist, use_container_width=True)

                # Metrics
                avg_score = df['Score'].mean()
                max_score = df['Score'].max()
                min_score = df['Score'].min()
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Score", f"{avg_score:.2f}%")
                col2.metric("Highest Score", f"{max_score}%")
                col3.metric("Lowest Score", f"{min_score}%")

                # Trend
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df_sorted = df.sort_values('Timestamp')
                fig_trend = px.line(df_sorted, x='Timestamp', y='Score', color='Teacher', markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)

                # Pass/Fail
                pass_threshold = 50
                df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= pass_threshold else 'Fail')
                fig_pie = px.pie(df, names='Result', title='Pass vs Fail (All Teachers)',
                                color='Result', color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
                st.plotly_chart(fig_pie, use_container_width=True)

                # Top Performers
                st.markdown("### 🏆 Top Performers (All Teachers)")
                top_df = df.sort_values('Score', ascending=False).head(10)[['Teacher','Student ID','Name','Score']]
                st.table(top_df.reset_index(drop=True))

                # Download Data
                st.markdown("### 📥 Download Data")
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download as CSV", data=csv_data, file_name="all_results.csv", mime="text/csv")

                output = io.BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                st.download_button("⬇️ Download as Excel", data=output.getvalue(),
                                   file_name="all_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("ℹ️ No results available yet across teachers.")

    else:  # Teacher Analytics
        department = st.text_input("Department", value="General").strip().replace("/", "-")
        subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
        analytics_path = f"results/{st.session_state.username}/{department}/{subject}/results.csv"

        if os.path.exists(analytics_path):
            df = pd.read_csv(analytics_path)
            if df.empty:
                st.warning("⚠️ No student results yet for this department/subject.")
            else:
                fig_dist = px.histogram(df, x="Score", nbins=10)
                st.plotly_chart(fig_dist, use_container_width=True)

                avg_score = df['Score'].mean()
                max_score = df['Score'].max()
                min_score = df['Score'].min()
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Score", f"{avg_score:.2f}%")
                col2.metric("Highest Score", f"{max_score}%")
                col3.metric("Lowest Score", f"{min_score}%")

                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df_sorted = df.sort_values('Timestamp')
                fig_trend = px.line(df_sorted, x='Timestamp', y='Score', markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)

                pass_threshold = 50
                df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= pass_threshold else 'Fail')
                fig_pie = px.pie(df, names='Result', title='Pass vs Fail', color='Result',
                                color_discrete_map={'Pass':'#28a745', 'Fail':'#dc3545'})
                st.plotly_chart(fig_pie, use_container_width=True)

                st.markdown("### 🏆 Top Performers")
                top_df = df.sort_values('Score', ascending=False).head(10)[['Student ID','Name','Score']]
                st.table(top_df.reset_index(drop=True))
        else:
            st.info("ℹ️ No results available for this department/subject yet.")
