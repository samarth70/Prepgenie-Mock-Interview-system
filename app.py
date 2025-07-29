# PrepGenie/app.py
import gradio as gr
import os
import tempfile
import PyPDF2
import google.generativeai as genai
import tensorflow as tf
from transformers import BertTokenizer, TFBertModel
import numpy as np
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Use environment variable or set a default
text_model = genai.GenerativeModel("gemini-2.5-flash")

# Load BERT model and tokenizer
model = TFBertModel.from_pretrained("bert-base-uncased")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# --- Helper Functions (Logic from Streamlit) ---

def getallinfo(data):
    text = f"""{data} is given by the user. Make sure you are getting the details like name, experience,
            education, skills of the user like in a resume. If the details are not provided return: not a resume.
            If details are provided then please try again and format the whole in a single paragraph covering all the information. """
    response = text_model.generate_content(text)
    response.resolve()
    return response.text

def file_processing(pdf_file_path): # Takes file path now
    with open(pdf_file_path, "rb") as f: # Open file from path
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def get_embedding(text):
    encoded_text = tokenizer(text, return_tensors="tf", truncation=True, padding=True) # Add padding/truncation
    output = model(encoded_text)
    embedding = output.last_hidden_state[:, 0, :]
    return embedding

def generate_feedback(question, answer):
    try:
        question_embedding = get_embedding(question)
        answer_embedding = get_embedding(answer)
        tf.experimental.numpy.experimental_enable_numpy_behavior()
        # Calculate cosine similarity
        dot_product = np.dot(question_embedding, answer_embedding.T)
        norms = np.linalg.norm(question_embedding) * np.linalg.norm(answer_embedding)
        if norms == 0:
            similarity_score = 0.0
        else:
            similarity_score = dot_product / norms
        return f"{similarity_score[0][0]:.2f}" # Format as string
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return "0.00"

def generate_questions(roles, data):
    questions = []
    # Ensure roles is a list and join if needed
    if isinstance(roles, list):
        roles_str = ", ".join(roles)
    else:
        roles_str = str(roles)

    text = f"""If this is not a resume then return text uploaded pdf is not a resume. this is a resume overview of the candidate.
            The candidate details are in {data}. The candidate has applied for the role of {roles_str}.
            Generate questions for the candidate based on the role applied and on the Resume of the candidate.
            Not always necceassary to ask only technical questions related to the role but the logic of question
            should include the job applied for because there might be some deep tech questions which the user might not know.
            Ask some personal questions too.Ask no additional questions. Dont categorize the questions.
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
    prompt = f"""As an interviewer, provide concise feedback (max 150 words) for candidate {data}.
    Questions asked: {questions}
    Candidate's answers: {answer}
    Score: {percent}
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

def store_audio_text():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold = 3
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Speak now... (You have 200 seconds)")
        try:
            # Listen for up to 380 seconds, but stop if 200 seconds of silence
            audio = r.listen(source, timeout=380, phrase_time_limit=200)
            print("Processing audio...")
            text = r.recognize_google(audio)
            print(f"Recognized text: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return " "
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return " "
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return " "
        except Exception as e:
            print(f"An error occurred during speech recognition: {e}")
            return " "

def generate_metrics(data, answer, question):
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
                    value = float(value_str.strip())
                    metrics[key] = value
                except ValueError:
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

# --- Gradio UI Components and Logic ---

def process_resume(file_obj):
    """Handles resume upload and processing."""
    if not file_obj:
        return "Please upload a PDF resume.", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    try:
        # Save uploaded file to a temporary location
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_obj.name)
        with open(file_path, "wb") as f:
            f.write(file_obj.read())

        # Process the PDF
        raw_text = file_processing(file_path)
        processed_data = getallinfo(raw_text)

        # Clean up temporary file
        os.remove(file_path)
        os.rmdir(temp_dir)

        return (
            f"File processed successfully!",
            gr.update(visible=True),  # Role selection dropdown
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            processed_data # Pass processed data for next step
        )
    except Exception as e:
        return f"Error processing file: {str(e)}", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), None

# In PrepGenie/app.py, replace the existing start_interview function with this:

