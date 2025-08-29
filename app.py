import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import pytesseract
import re
import io

# ========== Helper Functions ==========

def extract_text_from_image(image):
    try:
        return pytesseract.image_to_string(image)
    except:
        return ""

def parse_student_answers(answer_text):
    return [line.strip() for line in answer_text.splitlines() if line.strip()]

def grade_mcq(model_answers, student_answers):
    score = 0
    feedback = []
    for idx, (model, student) in enumerate(zip(model_answers, student_answers), start=1):
        if model.strip().lower() == student.strip().lower():
            score += 1
            feedback.append(f"Q{idx}: ✅ Correct")
        else:
            feedback.append(f"Q{idx}: ❌ Wrong (Your answer: {student}, Correct: {model})")
    return score, "\n".join(feedback)

def grade_with_answer_key(model_answer, student_answer):
    score = 0
    feedback = ""
    if model_answer.strip().lower() in student_answer.strip().lower():
        score = 1
        feedback = "✅ Good match."
    else:
        feedback = "❌ Answer does not match."
    return score, feedback

# ========== Session State ==========
for key in ["authenticated","role","remove_teacher","approve_teacher","batch_mode"]:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ["batch_mode"] else False

# ========== Sidebar Navigation ==========
st.sidebar.title("KHT Auto Grader")
page = st.sidebar.radio("Navigate", [
    "📥 Upload Answer Key",
    "📤 Upload & Grade Student Exam",
    "📊 Analytics",
    "⚙️ Admin Dashboard"
])

# ========== Page: Upload Answer Key ==========
if page == "📥 Upload Answer Key":
    st.subheader("Upload Answer Key")
    answer_key_file = st.file_uploader("Upload Answer Key File", type=["txt"])
    if answer_key_file:
        model_answer = answer_key_file.read().decode("utf-8").strip()
        st.session_state["model_answer"] = model_answer
        st.success("Answer key uploaded successfully!")

# ========== Page: Upload & Grade Student Exam ==========
if page == "📤 Upload & Grade Student Exam":
    st.subheader("Upload & Grade Student Exam")
    mode = st.radio("Select Exam Section", ["Multiple Choice","Essay"])
    department = st.text_input("Department", value="General").strip().replace("/","-")
    subject = st.text_input("Subject", value="Misc").strip().replace("/","-")

    st.session_state.batch_mode = st.checkbox(
        "Enable Batch Grading (Upload multiple files)",
        value=st.session_state.batch_mode
    )

    model_answer = st.session_state.get("model_answer","")

    if not st.session_state.batch_mode:
        student_file = st.file_uploader("Upload Student Answer", type=["txt","jpg","jpeg","png"])
        if student_file and st.button("Grade"):
            if student_file.type.startswith("text"):
                student_answer = student_file.read().decode("utf-8").strip()
            else:
                student_answer = extract_text_from_image(Image.open(student_file))

            if mode=="Multiple Choice":
                student_answers = parse_student_answers(student_answer)
                score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)

            result = {
                "Student ID": student_file.name.split(".")[0],
                "Name": student_file.name,
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
            st.success("Result saved successfully!")

# ========== Batch Grading ==========
if st.session_state.batch_mode:
    student_file_label = f"Upload Multiple {mode} Files"
    batch_files = st.file_uploader(student_file_label, type=["txt","jpg","jpeg","png"], accept_multiple_files=True)

    if batch_files and st.button("Grade All Exams"):
        results = []
        for file in batch_files:
            if file.type.startswith("text"):
                student_answer = file.read().decode("utf-8").strip()
            else:
                student_answer = extract_text_from_image(Image.open(file))

            if mode=="Multiple Choice":
                student_answers = parse_student_answers(student_answer)
                score, feedback = grade_mcq(model_answer.splitlines(), student_answers)
            else:
                score, feedback = grade_with_answer_key(model_answer, student_answer)

            result = {
                "Student ID": file.name.split(".")[0],
                "Name": file.name,
                "Department": department,
                "Subject": subject,
                "Answer": student_answer,
                "Score": score,
                "Feedback": feedback,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(result)

        save_path = f"results/{department}/{subject}/results.csv"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            df = pd.read_csv(save_path)
            df = pd.concat([df, pd.DataFrame(results)], ignore_index=True)
        except:
            df = pd.DataFrame(results)
        df.to_csv(save_path, index=False)
        st.success("All batch results saved successfully!")

# ========== Page: Analytics ==========
if page == "📊 Analytics":
    st.subheader("Exam Analytics")
    dept = st.text_input("Department", value="General").strip().replace("/","-")
    subj = st.text_input("Subject", value="Misc").strip().replace("/","-")
    file_path = f"results/{dept}/{subj}/results.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # 🔎 Search / Filter
        search = st.text_input("Search Student (by ID or Name)")
        if search:
            df = df[df["Student ID"].astype(str).str.contains(search, case=False) | 
                    df["Name"].str.contains(search, case=False)]

        st.dataframe(df)

        # 📊 Stats
        st.write("**Average Score:**", df["Score"].mean())
        st.write("**Highest Score:**", df["Score"].max())
        st.write("**Lowest Score:**", df["Score"].min())
        st.write("**Pass Rate (Score > 0):**", (df["Score"]>0).mean()*100, "%")

        # 📥 Download Buttons
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download CSV", csv_buffer.getvalue(), file_name=f"{dept}_{subj}_results.csv")

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button("📥 Download Excel", excel_buffer.getvalue(), file_name=f"{dept}_{subj}_results.xlsx")

        # 🗑️ Clear Results
        if st.button("Clear Results (Danger)"):
            os.remove(file_path)
            st.warning("All results cleared for this subject!")

    else:
        st.warning("No results found for this subject.")

# ========== Page: Admin Dashboard ==========
if page == "⚙️ Admin Dashboard":
    st.subheader("Admin Dashboard")
    st.write("Here you can manage teachers, approve or remove accounts, etc.")
