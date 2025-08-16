import json
from auto_grader import grade_answer

# Load questions from JSON
with open("questions.json", "r") as file:
    data = json.load(file)

# Process each question
for i, item in enumerate(data, 1):
    print(f"Q{i}: {item['question']}")
    score, feedback = grade_answer(item["model_answer"], item["student_answer"])
    print(f"Student Answer: {item['student_answer']}")
    print(f"Score: {score}%")
    print(f"Feedback: {feedback}")
    print("-" * 50)
