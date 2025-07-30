# PrepGenie/login_module/chat.py
import gradio as gr
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
text_model = genai.GenerativeModel("gemini-2.5-flash")


def file_processing_chat(pdf_file_obj): # Take the Gradio file object
    """Processes the uploaded PDF file for the chat module."""
    if not pdf_file_obj:
        print("No file object provided to file_processing_chat.")
        return ""

    try:
        # --- Key Fix: Extract the file path correctly ---
        if hasattr(pdf_file_obj, 'name'):
            file_path = pdf_file_obj.name
        else:
            file_path = str(pdf_file_obj)
            print(f"File object does not have 'name' attribute. Using str(): {file_path}")

        print(f"Attempting to process file at path: {file_path}")

        # --- Use the file path with PyPDF2 ---
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        error_msg = f"File not found at path: {file_path}"
        print(error_msg)
        return ""
    except PyPDF2.errors.PdfReadError as e:
        error_msg = f"Error reading PDF file {file_path}: {e}"
        print(error_msg)
        return ""
    except Exception as e:
        error_msg = f"Unexpected error processing PDF from object {pdf_file_obj}: {e}"
        print(error_msg)
        return ""

def getallinfo_chat(data):
    """Formats resume data."""
    if not data or not data.strip():
        return "No resume data provided or data is empty."

    text = f"""{data} is given by the user. Make sure you are getting the details like name, experience,
            education, skills of the user like in a resume. If the details are not provided return: not a resume.
            If details are provided then please try again and format the whole in a single paragraph covering all the information. """
    try:
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error formatting resume data: {e}")
        return "Error processing resume data."

def get_answer(question, input_text):
    """Generates answer/suggestions based on the question and resume text."""
    # Handle empty inputs
    if not question or not question.strip() or not input_text or not input_text.strip():
        return "Please provide a question and ensure your resume is processed."

    text = f"""You are a Great Resume Checker, you are given the details about the user and the user
            needs some changes about their resume and you are the one to guide them.
            There are queries which user wants to be solved about their resume. You are asked a question which is: {question} and
            you have to generate suggestions to improve the resume based on the text: {input_text}. Answer in a way that the user
            can understand and make the changes in their resume. and In paragraph form. maximum of 2 paragraphs. dont tell over the top.
            it should be less and precise. dont tell the user to change the whole resume. just give them some suggestions. dont give
            bullet points. Be point to point with user."""
    try:
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, I couldn't generate an answer at the moment."

# --- Gradio Chat Interface Functions ---

def process_resume_chat(file_obj):
    """Handles resume upload and initial processing for chat."""
    if not file_obj:
        return "Please upload a PDF resume.", "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    try:
        # Save uploaded file to a temporary location
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_obj.name)
        with open(file_path, "wb") as f:
            f.write(file_obj.read())

        # Process the PDF
        raw_text = file_processing_chat(file_path)
        if not raw_text.strip():
             os.remove(file_path)
             os.rmdir(temp_dir)
             return "Could not extract text from the PDF.", "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        processed_data = getallinfo_chat(raw_text)

        # Clean up temporary file
        os.remove(file_path)
        os.rmdir(temp_dir)

        return (
            f"Resume processed successfully!",
            processed_data, # Pass processed data for chat
            gr.update(visible=True), # Show chat input
            gr.update(visible=True), # Show send button
            [] # Clear previous chat history (return empty list for Chatbot)
        )
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(error_msg)
        return error_msg, "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def chat_with_resume(query, resume_data, history):
    """Handles the chat interaction."""
    # history is automatically managed by Gradio Chatbot, we just need to append to it
    if not query or not query.strip() or not resume_data or not resume_data.strip():
        # Return existing history if inputs are missing or empty
        # Gradio Chatbot expects a list of tuples [(user_msg, bot_response), ...]
        # If history is None, initialize as empty list
        current_history = history if history is not None else []
        # Add the error message to the chat history
        current_history.append((query if query else "", "Please enter a question and ensure your resume is processed."))
        return "", current_history # Clear input, update history

    try:
        answer = get_answer(query, resume_data)
        # Update history
        # Gradio Chatbot expects a list of tuples [(user_msg, bot_response), ...]
        current_history = history if history is not None else []
        current_history.append((query, answer))
        return "", current_history # Clear input, update history
    except Exception as e:
        error_msg = f"Error during chat: {str(e)}"
        print(error_msg)
        current_history = history if history is not None else []
        current_history.append((query, error_msg))
        return "", current_history

