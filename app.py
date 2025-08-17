# ---------- app.py (Full KHT AI Auto-Grader with Dynamic Floating Menu + All Pages) ----------
import streamlit as st
import json, os, hashlib, pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
from auto_grader import grade_with_answer_key

# ---------- App Config ----------
st.set_page_config(page_title="KHT AI Auto-Grader", layout="wide")

# ---------- Floating Menu CSS ----------
st.markdown("""
<style>
.menu-btn {position: fixed; top:20px; left:20px; background:linear-gradient(135deg,#6a1b9a 0%,#fff 100%);
color:white; padding:10px 16px; border-radius:30px; font-weight:bold; font-size:14px;
box-shadow:0px 4px 10px rgba(0,0,0,0.2); cursor:pointer; z-index:9999; transition:0.3s;}
.menu-btn:hover {background: linear-gradient(135deg,#fff 0%,#6a1b9a 100%); color:#6a1b9a; transform:scale(1.05);}
.menu-nav {position: fixed; top:70px; left:20px; background-color:#6a1b9a; color:white; padding:15px 20px;
border-radius:10px; box-shadow:0px 4px 15px rgba(0,0,0,0.3); display:none; flex-direction:column; z-index:9998;}
.menu-nav button {background-color:white; color:#6a1b9a; font-weight:bold; border:none; border-radius:5px; padding:8px 12px; margin-bottom:10px; cursor:pointer; transition:0.2s;}
.menu-nav button:hover {background-color:#ffc107; color:#6a1b9a;}
.menu-nav.show {display:flex; animation: slideIn 0.4s ease forwards;}
@keyframes slideIn {from{transform:translateX(-20px);opacity:0;} to{transform:translateX(0);opacity:1;}}
</style>

<div class="menu-btn" onclick="document.querySelector('.menu-nav').classList.toggle('show');">📂 Menu</div>
<div class="menu-nav">
<button onclick="window.parent.postMessage({funcName:'set_menu', menu:'Upload Answer Key'}, '*')">📥 Upload Answer Key</button>
<button onclick="window.parent.postMessage({funcName:'set_menu', menu:'Grade Exam'}, '*')">📤 Upload & Grade Student Exam</button>
<button onclick="window.parent.postMessage({funcName:'set_menu', menu:'Search Results'}, '*')">🔍 Search Results</button>
<button onclick="window.parent.postMessage({funcName:'set_menu', menu:'Dashboard'}, '*')">📊 View Dashboard</button>
<button onclick="window.parent.postMessage({funcName:'set_menu', menu:'Analytics'}, '*')">📈 Analytics</button>
</div>
""", unsafe_allow_html=True)

# ---------- Session State for Dynamic Menu ----------
if "menu_choice" not in st.session_state:
    st.session_state.menu_choice = "Upload Answer Key"

# Update menu_choice from query_params
if "menu_choice" in st.query_params:
    st.session_state.menu_choice = st.query_params["menu_choice"][0]

menu_choice = st.session_state.menu_choice

# ---------- Sidebar Toggle ----------
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

toggle_label = "☰ Open Sidebar" if st.session_state.sidebar_collapsed else "✖ Close Sidebar"
st.markdown(f"<button onclick='fetch(\"/?sidebar_toggle=true\")' class='toggle-btn'>{toggle_label}</button>", unsafe_allow_html=True)

if "sidebar_toggle" in st.query_params:
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    st.experimental_set_query_params()  # clear after toggle

if st.session_state.sidebar_collapsed:
    st.markdown("<style>section[data-testid='stSidebar'] {margin-left: -300px;}</style>", unsafe_allow_html=True)

# ---------- App Title & Logo ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Helper Functions ----------
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def load_teachers(): 
    if os.path.exists("teachers.json"): 
        with open("teachers.json","r") as f: return json.load(f)
    return {}
def save_teachers(data):
    with open("teachers.json","w") as f: json.dump(data,f)
def load_answer_key():
    try: 
        with open("answer_key.json","r") as f: return json.load(f).get("key","")
    except: return ""
def save_answer_key(text):
    with open("answer_key.json","w") as f: json.dump({"key": text},f)
def extract_text_from_image(image):
    try: return pytesseract.image_to_string(image)
    except Exception as e:
        st.markdown(f"<p class='notification'>OCR Error: {e}</p>", unsafe_allow_html=True)
        return ""
def color_rows(val):
    if val>=85: color='#d4edda'
    elif val>=60: color='#fff3cd'
    else: color='#f8d7da'
    return f'background-color: {color}'

# ---------- Authentication ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated=False
    st.session_state.role=None

login_type = st.sidebar.radio("Login as:", ["Admin","Teacher"])

