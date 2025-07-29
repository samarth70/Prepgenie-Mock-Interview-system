# PrepGenie/app.py
import gradio as gr
import os
import tempfile
import PyPDF2
import google.generativeai as genai
from transformers import BertTokenizer, TFBertModel
import numpy as np
import speech_recognition as sr
from dotenv import load_dotenv
import soundfile as sf
import json
import matplotlib.pyplot as plt
import io
import re

# --- Firebase Admin SDK Setup ---
import firebase_admin
from firebase_admin import credentials, auth

# Load environment variables
load_dotenv()

# --- Robust Firebase Initialization ---
def initialize_firebase():
    """Attempts to initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        print("Firebase app already initialized.")
        return firebase_admin.get_app()

    cred = None
    try:
        firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "prepgenie-64134-firebase-adminsdk-fbsvc-3370ac4ab9.json")
        if firebase_credentials_path and os.path.exists(firebase_credentials_path):
            print(f"Initializing Firebase with credentials file: {firebase_credentials_path}")
            cred = credentials.Certificate(firebase_credentials_path)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized successfully using credentials file.")
            return firebase_app
        elif not firebase_credentials_path:
             print("FIREBASE_CREDENTIALS_PATH is not set or is None.")
        else:
             print(f"Firebase credentials file not found at {firebase_credentials_path}")
    except Exception as e:
        print(f"Failed to initialize Firebase using credentials file: {e}")

    try:
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_credentials_json:
            print("Initializing Firebase with credentials from FIREBASE_CREDENTIALS_JSON environment variable.")
            cred_dict = json.loads(firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized successfully using FIREBASE_CREDENTIALS_JSON.")
            return firebase_app
        else:
             print("FIREBASE_CREDENTIALS_JSON environment variable not set.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing FIREBASE_CREDENTIALS_JSON: {e}")
    except Exception as e:
        print(f"Failed to initialize Firebase using FIREBASE_CREDENTIALS_JSON: {e}")

    print("Warning: Firebase Admin SDK could not be initialized. Authentication features will not work.")
    return None

FIREBASE_APP = initialize_firebase()
FIREBASE_AVAILABLE = FIREBASE_APP is not None

# --- Configure Generative AI (CHANGED MODEL) ---
# Replace 'gemini-pro' with 'gemini-flash-2.5'
genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or "YOUR_DEFAULT_API_KEY_HERE")
# text_model = genai.GenerativeModel("gemini-pro") # OLD
text_model = genai.GenerativeModel("gemini-1.5-flash") # NEW - Use the correct model name
print("Using Generative AI model: gemini-1.5-flash")

# Load BERT model and tokenizer
try:
    model = TFBertModel.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    BERT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load BERT model/tokenizer: {e}")
    BERT_AVAILABLE = False
    model = None
    tokenizer = None

# --- Helper Functions (Logic adapted from Streamlit) ---

def getallinfo(data):
    if not data or not data.strip():
        return "No data provided or data is empty."
    # Use the new model instance
    text = f"""{data} is given by the user. Make sure you are getting the details like name, experience,
            education, skills of the user like in a resume. If the details are not provided return: not a resume.
            If details are provided then please try again and format the whole in a single paragraph covering all the information. """
    try:
        # Use the correct model instance
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error in getallinfo: {e}") # This should now be clearer
        return "Error processing resume data."

def file_processing(pdf_file_path):
    """Processes the uploaded PDF file given its path."""
    if not pdf_file_path:
        return ""
    try:
        if hasattr(pdf_file_path, 'name'):
            file_path_to_use = pdf_file_path.name
        else:
            file_path_to_use = pdf_file_path

        with open(file_path_to_use, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error processing PDF {pdf_file_path}: {e}")
        return ""

def get_embedding(text):
    if not text or not text.strip():
         return np.zeros((1, 768))

    if not BERT_AVAILABLE or not model or not tokenizer:
        print("BERT model not available for embedding.")
        return np.zeros((1, 768))

    try:
        encoded_text = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        output = model(encoded_text)
        embedding = output.last_hidden_state[:, 0, :]
        return embedding.numpy()
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return np.zeros((1, 768))

def generate_feedback(question, answer):
    if not question or not question.strip() or not answer or not answer.strip():
        return "0.00"

    try:
        question_embedding = get_embedding(question)
        answer_embedding = get_embedding(answer)
        q_emb = np.squeeze(question_embedding)
        a_emb = np.squeeze(answer_embedding)

        dot_product = np.dot(q_emb, a_emb)
        norms = np.linalg.norm(q_emb) * np.linalg.norm(a_emb)
        if norms == 0:
            similarity_score = 0.0
        else:
            similarity_score = dot_product / norms
        return f"{similarity_score:.2f}"
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "0.00"

def generate_questions(roles, data):
    if not roles or (isinstance(roles, list) and not any(roles)) or not data or not data.strip():
        return ["Could you please introduce yourself based on your resume?"]

    questions = []
    if isinstance(roles, list):
        roles_str = ", ".join(roles)
    else:
        roles_str = str(roles)

    text = f"""If this is not a resume then return text uploaded pdf is not a resume. this is a resume overview of the candidate.
            The candidate details are in {data}. The candidate has applied for the role of {roles_str}.
            Generate questions for the candidate based on the role applied and on the Resume of the candidate.
            Not always necessary to ask only technical questions related to the role but the logic of question
            should include the job applied for because there might be some deep tech questions which the user might not know.
            Ask some personal questions too. Ask no additional questions. Don't categorize the questions.
            ask 2 questions only. directly ask the questions not anything else.
            Also ask the questions in a polite way. Ask the questions in a way that the candidate can understand the question.
            and make sure the questions are related to these metrics: Communication skills, Teamwork and collaboration,
            Problem-solving and critical thinking, Time management and organization, Adaptability and resilience."""
    try:
        # Use the correct model instance
        response = text_model.generate_content(text)
        response.resolve()
        questions_text = response.text.strip()
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        if not questions:
             questions = [q.strip() for q in questions_text.split('?') if q.strip()]
        if not questions:
             questions = [q.strip() for q in questions_text.split('.') if q.strip()]
        questions = questions[:2] if questions else ["Could you please introduce yourself based on your resume?"]
    except Exception as e:
        print(f"Error generating questions: {e}")
        questions = ["Could you please introduce yourself based on your resume?"]
    return questions

def generate_overall_feedback(data, percent, answer, questions):
    if not data or not data.strip() or not answer or not answer.strip() or not questions:
        return "Unable to generate feedback due to missing information."

    if isinstance(percent, float):
        percent_str = f"{percent:.2f}"
    else:
        percent_str = str(percent)

    prompt = f"""As an interviewer, provide concise feedback (max 150 words) for candidate {data}.
    Questions asked: {questions}
    Candidate's answers: {answer}
    Score: {percent_str}
    Feedback should include:
    1. Overall performance assessment (2-3 sentences)
    2. Key strengths (2-3 points)
    3. Areas for improvement (2-3 points)
    Be honest and constructive. Do not mention the exact score, but rate the candidate out of 10 based on their answers."""
    try:
        # Use the correct model instance
        response = text_model.generate_content(prompt)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error generating overall feedback: {e}")
        return "Feedback could not be generated."

def generate_metrics(data, answer, question):
    if not data or not data.strip() or not answer or not answer.strip() or not question or not question.strip():
        return {
            "Communication skills": 0.0, "Teamwork and collaboration": 0.0,
            "Problem-solving and critical thinking": 0.0, "Time management and organization": 0.0,
            "Adaptability and resilience": 0.0
        }

    metrics = {}
    text = f"""Here is the overview of the candidate {data}. In the interview the question asked was {question}.
    The candidate has answered the question as follows: {answer}. Based on the answers provided, give me the metrics related to:
    Communication skills, Teamwork and collaboration, Problem-solving and critical thinking, Time management and organization,
    Adaptability and resilience.
    Rules for rating:
    - Rate each skill from 0 to 10
    - If the answer is empty, 'Sorry could not recognize your voice', meaningless, or irrelevant: rate all skills as 0
    - Only provide numeric ratings without any additional text or '/10'
    - Ratings must reflect actual content quality - do not give courtesy points
    - Consider answer relevance to the specific skill being rated
    Format:
    Communication skills: [rating]
    Teamwork and collaboration: [rating]
    Problem-solving and critical thinking: [rating]
    Time management and organization: [rating]
    Adaptability and resilience: [rating]"""
    try:
        # Use the correct model instance
        response = text_model.generate_content(text)
        response.resolve()
        metrics_text = response.text.strip()
        for line in metrics_text.split('\n'):
            if ':' in line:
                key, value_str = line.split(':', 1)
                key = key.strip()
                try:
                    value_clean = value_str.strip().split()[0]
                    value = float(value_clean)
                    metrics[key] = value
                except (ValueError, IndexError):
                    metrics[key] = 0.0
        expected_metrics = [
            "Communication skills", "Teamwork and collaboration",
            "Problem-solving and critical thinking", "Time management and organization",
            "Adaptability and resilience"
        ]
        for m in expected_metrics:
            if m not in metrics:
                metrics[m] = 0.0
    except Exception as e:
        print(f"Error generating metrics: {e}")
        metrics = {
            "Communication skills": 0.0, "Teamwork and collaboration": 0.0,
            "Problem-solving and critical thinking": 0.0, "Time management and organization": 0.0,
            "Adaptability and resilience": 0.0
        }
    return metrics

# --- Evaluation Logic (Adapted from login_module/evaluate.py) ---

def getmetrics(interaction, resume):
    interaction_text = "\n".join([f"{q}: {a}" for q, a in interaction.items()])
    text = f"""This is the user's resume: {resume}.
    And here is the interaction of the interview: {interaction_text}.
    Please evaluate the interview based on the interaction and the resume.
    Rate me the following metrics on a scale of 1 to 10. 1 being the lowest and 10 being the highest.
    Communication skills, Teamwork and collaboration, Problem-solving and critical thinking,
    Time management and organization, Adaptability and resilience. Just give the ratings for the metrics.
    I do not need the feedback. Just the ratings in the format:
    Communication skills: X
    Teamwork and collaboration: Y
    Problem-solving and critical thinking: Z
    Time management and organization: A
    Adaptability and resilience: B
    """
    try:
        # Use the correct model instance
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error fetching metrics from AI: {e}")
        return ""

def parse_metrics(metric_text):
    metrics = {
        "Communication skills": 0,
        "Teamwork and collaboration": 0,
        "Problem-solving and critical thinking": 0,
        "Time management and organization": 0,
        "Adaptability and resilience": 0
    }
    if not metric_text:
        return metrics
    for line in metric_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value and value not in ['N/A', 'nan'] and not value.isspace():
                try:
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        metrics[key] = int(float(numbers[0]))
                    else:
                        metrics[key] = 0
                except (ValueError, IndexError, TypeError):
                    print(f"Warning: Could not parse metric value '{value}' for '{key}'. Setting to 0.")
                    metrics[key] = 0
            else:
                metrics[key] = 0
    return metrics

def create_metrics_chart(metrics_dict):
    try:
        labels = list(metrics_dict.keys())
        sizes = list(metrics_dict.values())
        if not any(sizes):
             fig, ax = plt.subplots(figsize=(4, 4))
             ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
             ax.axis('off')
        else:
            fig, ax = plt.subplots(figsize=(6, 6))
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        print(f"Error creating chart: {e}")
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.text(0.5, 0.5, 'Chart Error', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf

def generate_evaluation_report(metrics_data, average_rating, feedback_list, interaction_dict):
    try:
        report_lines = [f"## Hey Candidate, here is your interview evaluation:\n"]
        report_lines.append("### Skill Ratings:\n")
        for metric, rating in metrics_data.items():
            report_lines.append(f"* **{metric}:** {rating}/10\n")
        report_lines.append(f"\n### Overall Average Rating: {average_rating:.2f}/10\n")
        report_lines.append("### Feedback Summary:\n")
        if feedback_list:
            last_feedback = feedback_list[-1] if feedback_list else "No feedback available."
            report_lines.append(last_feedback)
        else:
             report_lines.append("No detailed feedback was generated.")
        report_lines.append("\n### Interview Interaction:\n")
        if interaction_dict:
            for q, a in interaction_dict.items():
                report_lines.append(f"* **{q}**\n  {a}\n")
        else:
             report_lines.append("Interaction data not available.")
        improvement_content = """
