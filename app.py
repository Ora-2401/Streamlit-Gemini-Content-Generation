import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import io
import csv
from fpdf import FPDF
import re

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Inject custom CSS for professional background and styling
st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="Gemini Content Tool", layout="wide")
st.title("Content Analysis & Creation Tool")
st.write("Analyze text and generate new content using Gemini API.")

st.sidebar.header("Settings")
mode = st.sidebar.selectbox("Select Mode", ["Analyze", "Create Content", "Generate Quiz"])
model_choice = st.sidebar.selectbox("Choose Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])

def parse_quiz(text):
    questions = []
    q_splits = re.split(r'\n?\d+\.\s', text)
    for q_text in q_splits[1:]:
        lines = q_text.strip().split('\n')
        question = lines[0].strip()
        options = {}
        answer = None
        for line in lines[1:]:
            match = re.match(r'([A-D])[\.\)]\s*(.*)', line.strip())
            if match:
                letter, option_text = match.groups()
                options[letter] = option_text
            ans_match = re.search(r'Answer\s*[:\-]\s*([A-D])', line, re.I)
            if ans_match:
                answer = ans_match.group(1)
        questions.append({'question': question, 'options': options, 'answer': answer})
    return questions

def quiz_to_csv_bytes(quiz):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Option A", "Option B", "Option C", "Option D", "Answer"])
    for q in quiz:
        row = [
            q.get('question', ''),
            q['options'].get('A', ''),
            q['options'].get('B', ''),
            q['options'].get('C', ''),
            q['options'].get('D', ''),
            q.get('answer', '')
        ]
        writer.writerow(row)
    return output.getvalue().encode('utf-8')

def quiz_to_pdf_bytes(quiz):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Generated Quiz", ln=True, align='C')
    pdf.ln(10)
    for i, q in enumerate(quiz, start=1):
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, f"{i}. {q['question']}")
        pdf.set_font("Arial", size=12)
        for letter in ['A', 'B', 'C', 'D']:
            if letter in q['options']:
                pdf.multi_cell(0, 8, f"   {letter}. {q['options'][letter]}")
        if q.get('answer'):
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(0, 8, f"Answer: {q['answer']}", ln=True)
        pdf.ln(5)
    pdf_output = pdf.output(dest='S').encode('latin1')
    return pdf_output

def text_to_pdf_bytes(text, title="Content"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf_output = pdf.output(dest='S').encode('latin1')
    return pdf_output

# -------------------------
# ANALYSIS MODE
# -------------------------
if mode == "Analyze":
    st.header("Content Analysis")
    text_input = st.text_area("Enter text to analyze", height=200)
    if st.button("Analyze Text"):
        if text_input.strip():
            model = genai.GenerativeModel(model_choice)
            with st.spinner("Analyzing..."):
                response = model.generate_content(f"Analyze the following text and provide insights:\n{text_input}")
            st.subheader("Analysis Result")
            st.write(response.text)

            pdf_bytes = text_to_pdf_bytes(response.text, title="Analysis Result")
            st.download_button(
                label="Download Analysis as PDF",
                data=pdf_bytes,
                file_name="analysis_result.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Please enter some text.")

# -------------------------
# CREATION MODE
# -------------------------
elif mode == "Create Content":
    st.header("Content Creation")
    creation_prompt = st.text_area("Describe what you want to create", height=200)
    if st.button("Generate Content"):
        if creation_prompt.strip():
            model = genai.GenerativeModel(model_choice)
            with st.spinner("Generating content..."):
                response = model.generate_content(creation_prompt)
            st.subheader("Generated Content")
            st.write(response.text)

            pdf_bytes = text_to_pdf_bytes(response.text, title="Generated Content")
            st.download_button(
                label="Download Content as PDF",
                data=pdf_bytes,
                file_name="generated_content.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Please enter a description.")

# -------------------------
# QUIZ GENERATOR MODE
# -------------------------
elif mode == "Generate Quiz":
    st.header("School Quiz Generator")
    topic = st.text_input("Enter the topic or lesson for the quiz")
    num_questions = st.slider("Number of questions", min_value=1, max_value=20, value=5)
    if st.button("Generate Quiz"):
        if topic.strip():
            model = genai.GenerativeModel(model_choice)
            prompt = (
                f"Create a school quiz with {num_questions} questions on the topic '{topic}'. "
                "Format the output with numbered questions followed by multiple choice options (A, B, C, D), "
                "and indicate the correct answer like 'Answer: B' after each question."
            )
            with st.spinner("Generating quiz..."):
                response = model.generate_content(prompt)
            st.subheader("Generated Quiz")
            st.text_area("Quiz Content", response.text, height=400)

            quiz = parse_quiz(response.text)
            if quiz:
                csv_bytes = quiz_to_csv_bytes(quiz)
                pdf_bytes = quiz_to_pdf_bytes(quiz)

                st.download_button(
                    label="Download Quiz as CSV",
                    data=csv_bytes,
                    file_name=f"{topic}_quiz.csv",
                    mime="text/csv"
                )
                st.download_button(
                    label="Download Quiz as PDF",
                    data=pdf_bytes,
                    file_name=f"{topic}_quiz.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("Could not parse quiz properly for export. Try generating again.")
        else:
            st.warning("Please enter a quiz topic.")