# Admin Login
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH=hash_password("admin123")
if login_type=="Admin":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Admin Login")
    admin_user=st.sidebar.text_input("Username")
    admin_pass=st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login as Admin"):
        if admin_user==ADMIN_USERNAME and hash_password(admin_pass)==ADMIN_PASSWORD_HASH:
            st.session_state.authenticated=True
            st.session_state.role="Admin"
            st.sidebar.markdown("<p class='notification'>✅ Admin login successful!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>❌ Incorrect admin credentials.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# Teacher Login/Register
if login_type=="Teacher":
    st.sidebar.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.sidebar.subheader("🔐 Teacher Login / Register")
    teachers=load_teachers()
    teacher_user=st.sidebar.text_input("Username")
    teacher_pass=st.sidebar.text_input("Password", type="password")
    login_btn=st.sidebar.button("Login as Teacher")
    register_btn=st.sidebar.button("Register Teacher")
    
    if login_btn:
        if teacher_user in teachers and teachers[teacher_user]==hash_password(teacher_pass):
            st.session_state.authenticated=True
            st.session_state.role="Teacher"
            st.sidebar.markdown("<p class='notification'>✅ Login successful!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>❌ Incorrect username or password.</p>", unsafe_allow_html=True)
    if register_btn:
        if teacher_user in teachers: st.sidebar.markdown("<p class='notification'>❌ Username exists.</p>", unsafe_allow_html=True)
        elif teacher_user and teacher_pass:
            teachers[teacher_user]=hash_password(teacher_pass)
            save_teachers(teachers)
            st.sidebar.markdown("<p class='notification'>✅ Teacher registered successfully!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<p class='notification'>⚠️ Enter username & password.</p>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.authenticated: st.stop()

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated=False
    st.session_state.role=None
    st.rerun()

# ---------- Render All Pages ----------
def render_page(choice):
    # ---------- Page 1: Upload Answer Key ----------
    if choice=="Upload Answer Key":
        st.header("📥 Upload Answer Key")
        key_file=st.file_uploader("Upload Answer Key", type=["txt","jpg","jpeg","png"])
        if key_file:
            if key_file.type.startswith("text"): key_text=key_file.read().decode("utf-8")
            else: key_text=extract_text_from_image(Image.open(key_file))
            save_answer_key(key_text)
            st.markdown(f"<div class='ocr-box'><pre>{key_text}</pre></div>", unsafe_allow_html=True)
            st.markdown("<p class='notification'>Answer Key saved successfully!</p>", unsafe_allow_html=True)

    # ---------- Page 2: Upload & Grade Student Exam ----------
    elif choice=="Grade Exam":
        st.header("📤 Upload & Grade Student Exam")
        model_answer = load_answer_key()
        if not model_answer:
            st.markdown("<p class='notification'>⚠️ Please upload the teacher's answer key first.</p>", unsafe_allow_html=True)

        student_name = st.text_input("Student Name")
        student_id = st.text_input("Student ID")
        department = st.text_input("Department", value="General").strip().replace("/", "-")
        subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
        exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg","png","jpeg"])

        if exam_file:
            image = Image.open(exam_file)
            student_answer = extract_text_from_image(image)
            st.markdown(f"<div class='ocr-box'><pre>{student_answer}</pre></div>", unsafe_allow_html=True)

            if st.button("Grade Answer"):
                if not model_answer:
                    st.markdown("<p class='notification'>⚠️ Cannot grade: Answer key missing.</p>", unsafe_allow_html=True)
                elif not all([student_name, student_id, department, subject]):
                    st.markdown("<p class='notification'>⚠️ Fill all student details.</p>", unsafe_allow_html=True)
                else:
                    score, feedback = grade_with_answer_key(model_answer, student_answer)
                    st.markdown(f"<p class='notification'>Final Score: {score}%</p>", unsafe_allow_html=True)
                    st.markdown("<p class='notification'>Detailed Feedback below:</p>", unsafe_allow_html=True)
                    for line in feedback.split("\n"):
                        cls = "feedback-correct" if "✅" in line else "feedback-partial" if "⚠️" in line else "feedback-wrong" if "❌" in line else ""
                        st.markdown(f"<span class='{cls}'>{line}</span>", unsafe_allow_html=True)

                    result = {"Student ID": student_id, "Name": student_name, "Department": department,
                              "Subject": subject, "Answer": student_answer, "Score": score,
                              "Feedback": feedback, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    save_path = f"results/{department}/{subject}/results.csv"
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    try:
                        df = pd.read_csv(save_path)
                        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                    except:
                        df = pd.DataFrame([result])
                    df.to_csv(save_path, index=False)
                    st.markdown("<p class='notification'>Result saved to dashboard!</p>", unsafe_allow_html=True)

    # ---------- Page 3: Search Results ----------
    elif choice=="Search Results":
        st.header("🔍 Search Student Results")
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
                    st.markdown("<p class='notification'>No results found.</p>", unsafe_allow_html=True)
            else:
                st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
        else:
            st.markdown("<p class='notification'>No results found. Upload student exams first.</p>", unsafe_allow_html=True)

    # ---------- Page 4: Dashboard ----------
    elif choice=="Dashboard":
        st.header("📊 Department/Subject Dashboard")
        department = st.text_input("Department", value="General").strip().replace("/", "-")
        subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
        dashboard_path = f"results/{department}/{subject}/results.csv"
        if os.path.exists(dashboard_path):
            df = pd.read_csv(dashboard_path)
            st.dataframe(df.style.applymap(color_rows, subset=["Score"]))
        else:
            st.markdown("<p class='notification'>No results available.</p>", unsafe_allow_html=True)

    # ---------- Page 5: Analytics ----------
    elif choice=="Analytics":
        st.header("📈 Analytics Overview")
        department = st.text_input("Department", value="General").strip().replace("/", "-")
        subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")
        analytics_path = f"results/{department}/{subject}/results.csv"

        if os.path.exists(analytics_path):
            df = pd.read_csv(analytics_path)
            if df.empty:
                st.markdown("<p>⚠️ No student results yet.</p>", unsafe_allow_html=True)
            else:
                import plotly.express as px
                # Score Distribution
                fig_dist = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#6a1b9a"])
                st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.markdown("<p>ℹ️ No results available yet.</p>", unsafe_allow_html=True)

# ---------- Render Current Menu ----------
render_page(menu_choice)