### Areas for Improvement:
*   **Communication:** Focus on clarity, conciseness, and tailoring your responses to the audience. Use examples and evidence to support your points.
*   **Teamwork and collaboration:** Highlight your teamwork skills through specific examples and demonstrate your ability to work effectively with others.
*   **Problem-solving and critical thinking:** Clearly explain your problem-solving approach and thought process. Show your ability to analyze information and arrive at logical solutions.
*   **Time management and organization:** Emphasize your ability to manage time effectively and stay organized during challenging situations.
*   **Adaptability and resilience:** Demonstrate your ability to adapt to new situations and overcome challenges. Share examples of how you have handled unexpected situations or setbacks in the past.
**Remember:** This is just a starting point. Customize the feedback based on the specific strengths and weaknesses identified in your interview.
"""
        report_lines.append(improvement_content)
        report_text = "".join(report_lines)
        return report_text
    except Exception as e:
        error_msg = f"Error generating evaluation report: {e}"
        print(error_msg)
        return error_msg

# --- Gradio UI Components and Logic (Interview) ---


def process_resume(file_obj):
    """Handles resume upload and processing."""
    print(f"process_resume called with: {file_obj}") # Debug print
    if not file_obj:
        # Return exactly 13 values to match the outputs list
        # [file_status_interview, role_selection, start_interview_btn,
        #  question_display, answer_instructions, audio_input,
        #  submit_answer_btn, next_question_btn, submit_interview_btn,
        #  answer_display, feedback_display, metrics_display,
        #  processed_resume_data_hidden_interview]
        print("No file uploaded.")
        return (
            "Please upload a PDF resume.",  # file_status_interview
            gr.update(visible=False),       # role_selection
            gr.update(visible=False),       # start_interview_btn
            gr.update(visible=False),       # question_display
            gr.update(visible=False),       # answer_instructions
            gr.update(visible=False),       # audio_input
            gr.update(visible=False),       # submit_answer_btn
            gr.update(visible=False),       # next_question_btn
            gr.update(visible=False),       # submit_interview_btn
            gr.update(visible=False),       # answer_display
            gr.update(visible=False),       # feedback_display
            gr.update(visible=False),       # metrics_display
            gr.update(visible=False)        # processed_resume_data_hidden_interview
            # Total: 13 values
        )

    try:
        # --- Correctly handle the file path from Gradio ---
        if hasattr(file_obj, 'name'):
            file_path = file_obj.name
        else:
            # Fallback if it's somehow a direct path string (less likely)
            file_path = str(file_obj)
        print(f"File path to process: {file_path}")

        # --- Process the PDF ---
        raw_text = file_processing(file_path) # Use the path
        print(f"Raw text extracted (length: {len(raw_text) if raw_text else 0})")
        if not raw_text or not raw_text.strip():
             print("Failed to extract text or text is empty.")
             return (
                "Could not extract text from the PDF.", # file_status_interview
                gr.update(visible=False), gr.update(visible=False), # role_selection, start_interview_btn
                gr.update(visible=False), gr.update(visible=False), # question_display, answer_instructions
                gr.update(visible=False), gr.update(visible=False), # audio_input, submit_answer_btn
                gr.update(visible=False), gr.update(visible=False), # next_question_btn, submit_interview_btn
                gr.update(visible=False), gr.update(visible=False), # answer_display, feedback_display
                gr.update(visible=False), gr.update(visible=False)  # metrics_display, processed_resume_data_hidden_interview
                # Total: 13 values
             )

        # --- Format the resume data ---
        processed_data = getallinfo(raw_text) # Use the new model instance if corrected
        print(f"Resume processed (length: {len(processed_data) if processed_data else 0})")

        # --- Return success state and values ---
        # Make sure to return the processed_data as the LAST value
        return (
            f"File processed successfully!", # file_status_interview
            gr.update(visible=True),         # role_selection (make visible)
            gr.update(visible=True),         # start_interview_btn (make visible)
            gr.update(visible=False),        # question_display (initially hidden)
            gr.update(visible=False),        # answer_instructions (initially hidden)
            gr.update(visible=False),        # audio_input (initially hidden)
            gr.update(visible=False),        # submit_answer_btn (initially hidden)
            gr.update(visible=False),        # next_question_btn (initially hidden)
            gr.update(visible=False),        # submit_interview_btn (initially hidden)
            gr.update(visible=False),        # answer_display (initially hidden)
            gr.update(visible=False),        # feedback_display (initially hidden)
            gr.update(visible=False),        # metrics_display (initially hidden)
            processed_data                   # processed_resume_data_hidden_interview (pass the data!)
            # Total: 13 values
        )
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(f"Exception in process_resume: {error_msg}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        # Ensure exactly 13 values are returned even on error
        return (
            error_msg,                      # file_status_interview
            gr.update(visible=False), gr.update(visible=False), # role_selection, start_interview_btn
            gr.update(visible=False), gr.update(visible=False), # question_display, answer_instructions
            gr.update(visible=False), gr.update(visible=False), # audio_input, submit_answer_btn
            gr.update(visible=False), gr.update(visible=False), # next_question_btn, submit_interview_btn
            gr.update(visible=False), gr.update(visible=False), # answer_display, feedback_display
            gr.update(visible=False), gr.update(visible=False)  # metrics_display, processed_resume_data_hidden_interview
            # Total: 13 values
        )


def start_interview(roles, processed_resume_data):
    """Starts the interview process."""
    if not roles or (isinstance(roles, list) and not any(roles)) or not processed_resume_data or not processed_resume_data.strip():
        # Return exactly 11 values matching the outputs list
        return (
            "Please select a role and ensure resume is processed.",
            "", # initial question
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Audio, Submit, Next
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Submit Int, Feedback, Metrics
            gr.update(visible=False), gr.update(visible=False), # Q Display, A Instructions
            {} # interview_state
            # 11 values total
        )

    try:
        questions = generate_questions(roles, processed_resume_data)
        initial_question = questions[0] if questions else "Could you please introduce yourself?"
        interview_state = {
            "questions": questions,
            "current_q_index": 0,
            "answers": [],
            "feedback": [],
            "interactions": {},
            "metrics_list": [],
            "resume_data": processed_resume_data
        }
        # Return exactly 11 values
        return (
            "Interview started. Please answer the first question.",
            initial_question,
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Submit Int, Feedback, Metrics
            gr.update(visible=True), gr.update(visible=True), # Q Display, A Instructions
            interview_state
            # 11 values total
        )
    except Exception as e:
        error_msg = f"Error starting interview: {str(e)}"
        print(error_msg)
        # Return exactly 11 values on error
        return (
            error_msg,
            "", # initial question
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False),
            {} # interview_state
            # 11 values total
        )

def submit_answer(audio, interview_state):
    """Handles submitting an answer via audio."""
    if not audio or not interview_state:
        # Return values matching the outputs list, ensuring audio is handled correctly
        # If audio is invalid, return None or gr.update() for the audio component
        return (
            "No audio recorded or interview not started.",
            "", # answer_text
            interview_state, # state
            gr.update(visible=False), gr.update(visible=False), # Feedback display/value
            gr.update(visible=False), gr.update(visible=False), # Metrics display/value
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next (keep visible for retry)
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=True) # Submit Int (hide), Q Display, A Instructions
            # 13 values total (matching outputs list)
        )

    try:
        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, "recorded_audio.wav")
        sample_rate, audio_data = audio
        sf.write(audio_file_path, audio_data, sample_rate)

        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data_sr = r.record(source)
        answer_text = r.recognize_google(audio_data_sr)
        print(f"Recognized Answer: {answer_text}")

        os.remove(audio_file_path)
        os.rmdir(temp_dir)

        interview_state["answers"].append(answer_text)
        current_q_index = interview_state["current_q_index"]
        current_question = interview_state["questions"][current_q_index]
        interview_state["interactions"][f"Q{current_q_index + 1}: {current_question}"] = f"A{current_q_index + 1}: {answer_text}"

        percent_str = generate_feedback(current_question, answer_text)
        try:
            percent = float(percent_str)
        except ValueError:
            percent = 0.0

        feedback_text = generate_overall_feedback(interview_state["resume_data"], percent_str, answer_text, current_question)
        interview_state["feedback"].append(feedback_text)

        metrics = generate_metrics(interview_state["resume_data"], answer_text, current_question)
        interview_state["metrics_list"].append(metrics)

        interview_state["current_q_index"] += 1

        # Return values matching the outputs list
        return (
            f"Answer submitted: {answer_text}",
            answer_text,
            interview_state,
            gr.update(visible=True), gr.update(value=feedback_text, visible=True), # Feedback
            gr.update(visible=True), gr.update(value=metrics, visible=True), # Metrics
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=True) # Submit Int, Q Display, A Instructions
            # 13 values total
        )

    except Exception as e:
        print(f"Error processing audio answer: {e}")
        # Return values matching the outputs list, handling error
        return (
            "Error processing audio. Please try again.",
            "", # answer_text
            interview_state, # state (pass through)
            gr.update(visible=False), gr.update(visible=False), # Feedback
            gr.update(visible=False), gr.update(visible=False), # Metrics
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next (keep for retry)
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=True) # Submit Int, Q Display, A Instructions
            # 13 values total
        )

def next_question(interview_state):
    """Moves to the next question or ends the interview."""
    if not interview_state:
        # Return values matching outputs list
        return (
            "Interview not started.",
            "", # next_q
            interview_state, # state
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Feedback, Metrics, Submit Int
            gr.update(visible=False), gr.update(visible=False), # Q Display, A Instructions
            "", {} # Clear answer/metrics display
            # 13 values total
        )

    current_q_index = interview_state["current_q_index"]
    total_questions = len(interview_state["questions"])

    if current_q_index < total_questions:
        next_q = interview_state["questions"][current_q_index]
        # Return values for next question
        return (
            f"Question {current_q_index + 1}/{total_questions}",
            next_q,
            interview_state,
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), # Audio, Submit, Next
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Feedback, Metrics, Submit Int
            gr.update(visible=True), gr.update(visible=True), # Q Display, A Instructions
            "", {} # Clear previous answer/metrics display
            # 13 values total
        )
    else:
        # Interview finished
        return (
            "Interview completed! Click 'Submit Interview' to see your evaluation.",
            "Interview Finished",
            interview_state,
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Audio, Submit, Next (hide)
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), # Feedback, Metrics, Submit Int (hide feedback/metrics)
            gr.update(visible=True), gr.update(visible=False), # Q Display (show finished), A Instructions (hide)
            "", {} # Clear answer/metrics display
            # 13 values total
            # Ensure submit_interview_btn is made visible here or in the event listener logic if needed immediately
        )

def submit_interview(interview_state):
    """Handles final submission, triggers evaluation, and prepares results."""
    if not interview_state or not isinstance(interview_state, dict):
        # Return values matching outputs list for submit_interview_btn.click
        return (
            "Interview state is missing or invalid.",
            interview_state, # state (pass through)
            gr.update(visible=False), gr.update(visible=False), # Report, Chart (hide)
            "", None # Report text, Chart image (clear)
            # 5 values total (matching submit_interview_btn.click outputs)
        )

    try:
        print("Interview submitted for evaluation.")
        interactions = interview_state.get("interactions", {})
        resume_data = interview_state.get("resume_data", "")
        feedback_list = interview_state.get("feedback", [])
        metrics_history = interview_state.get("metrics_list", [])

        if not interactions:
            error_msg = "No interview interactions found to evaluate."
            print(error_msg)
            # Return values matching outputs list
            return (
                error_msg,
                interview_state,
                gr.update(visible=False), gr.update(visible=False), # Report, Chart (hide)
                "", None # Report text, Chart image (clear)
                # 5 values total
            )

        raw_metrics_text = getmetrics(interactions, resume_data)
        print(f"Raw Metrics Text:\n{raw_metrics_text}")
        final_metrics = parse_metrics(raw_metrics_text)
        print(f"Parsed Metrics: {final_metrics}")

        if final_metrics:
            average_rating = sum(final_metrics.values()) / len(final_metrics)
        else:
            average_rating = 0.0

        report_text = generate_evaluation_report(final_metrics, average_rating, feedback_list, interactions)
        print("Evaluation report generated.")
        chart_buffer = create_metrics_chart(final_metrics)
        print("Evaluation chart generated.")

        # Return values matching outputs list
        return (
            "Evaluation Complete! See your results below.",
            interview_state, # state (pass through, though not changed)
            gr.update(visible=True, value=report_text), # Show and update report
            gr.update(visible=True, value=chart_buffer)  # Show and update chart
            # 4 values total (Note: outputs list had 4 items, but function returns 4, so it should be fine)
            # Actually, checking the listener again:
            # outputs=[file_status_interview, interview_state, evaluation_report_display, evaluation_chart_display]
            # So, 4 outputs, 4 returns. Correct.
        )
    except Exception as e:
        error_msg = f"Error during evaluation submission: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        # Return values matching outputs list on error
        return (
            error_msg,
            interview_state, # state (pass through)
            gr.update(visible=True, value=error_msg), # Show error in report area
            gr.update(visible=False) # Hide chart
            # 4 values total
        )

# --- Login and Navigation Logic (Firebase Integrated) ---

def login(email, password): # Correct arguments: email, password
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE:
        # Return exactly 8 values matching the outputs list for login_btn.click
        return (
            "Firebase not initialized. Login unavailable.",
            gr.update(visible=True),   # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            "",                        # login_email_input (clear)
            "",                        # login_password_input (clear)
            "",                        # user_state
            ""                         # user_email_state
        )

    # --- CORRECTION 1: Remove 'username' from the condition check ---
    # The login function does not have a 'username' argument.
    if not email or not password: # <-- Corrected line
        # Return exactly 8 values for this case too
        return (
            "Please enter email and password.",
            gr.update(visible=True),   # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            email,                     # login_email_input (keep value)
            password,                  # login_password_input (keep value)
            "",                        # user_state
            ""                         # user_email_state
        )

    try:
        user = auth.get_user_by_email(email)
        welcome_msg = f"Welcome, {user.display_name or user.uid}!"
        return (
            welcome_msg,
            gr.update(visible=False),  # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=True),   # main_app
            "",                        # login_email_input (clear on success)
            "",                        # login_password_input (clear on success)
            user.uid,                  # user_state
            user.email                 # user_email_state
        )
    except auth.UserNotFoundError:
        return (
            "User not found. Please check your email or sign up.",
            gr.update(visible=True),   # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            email,                     # login_email_input (keep value)
            password,                  # login_password_input (keep value)
            "",                        # user_state
            ""                         # user_email_state
        )
    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        print(error_msg)
        return (
            error_msg,
            gr.update(visible=True),   # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            email,                     # login_email_input (keep value)
            password,                  # login_password_input (keep value)
            "",                        # user_state
            ""                         # user_email_state
        )


def signup(email, password, username): # Correct arguments: email, password, username
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE:
        # Return exactly 9 values matching the outputs list for signup_btn.click
        # --- CORRECTION 2a: Ensure the number of returned values matches the expected 9 ---
        return (
            "Firebase not initialized. Signup unavailable.",
            gr.update(visible=True),   # login_section
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            # --- CORRECTION 2b: Remove the extra placeholder gr.update() ---
            # gr.update(visible=False),  # Placeholder/adjust (This was the 5th item causing the mismatch)
            "",                        # signup_email_input (5th)
            "",                        # signup_password_input (6th)
            "",                        # signup_username_input (7th)
            "",                        # user_state (8th)
            ""                         # user_email_state (9th)
            # 9 values total
        )

    # --- CORRECTION 3: The 'username' check is valid here ---
    if not email or not password or not username: # <-- This line is correct for signup
        # Return exactly 9 values for this case too
        return (
            "Please fill all fields.",
            gr.update(visible=False),  # login_section
            gr.update(visible=True),   # signup_section
            gr.update(visible=False),  # main_app
            # gr.update(visible=False),  # Placeholder/adjust (Remove this)
            email,                     # signup_email_input (5th)
            password,                  # signup_password_input (6th)
            username,                  # signup_username_input (7th)
            "",                        # user_state (8th)
            ""                         # user_email_state (9th)
            # 9 values total
        )

    try:
        user = auth.create_user(email=email, password=password, uid=username, display_name=username)
        success_msg = f"Account created successfully for {username}!"
        # Switch to login view after successful signup
        return (
            success_msg,
            gr.update(visible=True),   # login_section (switch to login)
            gr.update(visible=False),  # signup_section
            gr.update(visible=False),  # main_app
            # gr.update(visible=False),  # Placeholder/adjust (Remove this)
            "", "", "",                # Clear email/password/username inputs (5th, 6th, 7th)
            user.uid, user.email       # Set user state (8th, 9th)
            # 9 values total
        )
    except auth.UidAlreadyExistsError:
        return (
            "Username already exists. Please choose another.",
            gr.update(visible=False),  # login_section
            gr.update(visible=True),   # signup_section
            gr.update(visible=False),  # main_app
            # gr.update(visible=False),  # Placeholder/adjust (Remove this)
            email, password, username, # Keep inputs (5th, 6th, 7th)
            "", ""                     # Clear user state (8th, 9th)
            # 9 values total
        )
    except auth.EmailAlreadyExistsError:
        return (
            "Email already exists. Please use another email.",
            gr.update(visible=False),  # login_section
            gr.update(visible=True),   # signup_section
            gr.update(visible=False),  # main_app
            # gr.update(visible=False),  # Placeholder/adjust (Remove this)
            email, password, username, # Keep inputs (5th, 6th, 7th)
            "", ""                     # Clear user state (8th, 9th)
            # 9 values total
        )
    except Exception as e:
        error_msg = f"Signup failed: {str(e)}"
        print(error_msg)
        return (
            error_msg,
            gr.update(visible=False),  # login_section
            gr.update(visible=True),   # signup_section
            gr.update(visible=False),  # main_app
            # gr.update(visible=False),  # Placeholder/adjust (Remove this)
            email, password, username, # Keep inputs (5th, 6th, 7th)
            "", ""                     # Clear user state (8th, 9th)
            # 9 values total
        )


def logout():
    # Return exactly 9 values matching the outputs list for logout_btn.click
    return (
        "",                         # Clear login status
        gr.update(visible=True),   # Show login section
        gr.update(visible=False),  # Hide signup section
        gr.update(visible=False),  # Hide main app
        # gr.update(visible=False),  # Placeholder/adjust (Remove this if present in your listener)
        "", "", "",                # Clear email/password/username inputs
        "", ""                     # Clear user_state and user_email_state
        # 9 values total
    )


def navigate_to_interview():
    return (gr.update(visible=True), gr.update(visible=False))

def navigate_to_chat():
    return (gr.update(visible=False), gr.update(visible=True))

# --- Import Chat Module Functions ---
try:
    from login_module import chat as chat_module
    CHAT_MODULE_AVAILABLE = True
    print("Chat module imported successfully.")
except ImportError as e:
    print(f"Warning: Could not import chat module: {e}")
    CHAT_MODULE_AVAILABLE = False
    chat_module = None

# --- Gradio Interface ---
with gr.Blocks(title="PrepGenie - Mock Interview") as demo:
    gr.Markdown("# 🦈 PrepGenie")
    interview_state = gr.State({})
    user_state = gr.State("")
    user_email_state = gr.State("")
    processed_resume_data_state = gr.State("")

    # --- Login Section ---
    with gr.Column(visible=True) as login_section:
        gr.Markdown("## Login")
        login_email_input = gr.Textbox(label="Email Address")
        login_password_input = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status", interactive=False)
        switch_to_signup_btn = gr.Button("Don't have an account? Sign Up")

    # --- Signup Section ---
    with gr.Column(visible=False) as signup_section:
        gr.Markdown("## Sign Up")
        signup_email_input = gr.Textbox(label="Email Address")
        signup_password_input = gr.Textbox(label="Password", type="password")
        signup_username_input = gr.Textbox(label="Unique Username")
        signup_btn = gr.Button("Create my account")
        signup_status = gr.Textbox(label="Signup Status", interactive=False)
        switch_to_login_btn = gr.Button("Already have an account? Login")

    # --- Main App Sections ---
    with gr.Column(visible=False) as main_app:
        with gr.Row():
            with gr.Column(scale=1):
                 logout_btn = gr.Button("Logout")
            with gr.Column(scale=4):
                welcome_display = gr.Markdown("### Welcome, User!")

        with gr.Row():
            with gr.Column(scale=1):
                interview_btn = gr.Button("Mock Interview")
                if CHAT_MODULE_AVAILABLE:
                    chat_btn = gr.Button("Chat with Resume")
                else:
                    chat_btn = gr.Button("Chat with Resume (Unavailable)", interactive=False)
            with gr.Column(scale=4):
                # --- Interview Section ---
                with gr.Column(visible=False) as interview_selection:
                    gr.Markdown("## Mock Interview")
                    with gr.Row():
                        with gr.Column():
                            file_upload_interview = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
                            process_btn_interview = gr.Button("Process Resume")
                        with gr.Column():
                            file_status_interview = gr.Textbox(label="Status", interactive=False)

                    role_selection = gr.Dropdown(
                        choices=["Data Scientist", "Software Engineer", "Product Manager", "Data Analyst", "Business Analyst"],
                        multiselect=True, label="Select Job Role(s)", visible=False
                    )
                    start_interview_btn = gr.Button("Start Interview", visible=False)
                    question_display = gr.Textbox(label="Question", interactive=False, visible=False)
                    answer_instructions = gr.Markdown("Click 'Record Answer' and speak your response.", visible=False)
                    audio_input = gr.Audio(label="Record Answer", type="numpy", visible=False)
                    submit_answer_btn = gr.Button("Submit Answer", visible=False)
                    next_question_btn = gr.Button("Next Question", visible=False)
                    submit_interview_btn = gr.Button("Submit Interview", visible=False, variant="primary")
                    answer_display = gr.Textbox(label="Your Answer", interactive=False, visible=False)
                    feedback_display = gr.Textbox(label="Feedback", interactive=False, visible=False)
                    metrics_display = gr.JSON(label="Metrics", visible=False)
                    processed_resume_data_hidden_interview = gr.Textbox(visible=False)

                    # --- Evaluation Results Section ---
                    with gr.Column(visible=False) as evaluation_selection:
                        gr.Markdown("## Interview Evaluation Results")
                        evaluation_report_display = gr.Markdown(label="Your Evaluation Report", visible=False)
                        evaluation_chart_display = gr.Image(label="Skills Breakdown", type="pil", visible=False)

                # --- Chat Section ---
                if CHAT_MODULE_AVAILABLE:
                    with gr.Column(visible=False) as chat_selection:
                        gr.Markdown("## Chat with Resume")
                        with gr.Row():
                            with gr.Column():
                                file_upload_chat = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
                                process_chat_btn = gr.Button("Process Resume")
                            with gr.Column():
                                file_status_chat = gr.Textbox(label="Status", interactive=False)
                        chatbot = gr.Chatbot(label="Chat History", visible=False, type="messages")
                        query_input = gr.Textbox(label="Ask about your resume", placeholder="Type your question here...", visible=False)
                        send_btn = gr.Button("Send", visible=False)
                else:
                    with gr.Column(visible=False) as chat_selection:
                        gr.Markdown("## Chat with Resume (Unavailable)")
                        gr.Textbox(value="Chat module is not available.", interactive=False)

        interview_view = interview_selection
        chat_view = chat_selection
        interview_btn.click(fn=navigate_to_interview, inputs=None, outputs=[interview_view, chat_view])
        if CHAT_MODULE_AVAILABLE:
            chat_btn.click(fn=navigate_to_chat, inputs=None, outputs=[interview_view, chat_view])

    # --- Event Listeners for Interview ---
    process_btn_interview.click(
        fn=process_resume,
        inputs=[file_upload_interview],
        outputs=[
            file_status_interview, role_selection, start_interview_btn,
            question_display, answer_instructions, audio_input,
            submit_answer_btn, next_question_btn, submit_interview_btn,
            answer_display, feedback_display, metrics_display,
            processed_resume_data_hidden_interview # 13 outputs
        ]
    )

    start_interview_btn.click(
        fn=start_interview,
        inputs=[role_selection, processed_resume_data_hidden_interview],
        outputs=[
            file_status_interview, question_display,
            # interview_state["questions"], interview_state["answers"], # REMOVED - Invalid
            # interview_state["interactions"], interview_state["metrics_list"], # REMOVED - Invalid
            # Outputs for UI updates
            audio_input, submit_answer_btn, next_question_btn,
            submit_interview_btn, feedback_display, metrics_display,
            question_display, answer_instructions,
            interview_state # Update the state object itself (11 outputs)
        ]
    )

    submit_answer_btn.click(
        fn=submit_answer,
        inputs=[audio_input, interview_state],
        outputs=[
            file_status_interview, answer_display, interview_state,
            feedback_display, feedback_display, # Update value and visibility
            metrics_display, metrics_display,   # Update value and visibility
            audio_input, submit_answer_btn, next_question_btn, # 13 outputs
            submit_interview_btn, question_display, answer_instructions
        ]
    )

    next_question_btn.click(
        fn=next_question,
        inputs=[interview_state],
        outputs=[
            file_status_interview, question_display, interview_state,
            audio_input, submit_answer_btn, next_question_btn,
            feedback_display, metrics_display, submit_interview_btn,
            question_display, answer_instructions,
            answer_display, metrics_display # Clear previous answer/metrics display (13 outputs)
        ]
    )

    submit_interview_btn.click(
        fn=submit_interview,
        inputs=[interview_state],
        outputs=[
            file_status_interview, # Status message
            interview_state,       # State (passed through)
            evaluation_report_display, # Show report
            evaluation_chart_display   # Show chart (4 outputs)
        ]
    )

    # --- Event Listeners for Chat ---
    if CHAT_MODULE_AVAILABLE:
        process_chat_btn.click(
            fn=chat_module.process_resume_chat,
            inputs=[file_upload_chat],
            outputs=[file_status_chat, processed_resume_data_state, query_input, send_btn, chatbot]
        )
        send_btn.click(
            fn=chat_module.chat_with_resume,
            inputs=[query_input, processed_resume_data_state, chatbot],
            outputs=[query_input, chatbot]
        )
        query_input.submit(
            fn=chat_module.chat_with_resume,
            inputs=[query_input, processed_resume_data_state, chatbot],
            outputs=[query_input, chatbot]
        )

    # --- Login/Logout Event Listeners ---

    login_btn.click(
        fn=login,
        inputs=[login_email_input, login_password_input],
        outputs=[login_status, login_section, signup_section, main_app,
                 login_email_input, login_password_input, user_state, user_email_state] # 8 outputs
    )
    
    signup_btn.click(
        fn=signup,
        inputs=[signup_email_input, signup_password_input, signup_username_input],
        outputs=[signup_status, login_section, signup_section, main_app,
                 # Remove any extra gr.update() from the outputs list if present
                 signup_email_input, signup_password_input, signup_username_input,
                 user_state, user_email_state] # 9 outputs
    )
    
    logout_btn.click(
        fn=logout,
        inputs=None,
        outputs=[login_status, login_section, signup_section, main_app,
                 # Remove any extra gr.update() from the outputs list if present
                 login_email_input, login_password_input, signup_username_input, # Note: uses signup_username_input target
                 user_state, user_email_state] # 9 outputs
    )



    switch_to_signup_btn.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[login_section, signup_section]
    )

    switch_to_login_btn.click(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
        inputs=None,
        outputs=[login_section, signup_section]
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
