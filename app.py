# ---------- app.py (Full KHT AI Auto-Grader with Floating Menu + Sidebar Toggle) ----------
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

# ---------- Styles & Floating Menu ----------
st.markdown("""
<style>
/* Floating menu button */
.menu-btn {
    position: fixed;
    top: 20px;
    left: 20px;
    background: linear-gradient(135deg, #FFC72C 0%, #DA291C 100%);
    color: white;
    padding: 10px 16px;
    border-radius: 30px;
    font-weight: bold;
    font-size: 14px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    cursor: pointer;
    z-index: 9999;
    transition: 0.3s;
}
.menu-btn:hover {
    transform: scale(1.05);
}

/* Menu container */
.menu-nav {
    position: fixed;
    top: 70px;
    left: 20px;
    background-color: #DA291C;
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    display: none;
    flex-direction: column;
    z-index: 9998;
}
.menu-nav button {
    background-color: #FFC72C;
    color: #DA291C;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    padding: 8px 12px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: 0.2s;
}
.menu-nav button:hover {
    background-color: #FF6F61;
    color: white;
}
.menu-nav.show {
    display: flex;
    animation: slideIn 0.4s ease forwards;
}
@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Notifications */
.notification {
    padding: 10px;
    margin: 10px 0;
    border-radius: 5px;
    font-weight: bold;
}

/* OCR box */
.ocr-box {
    background-color: #fff4e6;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    font-family: monospace;
    white-space: pre-wrap;
}

/* Feedback colors */
.feedback-correct {color: #28a745; font-weight:bold;}
.feedback-partial {color: #ffc107; font-weight:bold;}
.feedback-wrong {color: #dc3545; font-weight:bold;}
</style>

<div class="menu-btn" onclick="
    const menu = document.querySelector('.menu-nav');
    menu.classList.toggle('show');
">
    📂 Menu
</div>

<div class="menu-nav">
    <button onclick='window.parent.postMessage({funcName: "home"}, "*")'>Home</button>
    <button onclick='window.parent.postMessage({funcName: "profile"}, "*")'>Profile</button>
    <button onclick='window.parent.postMessage({funcName: "settings"}, "*")'>Settings</button>
    <button onclick='window.parent.postMessage({funcName: "help"}, "*")'>Help</button>
</div>
""", unsafe_allow_html=True)

# ---------- Handle menu choice ----------
if "menu_choice" not in st.session_state:
    st.session_state.menu_choice = "home"

# JS message handler
def handle_js_message():
    js = st.experimental_get_query_params()
    if "funcName" in js:
        st.session_state.menu_choice = js["funcName"][0]

handle_js_message()

menu_choice = st.session_state.menu_choice
if menu_choice == "home":
    st.header("🏠 Home Page")
elif menu_choice == "profile":
    st.header("👤 Profile Page")
elif menu_choice == "settings":
    st.header("⚙️ Settings Page")
elif menu_choice == "help":
    st.header("❓ Help Page")

# ---------- Sidebar Toggle ----------
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

toggle_label = "☰ Open Sidebar" if st.session_state.sidebar_collapsed else "✖ Close Sidebar"
st.markdown(f"""<button onclick="fetch('/?sidebar_toggle=true')" class="toggle-btn">{toggle_label}</button>""", unsafe_allow_html=True)
if st.query_params.get("sidebar_toggle"):
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    st.query_params.clear()
if st.session_state.sidebar_collapsed:
    st.markdown("<style>section[data-testid='stSidebar'] {{margin-left: -300px;}}</style>", unsafe_allow_html=True)

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#DA291C;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def load_teachers():
    if os.path.exists("teachers.json"):
        with open("teachers.json", "r") as f: return json.load(f)
    return {}
def save_teachers(data):
    with open("teachers.json", "w") as f: json.dump(data, f)
def load_answer_key():
    try:
        with open("answer_key.json", "r") as f: return json.load(f).get("key", "")
    except: return ""
def save_answer_key(text):
    with open("answer_key.json", "w") as f: json.dump({"key": text}, f)
def extract_text_from_image(image):
    try: return pytesseract.image_to_string(image)
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

