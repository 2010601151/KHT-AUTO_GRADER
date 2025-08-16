import streamlit as st
import json
import pandas as pd
import hashlib
from datetime import datetime
from PIL import Image
import pytesseract

# =====================
# Helper Functions
# =====================
def load_data(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =====================
# Load JSON Data
# =====================
teachers = load_data("teachers.json", {})
results = load_data("results.json", {})
answer_keys = load_data("answer_keys.json", {})

# =====================
# CSS Styling (Purple & White Theme)
# =====================
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            color: #333333;
        }

        /* Top Navbar */
        .topnav {
            overflow: hidden;
            background-color: #6a0dad;  /* Purple background */
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .topnav a {
            float: right;
            color: #ffffff;  /* White text */
            text-align: center;
            padding: 10px 16px;
            text-decoration: none;
            font-size: 16px;
            font-weight: 500;
        }
        .topnav a:hover {
            background-color: #9b30ff;  /* Lighter purple on hover */
            color: white;
            border-radius: 6px;
        }
        .topnav a.active {
            background-color: #4b0082;  /* Darker purple for active */
            color: white;
            border-radius: 6px;
        }

        /* Login & Cards */
        .stButton>button {
            background-color: #6a0dad;
            color: white;
            border-radius: 8px;
            padding: 8px 20px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #9b30ff;
            color: #fff;
        }
        .stTextInput>div>div>input {
            border: 2px solid #6a0dad;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)


# =====================
# Top Navigation
# =====================
pages = ["Home", "Admin", "Teacher", "Upload Answer Key", "Student Upload", "Dashboard"]
choice = st.selectbox("Navigation", pages, index=0, key="nav")

# =====================
# Home Page
# =====================
if choice == "Home":
    st.title("🏫 KHT AI Auto-Grader")
    st.write("Welcome! Use the menu above to navigate.")

# =====================
# Admin Page
# =====================
elif choice == "Admin":
    st.subheader("🔑 Admin Login")
    admin_user = st.text_input("Username")
    admin_pass = st.text_input("Password", type="password")

    if st.button("Login as Admin"):
        if admin_user == "admin" and hash_password(admin_pass) == hash_password("admin123"):
            st.success("Logged in as Admin ✅")

            st.subheader("👩‍🏫 Manage Teachers")

            # Show teachers
            if teachers:
                for t_user, t_pass in teachers.items():
                    st.markdown(f"- **{t_user}** | 🔑 {t_pass[:10]}... (hashed)")
                    if st.button(f"Delete {t_user}"):
                        del teachers[t_user]
                        save_data("teachers.json", teachers)
                        st.warning(f"Teacher {t_user} deleted.")
                        st.stop()
            else:
                st.info("No teachers registered yet.")

            # Add teacher
            new_t_user = st.text_input("New Teacher Username")
            new_t_pass = st.text_input("New Teacher Password", type="password")
            if st.button("Add Teacher"):
                if new_t_user in teachers:
                    st.error("Teacher already exists!")
                else:
                    teachers[new_t_user] = hash_password(new_t_pass)
                    save_data("teachers.json", teachers)
                    st.success("New teacher added ✅")
        else:
            st.error("Invalid admin credentials ❌")

# =====================
# Teacher Page
# =====================
elif choice == "Teacher":
    st.subheader("👨‍🏫 Teacher Login")
    t_user = st.text_input("Teacher Username")
    t_pass = st.text_input("Password", type="password")

    if st.button("Login as Teacher"):
        if t_user in teachers and teachers[t_user] == hash_password(t_pass):
            st.success(f"Welcome {t_user} ✅")

            st.subheader("📥 Upload Answer Key")
            answer_text = st.text_area("Enter Answer Key (comma-separated)")
            ans_file = st.file_uploader("Or upload image (OCR)", type=["png", "jpg"])

            if st.button("Save Answer Key"):
                if answer_text:
                    answer_keys[t_user] = answer_text.split(",")
                    save_data("answer_keys.json", answer_keys)
                    st.success("Answer key saved!")
                elif ans_file:
                    try:
                        text = pytesseract.image_to_string(Image.open(ans_file))
                        answer_keys[t_user] = text.split(",")
                        save_data("answer_keys.json", answer_keys)
                        st.success("Answer key saved from OCR!")
                    except:
                        st.error("OCR failed. Try again.")
                else:
                    st.warning("Provide text or image.")
        else:
            st.error("Invalid teacher credentials ❌")

# =====================
# Student Upload
# =====================
elif choice == "Student Upload":
    st.subheader("📤 Student Exam Upload")
    student_name = st.text_input("Student Name")
    teacher_choice = st.selectbox("Select Teacher", list(teachers.keys()))
    stu_file = st.file_uploader("Upload Answers (CSV)", type=["csv"])

    if st.button("Submit for Grading"):
        if stu_file and teacher_choice in answer_keys:
            df = pd.read_csv(stu_file)
            answers = df["Answer"].tolist()
            key = answer_keys[teacher_choice]

            score = sum([1 for a, b in zip(answers, key) if a.strip() == b.strip()])
            total = len(key)
            percent = round((score/total)*100, 2)

            results[student_name] = {"teacher": teacher_choice, "score": percent, "time": str(datetime.now())}
            save_data("results.json", results)

            st.success(f"Graded ✅ {student_name} scored {percent}%")
        else:
            st.error("Missing file or no answer key.")

# =====================
# Dashboard
# =====================
elif choice == "Dashboard":
    st.subheader("📊 Dashboard")

    if results:
        df = pd.DataFrame(results).T
        st.dataframe(df)
        st.bar_chart(df["score"])
    else:
        st.info("No results yet.")
