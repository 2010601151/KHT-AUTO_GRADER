# ---------- app.py (Streamlit Cloud–Ready + OCR Fixed) ----------
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

# ---------- Theme ----------
st.markdown("""
    <style>
        .stApp { background-color: #ffffff; color: #5c4d7d; }
        section[data-testid="stSidebar"] { background-color: #6a1b9a; }
        section[data-testid="stSidebar"] * { color: white !important; }
        h1, h2, h3, h4 { color: #000000; font-weight: bold; }
        div.stButton > button {
            background-color: #6a1b9a; color: white; font-weight: bold;
            border: none; border-radius: 5px; padding: 0.4em 1em;
        }
        div.stButton > button:hover { background-color: #4a0072; color: white; }
        input, textarea, select { border: 1px solid #6a1b9a !important; color: #5c4d7d !important; }
        label, .stFileUploader label { color: #6a1b9a !important; font-weight: bold; }
        table { border: 2px solid #6a1b9a !important; border-collapse: collapse !important; }
        thead tr th { background-color: #6a1b9a !important; color: white !important; font-weight: bold !important; }
        tbody tr:nth-child(odd) { background-color: #f3e5f5 !important; }
        tbody tr:nth-child(even) { background-color: white !important; }
        tbody tr td { color: #5c4d7d !important; font-weight: 500 !important; border: 1px solid #ddd !important; }
    </style>
""", unsafe_allow_html=True)

# ---------- App Title ----------
st.markdown("<h1 style='color:#000000;'>KHT AI Auto-Grader</h1>", unsafe_allow_html=True)

# ---------- Logo ----------
if os.path.exists("kht_logo.jpeg"):
    st.image("kht_logo.jpeg", width=140)

# ---------- Authentication ----------
VALID_TEACHER_PASSWORD = "kht2025"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

if not st.session_state.authenticated:
    st.sidebar.subheader("🔐 Teacher Login Required")
    password = st.sidebar.text_input("Enter Teacher Password", type="password")
    if st.sidebar.button("Login"):
        if password == VALID_TEACHER_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.role = "Teacher"
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Incorrect password.")
    st.stop()
else:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.rerun()

# ---------- Sidebar Navigation ----------
page = st.sidebar.selectbox("📂 Select Page", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "🔍 Search Results (ID or Name)",
    "📊 View Dashboard",
    "📈 Analytics"
])

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
    # Works automatically on Streamlit Cloud Tesseract
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.error(f"OCR Error: {e}")
        return ""

# ---------- Function to Color Score Rows ----------
def color_rows(val):
    if val >= 85: color = '#d4edda'
    elif val >= 60: color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

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
        st.text_area("Extracted Answer Key", key_text, height=200)
        st.success("Answer Key saved successfully!")

# ---------- Page 2: Upload & Grade ----------
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload Student Exam for Grading")
    model_answer = load_answer_key()
    if not model_answer:
        st.warning("Please upload the teacher's answer key before grading.")
        st.stop()

    student_name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    department = st.text_input("Department", value="General").strip().replace("/", "-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/", "-")

    if not all([student_name, student_id, department, subject]):
        st.info("Fill all student details before uploading exam.")
        st.stop()

    exam_file = st.file_uploader("Upload Student Exam (Image)", type=["jpg", "png", "jpeg"])
    if exam_file:
        image = Image.open(exam_file)
        student_answer = extract_text_from_image(image)
        st.text_area("Extracted Student Answer", value=student_answer, height=200)

        if st.button("Grade Answer"):
            score, feedback = grade_with_answer_key(model_answer, student_answer)
            st.success(f"Final Score: {score}%")

            # Inline feedback with semantic similarity
            st.markdown("### Detailed Feedback")
            for line in feedback.split("\n"):
                st.text(line)

            # Save results
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

# ---------- Pages 3,4,5: Search, Dashboard, Analytics ----------
# Keep as in previous version (unchanged)

# ---------- Footer ----------
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; font-size: 16px; color: #6a1b9a;'>
        Built with ❤️ by <strong>Korvah Harper Tarnue</strong><br>
        Software Engineer, Cyprus International University<br>
        Version 1.0 • Updated August 2025
    </div>
    """,
    unsafe_allow_html=True
)