# ---------- Admin ----------
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
            st.sidebar.error("❌ Incorrect admin credentials")
    if not st.session_state.authenticated: st.stop()

# ---------- Teacher ----------
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
        else: st.sidebar.error("❌ Incorrect username or password")
    if st.sidebar.button("Register Teacher"):
        if teacher_user in teachers: st.sidebar.error("❌ Username exists")
        elif teacher_user and teacher_pass:
            teachers[teacher_user] = hash_password(teacher_pass)
            save_teachers(teachers)
            st.sidebar.success("✅ Teacher registered!")
        else: st.sidebar.warning("⚠️ Enter username & password")
    if not st.session_state.authenticated: st.stop()

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
    st.subheader("Upload Teacher Answer Key (Text/Image)")
    key_file = st.file_uploader("Upload Answer Key", type=["txt","jpg","jpeg","png"])
    if key_file:
        if key_file.type.startswith("text"): key_text = key_file.read().decode("utf-8")
        else: key_text = extract_text_from_image(Image.open(key_file))
        save_answer_key(key_text)
        st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
        st.success("Answer Key saved!")

# ---------- Page 2 ----------
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    model_answer = load_answer_key()
    if not model_answer: st.warning("⚠️ Please upload the teacher's answer key")
    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg","jpeg","png"])
    if exam_file:
        student_answer = extract_text_from_image(Image.open(exam_file))
        st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)
        if st.button("Grade Answer"):
            if not all([student_name, student_id, department, subject]): st.warning("⚠️ Fill all fields")
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)
                st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                for line in feedback.split("\n"):
                    cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                    st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)
                # Save result
                result = {
                    "Student ID": student_id,"Name":student_name,"Department":department,
                    "Subject":subject,"Answer":student_answer,"Score":score,
                    "Feedback":feedback,"Timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_path = f"results/{department}/{subject}/results.csv"
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                try: df = pd.read_csv(save_path); df = pd.concat([df,pd.DataFrame([result])], ignore_index=True)
                except: df = pd.DataFrame([result])
                df.to_csv(save_path,index=False)
                st.success("Result saved!")

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
            if not filtered.empty: st.dataframe(filtered.style.applymap(color_rows, subset=["Score"]))
            else: st.warning("No results found")
        else: st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else: st.info("No results available")

# ---------- Page 4 ----------
if page == "📊 View Dashboard":
    st.subheader("Department/Subject Dashboard")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    dashboard_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(dashboard_path):
        df = pd.read_csv(dashboard_path)
        st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
    else: st.info("No results available")

# ---------- Page 5 ----------
if page == "📈 Analytics":
    st.markdown("### Analytics Overview")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
    analytics_path = f"results/{department}/{subject}/results.csv"
    if os.path.exists(analytics_path):
        df = pd.read_csv(analytics_path)
        if df.empty: st.warning("No results yet")
        else:
            import plotly.express as px
            fig_dist = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#DA291C"], title="Score Distribution")
            st.plotly_chart(fig_dist, use_container_width=True)
            avg_score,max_score,min_score = df['Score'].mean(),df['Score'].max(),df['Score'].min()
            col1,col2,col3=st.columns(3)
            col1.metric("Average Score", f"{avg_score:.2f}%")
            col2.metric("Highest Score", f"{max_score}%")
            col3.metric("Lowest Score", f"{min_score}%")
            df['Timestamp']=pd.to_datetime(df['Timestamp'])
            fig_trend=px.line(df.sort_values('Timestamp'), x='Timestamp', y='Score', markers=True, color_discrete_sequence=["#DA291C"], title="Score Trend")
            st.plotly_chart(fig_trend, use_container_width=True)
            df['Result']=df['Score'].apply(lambda x:'Pass' if x>=50 else 'Fail')
            fig_pie=px.pie(df,names='Result',color='Result',color_discrete_map={'Pass':'#28a745','Fail':'#dc3545'}, title='Pass/Fail Breakdown')
            st.plotly_chart(fig_pie,use_container_width=True)
            st.table(df.sort_values('Score',ascending=False).head(10)[['Student ID','Name','Score']].reset_index(drop=True))
    else: st.info("No results yet")