def start_interview(roles, processed_resume_data):
    """Starts the interview process."""
    if not roles or not processed_resume_data:
        # Return initial/empty states for UI components
        return (
            "Please select a role and ensure resume is processed.",
            "", # initial question
            gr.update(visible=False), # audio_input
            gr.update(visible=False), # submit_answer_btn
            gr.update(visible=False), # next_question_btn
            gr.update(visible=False), # submit_interview_btn
            gr.update(visible=False), # feedback_display
            gr.update(visible=False), # metrics_display
            gr.update(visible=False), # question_display (redundant, but matches output count)
            gr.update(visible=False), # answer_instructions
            {} # interview_state (empty dict)
        )

    try:
        questions = generate_questions(roles, processed_resume_data)
        initial_question = questions[0] if questions else "Could you please introduce yourself?"

        # Initialize state for the interview
        interview_state_data = {
            "questions": questions,
            "current_q_index": 0,
            "answers": [],
            "feedback": [],
            "interactions": {},
            "metrics_list": [], # List to store metrics for each question
            "resume_data": processed_resume_data
        }

        # Return values matching the outputs list for start_interview_btn.click
        return (
            "Interview started. Please answer the first question.",
            initial_question,
            gr.update(visible=True), # audio_input visible
            gr.update(visible=True), # submit_answer_btn visible
            gr.update(visible=True), # next_question_btn visible
            gr.update(visible=False), # submit_interview_btn hidden initially
            gr.update(visible=False), # feedback_display hidden initially
            gr.update(visible=False), # metrics_display hidden initially
            gr.update(visible=True), # question_display visible
            gr.update(visible=True), # answer_instructions visible
            interview_state_data # Update the interview_state object
        )
    except Exception as e:
        error_msg = f"Error starting interview: {str(e)}"
        print(error_msg) # Log the error
        return (
            error_msg,
            "", # No question
            gr.update(visible=False), # Hide components
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False), # question_display
            gr.update(visible=False), # answer_instructions
            {} # Empty state on error
        )
def submit_answer(audio, interview_state):
    """Handles submitting an answer via audio."""
    if not audio or not interview_state:
        return "No audio recorded or interview not started.", "", interview_state, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    try:
        # Save audio to a temporary file
        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, "recorded_audio.wav")
        audio[1].save(audio_file_path) # audio is a tuple (sample_rate, numpy_array)

        # Convert audio file to text
        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data = r.record(source)
        answer_text = r.recognize_google(audio_data)
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
        return "Error processing audio. Please try again.", "", interview_state, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)

def next_question(interview_state):
    """Moves to the next question or ends the interview."""
    if not interview_state:
        return "Interview not started.", "", interview_state, gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

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

# --- Gradio Interface ---

with gr.Blocks(title="PrepGenie - Mock Interview") as demo:
    gr.Markdown("# 🦈 PrepGenie - Mock Interview")
    gr.Markdown("Prepare for your next interview with AI-powered feedback.")

    # State to hold interview data
    interview_state = gr.State({})

    # File Upload Section
    with gr.Row():
        with gr.Column():
            file_upload = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
            process_btn = gr.Button("Process Resume")
        with gr.Column():
            file_status = gr.Textbox(label="Status", interactive=False)

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

    # Hidden textbox to hold processed resume data temporarily
    processed_resume_data = gr.Textbox(visible=False)

    # --- Event Listeners ---

    process_btn.click(
        fn=process_resume,
        inputs=[file_upload],
        outputs=[
            file_status, role_selection, start_interview_btn,
            question_display, answer_instructions, audio_input,
            submit_answer_btn, next_question_btn, submit_interview_btn,
            answer_display, feedback_display, metrics_display,
            processed_resume_data # Pass processed data for next step
        ]
    )

    # Start Interview
    start_interview_btn.click(
        fn=start_interview,
        inputs=[role_selection, processed_resume_data],
        outputs=[
            file_status,           # Status message
            question_display,      # First question text
            audio_input,           # Audio input visibility
            submit_answer_btn,     # Submit Answer button visibility
            next_question_btn,     # Next Question button visibility
            submit_interview_btn,  # Submit Interview button visibility (initially hidden)
            feedback_display,      # Feedback textbox (initially hidden/empty)
            metrics_display,       # Metrics display (initially hidden/empty)
            question_display,      # (Duplicate reference, likely not needed, but kept for structure)
            answer_instructions,   # Answer instructions visibility
            interview_state        # THE KEY CHANGE: Update the entire state object
        ]
    )



    # Submit Answer
    submit_answer_btn.click(
        fn=submit_answer,
        inputs=[audio_input, interview_state],
        outputs=[
            file_status, answer_display, interview_state,
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
            file_status, question_display, interview_state,
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
        outputs=[file_status, interview_state]
        # In a full app, you might navigate to an evaluation page here
    )

# Run the app
if __name__ == "__main__":
    demo.launch() # You can add server_name="0.0.0.0", server_port=7860 for external access