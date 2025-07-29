# PrepGenie/app.py
import gradio as gr
import os
import tempfile
import PyPDF2
import google.generativeai as genai
# import tensorflow as tf # Not directly used here, but models might need it
from transformers import BertTokenizer, TFBertModel
import numpy as np
import speech_recognition as sr
import time
from dotenv import load_dotenv
import soundfile as sf # For saving audio numpy array
import json

# --- Firebase Admin SDK Setup ---
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK (Use environment variable for credentials path or default)
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "prepgenie-64134-firebase-adminsdk-fbsvc-3370ac4ab9.json")
if not firebase_admin._apps:
    try:
        # Try loading from file path first
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully using credentials file.")
    except FileNotFoundError:
        print(f"Firebase credentials file not found at {firebase_credentials_path}. Trying environment variable...")
        try:
            # Fallback: Try loading from environment variable (expects JSON string)
            firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
            if firebase_credentials_json:
                cred_dict = json.loads(firebase_credentials_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin initialized successfully using environment variable.")
            else:
                raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable not set.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error initializing Firebase Admin: {e}")
            print("Firebase authentication will not be available.")
            # You might want to handle this case differently, e.g., disable features or show an error
    except Exception as e:
        print(f"Unexpected error initializing Firebase Admin: {e}")
        print("Firebase authentication will not be available.")

# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or "YOUR_DEFAULT_API_KEY_HERE") # Use environment variable or set a default
text_model = genai.GenerativeModel("gemini-pro")

# Load BERT model and tokenizer (Consider lazy loading if performance is an issue)
try:
    model = TFBertModel.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    BERT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load BERT model/tokenizer: {e}")
    BERT_AVAILABLE = False
    model = None
    tokenizer = None

# --- Helper Functions (Logic from Streamlit - Interview) ---

def getallinfo(data):
    if not data or not data.strip(): # Check for None or empty/whitespace
        return "No data provided or data is empty."
    text = f"""{data} is given by the user. Make sure you are getting the details like name, experience,
            education, skills of the user like in a resume. If the details are not provided return: not a resume.
            If details are provided then please try again and format the whole in a single paragraph covering all the information. """
    try:
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error in getallinfo: {e}")
        return "Error processing resume data."

def file_processing(pdf_file_path): # Takes file path now
    if not pdf_file_path:
        return ""
    try:
        with open(pdf_file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return ""

def get_embedding(text):
    if not text or not text.strip():
         print("Empty text provided for embedding.")
         return np.zeros((1, 768)) # Return dummy embedding for empty text

    if not BERT_AVAILABLE or not model or not tokenizer:
        print("BERT model not available for embedding.")
        # Return a dummy embedding or handle the error appropriately
        return np.zeros((1, 768)) # Dummy embedding size for bert-base-uncased

    try:
        # Add padding/truncation to handle variable lengths robustly
        encoded_text = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        output = model(encoded_text)
        embedding = output.last_hidden_state[:, 0, :] # CLS token embedding
        return embedding.numpy() # Convert to numpy for easier handling
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return np.zeros((1, 768)) # Return dummy embedding on error

def generate_feedback(question, answer):
    # Handle empty inputs
    if not question or not question.strip() or not answer or not answer.strip():
        return "0.00"

    try:
        question_embedding = get_embedding(question)
        answer_embedding = get_embedding(answer)
        # Calculate cosine similarity (ensure correct shapes)
        # np.dot expects 1D or 2D arrays. Squeeze to remove single-dimensional entries.
        q_emb = np.squeeze(question_embedding)
        a_emb = np.squeeze(answer_embedding)

        dot_product = np.dot(q_emb, a_emb)
        norms = np.linalg.norm(q_emb) * np.linalg.norm(a_emb)
        if norms == 0:
            similarity_score = 0.0
        else:
            similarity_score = dot_product / norms
        return f"{similarity_score:.2f}" # Format as string with 2 decimal places
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "0.00"

def generate_questions(roles, data):
    # Handle empty inputs
    if not roles or (isinstance(roles, list) and not any(roles)) or not data or not data.strip():
        return ["Could you please introduce yourself based on your resume?"]

    questions = []
    # Ensure roles is a list and join if needed
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
            Problem-solving and critical thinking, Time management and organization, Adaptability and resilience. dont
            tell anything else just give me the questions. if there is a limit in no of questions, ask or try questions that covers
            all need."""
    try:
        response = text_model.generate_content(text)
        response.resolve()
        questions_text = response.text.strip()
        # Split by newline, question mark, or period. Filter out empty strings.
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        if not questions:
             questions = [q.strip() for q in questions_text.split('?') if q.strip()]
        if not questions:
             questions = [q.strip() for q in questions_text.split('.') if q.strip()]
        # Ensure we only get up to 2 questions
        questions = questions[:2] if questions else ["Could you please introduce yourself based on your resume?"]
    except Exception as e:
        print(f"Error generating questions: {e}")
        questions = ["Could you please introduce yourself based on your resume?"]
    return questions

def generate_overall_feedback(data, percent, answer, questions):
    # Handle empty inputs
    if not data or not data.strip() or not answer or not answer.strip() or not questions:
        return "Unable to generate feedback due to missing information."

    # Ensure percent is a string for formatting, handle potential float input
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
        response = text_model.generate_content(prompt)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error generating overall feedback: {e}")
        return "Feedback could not be generated."

def generate_metrics(data, answer, question):
    # Handle empty inputs
    if not data or not data.strip() or not answer or not answer.strip() or not question or not question.strip():
        # Return default 0 metrics for empty inputs
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
        response = text_model.generate_content(text)
        response.resolve()
        metrics_text = response.text.strip()
        # Parse the metrics text
        for line in metrics_text.split('\n'):
            if ':' in line:
                key, value_str = line.split(':', 1)
                key = key.strip()
                try:
                    # Handle potential extra characters after the number
                    value_clean = value_str.strip().split()[0] # Take first token
                    value = float(value_clean)
                    metrics[key] = value
                except (ValueError, IndexError):
                    # If parsing fails, set to 0
                    metrics[key] = 0.0
        # Ensure all expected metrics are present
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
        # Return default 0 metrics on error
        metrics = {
            "Communication skills": 0.0, "Teamwork and collaboration": 0.0,
            "Problem-solving and critical thinking": 0.0, "Time management and organization": 0.0,
            "Adaptability and resilience": 0.0
        }
    return metrics

# --- Gradio UI Components and Logic (Interview) ---

def process_resume(file_obj):
    """Handles resume upload and processing."""
    if not file_obj:
        return ("Please upload a PDF resume.", gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False))

    try:
        # Save uploaded file to a temporary location
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_obj.name)
        with open(file_path, "wb") as f:
            f.write(file_obj.read())

        # Process the PDF
        raw_text = file_processing(file_path)
        if not raw_text or not raw_text.strip():
             os.remove(file_path)
             os.rmdir(temp_dir)
             return ("Could not extract text from the PDF.", gr.update(visible=False), gr.update(visible=False),
                     gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                     gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                     gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                     gr.update(visible=False), gr.update(visible=False))

        processed_data = getallinfo(raw_text)

        # Clean up temporary file
        os.remove(file_path)
        os.rmdir(temp_dir)

        return (
            f"File processed successfully!",
            gr.update(visible=True),  # Role selection dropdown
            gr.update(visible=True),  # Start Interview button
            gr.update(visible=False), # Question display (initially)
            gr.update(visible=False), # Answer instructions (initially)
            gr.update(visible=False), # Audio input (initially)
            gr.update(visible=False), # Submit Answer button (initially)
            gr.update(visible=False), # Next Question button (initially)
            gr.update(visible=False), # Submit Interview button (initially)
            gr.update(visible=False), # Answer display (initially)
            gr.update(visible=False), # Feedback display (initially)
            gr.update(visible=False), # Metrics display (initially)
            gr.update(visible=False), # Processed resume data textbox (hidden)
            processed_data # Pass processed data for next step
        )
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(error_msg)
        return (error_msg, gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False))

def start_interview(roles, processed_resume_data):
    """Starts the interview process."""
    # Corrected the condition check
    if not roles or (isinstance(roles, list) and not any(roles)) or not processed_resume_data or not processed_resume_data.strip():
        return ("Please select a role and ensure resume is processed.", "", [], [], {}, {},
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), {}) # Return empty state on error

    try:
        questions = generate_questions(roles, processed_resume_data)
        initial_question = questions[0] if questions else "Could you please introduce yourself?"

        # Initialize state for the interview
        interview_state = {
            "questions": questions,
            "current_q_index": 0,
            "answers": [],
            "feedback": [],
            "interactions": {},
            "metrics_list": [], # List to store metrics for each question
            "resume_data": processed_resume_data
        }

        return (
            "Interview started. Please answer the first question.",
            initial_question,
            questions,
            [], # answers
            {}, # interactions
            {}, # metrics (initially empty)
            gr.update(visible=True), # Audio input
            gr.update(visible=True), # Submit Answer button
            gr.update(visible=True), # Next Question button
            gr.update(visible=False), # Submit Interview button (hidden initially)
            gr.update(visible=False), # Feedback textbox
            gr.update(visible=False), # Metrics display
            gr.update(visible=True), # Question display
            gr.update(visible=True), # Answer instructions
            interview_state
        )
    except Exception as e:
        error_msg = f"Error starting interview: {str(e)}"
        print(error_msg)
        return (error_msg, "", [], [], {}, {}, gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), {})

def submit_answer(audio, interview_state):
    """Handles submitting an answer via audio."""
    if not audio or not interview_state:
        return ("No audio recorded or interview not started.", "", interview_state,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=True),
                gr.update(visible=True))

    try:
        # Save audio to a temporary file
        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, "recorded_audio.wav")
        # audio is a tuple (sample_rate, numpy_array)
        sample_rate, audio_data = audio
        # Use soundfile to save the numpy array as a WAV file
        sf.write(audio_file_path, audio_data, sample_rate)

        # Convert audio file to text
        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data_sr = r.record(source)
        answer_text = r.recognize_google(audio_data_sr)
        print(f"Recognized Answer: {answer_text}")

        # Clean up temporary audio file
        os.remove(audio_file_path)
        os.rmdir(temp_dir)

        # Update state with the answer
        interview_state["answers"].append(answer_text)
        current_q_index = interview_state["current_q_index"]
        current_question = interview_state["questions"][current_q_index]
        interview_state["interactions"][f"Q{current_q_index + 1}: {current_question}"] = f"A{current_q_index + 1}: {answer_text}"

        # Generate feedback and metrics for the current question
        percent_str = generate_feedback(current_question, answer_text)
        try:
            percent = float(percent_str)
        except ValueError:
            percent = 0.0

        feedback_text = generate_overall_feedback(interview_state["resume_data"], percent_str, answer_text, current_question)
        interview_state["feedback"].append(feedback_text)

        metrics = generate_metrics(interview_state["resume_data"], answer_text, current_question)
        interview_state["metrics_list"].append(metrics) # Store metrics for this question

        # Update state index
        interview_state["current_q_index"] += 1

        return (
            f"Answer submitted: {answer_text}",
            answer_text,
            interview_state,
            gr.update(visible=True), # Show feedback textbox
            gr.update(value=feedback_text, visible=True), # Update feedback textbox
            gr.update(visible=True), # Show metrics display
            gr.update(value=metrics, visible=True), # Update metrics display
            gr.update(visible=True), # Keep audio input visible for next question
            gr.update(visible=True), # Keep submit answer button
            gr.update(visible=True), # Keep next question button
            gr.update(visible=False), # Submit interview button still hidden
            gr.update(visible=True), # Question display
            gr.update(visible=True) # Answer instructions
        )

    except Exception as e:
        print(f"Error processing audio answer: {e}")
        return ("Error processing audio. Please try again.", "", interview_state,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=True),
                gr.update(visible=True))

def next_question(interview_state):
    """Moves to the next question or ends the interview."""
    if not interview_state:
        return ("Interview not started.", "", interview_state, gr.update(visible=True),
                gr.update(visible=True), gr.update(visible=True), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
                gr.update(visible=False), gr.update(visible=False))

    current_q_index = interview_state["current_q_index"]
    total_questions = len(interview_state["questions"])

    if current_q_index < total_questions:
        next_q = interview_state["questions"][current_q_index]
        return (
            f"Question {current_q_index + 1}/{total_questions}",
            next_q,
            interview_state,
            gr.update(visible=True), # Audio input
            gr.update(visible=True), # Submit Answer
            gr.update(visible=True), # Next Question
            gr.update(visible=False), # Feedback textbox (hidden for new question)
            gr.update(visible=False), # Metrics display (hidden for new question)
            gr.update(visible=False), # Submit Interview (still hidden)
            gr.update(visible=True), # Question display
            gr.update(visible=True), # Answer instructions
            "", # Clear previous answer display
            {} # Clear previous metrics display
        )
    else:
        # Interview finished
        return (
            "Interview completed! Click 'Submit Interview' to see your evaluation.",
            "Interview Finished",
            interview_state,
            gr.update(visible=False), # Hide audio input
            gr.update(visible=False), # Hide submit answer
            gr.update(visible=False), # Hide next question
            gr.update(visible=False), # Hide feedback textbox
            gr.update(visible=False), # Hide metrics display
            gr.update(visible=True), # Show submit interview button
            gr.update(visible=True), # Question display (shows finished)
            gr.update(visible=False), # Hide answer instructions
            "", # Clear answer display
            {} # Clear metrics display
        )

def submit_interview(interview_state):
    """Handles final submission and triggers evaluation."""
    if not interview_state:
        return "Interview state is missing.", interview_state

    # The evaluation logic would typically be triggered here or handled in a separate function.
    # For now, we'll just indicate it's ready.
    print("Interview submitted for evaluation.")
    print("Final State:", interview_state)
    # In a full implementation, you might call an evaluation function here
    # or redirect to an evaluation page/component.

    return "Interview submitted successfully!", interview_state

# --- Login and Navigation Logic (Firebase Integrated) ---

def login(email, password):
    # Simple mock login using Firebase - replace with real authentication logic
    # For demo, accept any non-empty username/password
    # In a real app, you would verify the password against Firebase Auth (server-side)
    # This is a simplified placeholder that checks if user exists.
    if not email or not password:
        return ("Please enter email and password.", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, "")

    try:
        # Attempt to get user by email (this checks existence, not password in client-side code)
        # A real implementation would involve secure server-side verification.
        user = auth.get_user_by_email(email)
        welcome_msg = f"Welcome, {user.display_name or user.uid}!" # Use display name or UID
        # Show main app, hide login
        return (welcome_msg,
                gr.update(visible=False), # login_section
                gr.update(visible=True),  # main_app
                "", "", # Clear email/password inputs
                user.uid) # Update user_state with UID
    except auth.UserNotFoundError:
        return ("User not found. Please check your email or sign up.", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, "")
    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        print(error_msg)
        return (error_msg, gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, "")

def signup(email, password, username):
    if not email or not password or not username:
        return ("Please fill all fields.", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, username, "")

    try:
        # Create user in Firebase
        user = auth.create_user(email=email, password=password, uid=username, display_name=username)
        success_msg = f"Account created successfully for {username}!"
        # Automatically log the user in or prompt for login
        # Here, we'll just show success and keep them on the signup form
        return (success_msg, gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "", "", "", user.uid) # Clear inputs, set user state
    except auth.UidAlreadyExistsError:
        return ("Username already exists. Please choose another.", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, username, "")
    except auth.EmailAlreadyExistsError:
        return ("Email already exists. Please use another email.", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, username, "")
    except Exception as e:
        error_msg = f"Signup failed: {str(e)}"
        print(error_msg)
        return (error_msg, gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), email, password, username, "")

def logout():
    return ("", # Clear login status
            gr.update(visible=True),  # Show login section
            gr.update(visible=False), # Hide main app
            gr.update(visible=False), # Hide signup section (if it was visible)
            "", "", "", # Clear email/password/username inputs
            "") # Clear user_state

def navigate_to_interview():
    return (gr.update(visible=True), gr.update(visible=False)) # Show interview, hide chat

def navigate_to_chat():
    return (gr.update(visible=False), gr.update(visible=True)) # Hide interview, show chat

# --- Import Chat Module Functions ---
# Assuming chat.py is in the same directory or correctly in the Python path
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
    # State to hold interview data
    interview_state = gr.State({})
    # State for username/UID
    user_state = gr.State("")

    # --- Login Section ---
    with gr.Column(visible=True) as login_section:
        gr.Markdown("## Login")
        login_email_input = gr.Textbox(label="Email Address")
        login_password_input = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_status = gr.Textbox(label="Login Status", interactive=False)
        # Switch to Signup
        switch_to_signup_btn = gr.Button("Don't have an account? Sign Up")

    # --- Signup Section ---
    with gr.Column(visible=False) as signup_section:
        gr.Markdown("## Sign Up")
        signup_email_input = gr.Textbox(label="Email Address")
        signup_password_input = gr.Textbox(label="Password", type="password")
        signup_username_input = gr.Textbox(label="Unique Username")
        signup_btn = gr.Button("Create my account")
        signup_status = gr.Textbox(label="Signup Status", interactive=False)
        # Switch to Login
        switch_to_login_btn = gr.Button("Already have an account? Login")

    # --- Main App Sections (Initially Hidden) ---
    with gr.Column(visible=False) as main_app:
        with gr.Row():
            with gr.Column(scale=1):
                 logout_btn = gr.Button("Logout")
            with gr.Column(scale=4):
                # Dynamic welcome message (basic approach)
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
                    # File Upload Section
                    with gr.Row():
                        with gr.Column():
                            file_upload_interview = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
                            process_btn_interview = gr.Button("Process Resume")
                        with gr.Column():
                            file_status_interview = gr.Textbox(label="Status", interactive=False)

                    # Role Selection (Initially hidden)
                    role_selection = gr.Dropdown(
                        choices=["Data Scientist", "Software Engineer", "Product Manager", "Data Analyst", "Business Analyst"],
                        multiselect=True,
                        label="Select Job Role(s)",
                        visible=False
                    )
                    start_interview_btn = gr.Button("Start Interview", visible=False)

                    # Interview Section (Initially hidden)
                    question_display = gr.Textbox(label="Question", interactive=False, visible=False)
                    answer_instructions = gr.Markdown("Click 'Record Answer' and speak your response.", visible=False)
                    audio_input = gr.Audio(label="Record Answer", type="numpy", visible=False)
                    submit_answer_btn = gr.Button("Submit Answer", visible=False)
                    next_question_btn = gr.Button("Next Question", visible=False)
                    submit_interview_btn = gr.Button("Submit Interview", visible=False, variant="primary")

                    # Feedback and Metrics (Initially hidden)
                    answer_display = gr.Textbox(label="Your Answer", interactive=False, visible=False)
                    feedback_display = gr.Textbox(label="Feedback", interactive=False, visible=False)
                    metrics_display = gr.JSON(label="Metrics", visible=False)

                    # Hidden textbox to hold processed resume data temporarily for interview
                    processed_resume_data_hidden_interview = gr.Textbox(visible=False)

                # --- Chat Section ---
                if CHAT_MODULE_AVAILABLE:
                    with gr.Column(visible=False) as chat_selection:
                        gr.Markdown("## Chat with Resume")
                        # File Upload Section (Chat uses its own upload)
                        with gr.Row():
                            with gr.Column():
                                file_upload_chat = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
                                process_chat_btn = gr.Button("Process Resume")
                            with gr.Column():
                                file_status_chat = gr.Textbox(label="Status", interactive=False)

                        # Chat Section (Initially hidden)
                        chatbot = gr.Chatbot(label="Chat History", visible=False)
                        query_input = gr.Textbox(label="Ask about your resume", placeholder="Type your question here...", visible=False)
                        send_btn = gr.Button("Send", visible=False)
                else:
                    with gr.Column(visible=False) as chat_selection:
                        gr.Markdown("## Chat with Resume (Unavailable)")
                        gr.Textbox(value="Chat module is not available.", interactive=False)


        # Navigation buttons
        interview_view = interview_selection
        chat_view = chat_selection

        interview_btn.click(fn=navigate_to_interview, inputs=None, outputs=[interview_view, chat_view])
        if CHAT_MODULE_AVAILABLE:
            chat_btn.click(fn=navigate_to_chat, inputs=None, outputs=[interview_view, chat_view])
        # Update welcome message when user_state changes (basic)
        user_state.change(fn=lambda user: f"### Welcome, {user}!" if user else "### Welcome, User!", inputs=[user_state], outputs=[welcome_display])

    # --- Event Listeners for Interview ---
    # Process Resume (Interview)
    process_btn_interview.click(
        fn=process_resume,
        inputs=[file_upload_interview],
        outputs=[
            file_status_interview, role_selection, start_interview_btn,
            question_display, answer_instructions, audio_input,
            submit_answer_btn, next_question_btn, submit_interview_btn,
            answer_display, feedback_display, metrics_display,
            processed_resume_data_hidden_interview
        ]
    )

    # Start Interview
    start_interview_btn.click(
        fn=start_interview,
        inputs=[role_selection, processed_resume_data_hidden_interview],
        outputs=[
            file_status_interview, question_display,
            # Outputs for UI updates
            audio_input, submit_answer_btn, next_question_btn,
            submit_interview_btn, feedback_display, metrics_display,
            question_display, answer_instructions, # These are UI updates
            interview_state # Update the state object itself
        ]
    )

    # Submit Answer
    submit_answer_btn.click(
        fn=submit_answer,
        inputs=[audio_input, interview_state],
        outputs=[
            file_status_interview, answer_display, interview_state,
            feedback_display, feedback_display, # Update value and visibility
            metrics_display, metrics_display,   # Update value and visibility
            audio_input, submit_answer_btn, next_question_btn,
            submit_interview_btn, question_display, answer_instructions
        ]
    )

    # Next Question
    next_question_btn.click(
        fn=next_question,
        inputs=[interview_state],
        outputs=[
            file_status_interview, question_display, interview_state,
            audio_input, submit_answer_btn, next_question_btn,
            feedback_display, metrics_display, submit_interview_btn,
            question_display, answer_instructions,
            answer_display, metrics_display # Clear previous answer/metrics display
        ]
    )

    # Submit Interview (Placeholder for evaluation trigger)
    submit_interview_btn.click(
        fn=submit_interview,
        inputs=[interview_state],
        outputs=[file_status_interview, interview_state]
        # In a full app, you might navigate to an evaluation page here
    )

    # --- Event Listeners for Chat (if available) ---
    if CHAT_MODULE_AVAILABLE:
        # Process Resume for Chat
        process_chat_btn.click(
            fn=chat_module.process_resume_chat,
            inputs=[file_upload_chat],
            outputs=[file_status_chat, processed_resume_data_state, query_input, send_btn, chatbot]
        )

        # Chat Interaction
        send_btn.click(
            fn=chat_module.chat_with_resume,
            inputs=[query_input, processed_resume_data_state, chatbot], # chatbot provides history
            outputs=[query_input, chatbot] # Update input (clear) and chatbot (new history)
        )
        query_input.submit( # Allow submitting with Enter key
            fn=chat_module.chat_with_resume,
            inputs=[query_input, processed_resume_data_state, chatbot],
            outputs=[query_input, chatbot]
        )

    # --- Login/Logout Event Listeners ---
    login_btn.click(
        fn=login,
        inputs=[login_email_input, login_password_input],
        outputs=[login_status, login_section, main_app, signup_section, login_email_input, login_password_input, user_state]
    )

    signup_btn.click(
        fn=signup,
        inputs=[signup_email_input, signup_password_input, signup_username_input],
        outputs=[signup_status, signup_section, login_section, main_app, signup_email_input, signup_password_input, signup_username_input, user_state]
    )

    logout_btn.click(
        fn=logout,
        inputs=None,
        outputs=[login_status, login_section, main_app, signup_section, login_email_input, login_password_input, signup_username_input, user_state]
    )

    # Switch between Login and Signup
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

# Run the app
if __name__ == "__main__":
    demo.launch(share=True) # You can add server_name="0.0.0.0", server_port=7860 for external access
