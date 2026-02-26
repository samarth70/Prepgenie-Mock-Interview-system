# PrepGenie/login_module/chat.py
import gradio as gr
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Generative AI (Ensure model name is correct)
# Note: 'gemini-2.5-flash' might need verification. Common ones are 'gemini-1.5-flash', 'gemini-pro'.
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
text_model = genai.GenerativeModel("gemini-2.0-flash") # Potentially incorrect model name
# text_model = genai.GenerativeModel("gemini-1.5-flash") # Using a known model name
# print("Using Generative AI model for chat: gemini-1.5-flash")


def file_processing_chat(pdf_file_path_string): # Expect the file path string directly
    """Processes the uploaded PDF file given its path."""
    if not pdf_file_path_string:
        print("No file path provided to file_processing_chat.")
        return ""

    try:
        # Ensure the input is treated as a string path
        file_path = str(pdf_file_path_string)
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
        error_msg = f"Unexpected error processing PDF from path {pdf_file_path_string}: {e}"
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
        # Use the correct model instance
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
        # Use the correct model instance
        response = text_model.generate_content(text)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, I couldn't generate an answer at the moment."


# --- Gradio Chat Interface Functions ---

def process_resume_chat(file_obj):
    """Handles resume upload and initial processing for chat."""
    print(f"process_resume_chat called with: {file_obj}") # Debug print
    if not file_obj:
        print("No file uploaded in process_resume_chat.")
        return (
            "Please upload a PDF resume.",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    try:
        # --- Correctly handle the file path from Gradio ---
        # Determine the correct file path from the Gradio object
        if hasattr(file_obj, 'name'):
            # This is the standard way for Gradio File uploads
            uploaded_file_path = file_obj.name
            print(f"Using Gradio-provided file path: {uploaded_file_path}")
        else:
            # Fallback: If it's already a string path (less common) or different structure
            uploaded_file_path = str(file_obj)
            print(f"File object does not have 'name' attribute. Using str(): {uploaded_file_path}")

        # --- Process the PDF directly from the uploaded file path ---
        # No need to save it again, we can use the path Gradio provided
        raw_text = file_processing_chat(uploaded_file_path) # Pass the path string
        print(f"Raw text extracted (length: {len(raw_text) if raw_text else 0})")

        if not raw_text or not raw_text.strip():
            print("Failed to extract text or text is empty in process_resume_chat.")
            return (
                "Could not extract text from the PDF.",
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            )

        # --- Format the resume data ---
        processed_data = getallinfo_chat(raw_text) # Use the new model instance if corrected
        print(f"Resume processed for chat (length: {len(processed_data) if processed_data else 0})")

        # --- Return success state and values ---
        return (
            f"Resume processed successfully!",
            processed_data,              # Pass processed data for chat
            gr.update(visible=True),     # Show chat input
            gr.update(visible=True),     # Show send button
            []                           # Clear/initialize chat history
        )
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(f"Exception in process_resume_chat: {error_msg}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return (
            error_msg,
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )


def chat_with_resume(query, resume_data, history):
    """Handles the chat interaction."""
    # Initialize history if None
    current_history = history if history is not None else []
    
    if not query or not query.strip() or not resume_data or not resume_data.strip():
        # Add an error message to the chat history
        current_history.append({"role": "user", "content": query if query else ""})
        current_history.append({"role": "assistant", "content": "Please enter a question and ensure your resume is processed."})
        return "", current_history
    
    try:
        answer = get_answer(query, resume_data)
        
        # Append user message
        current_history.append({"role": "user", "content": query})
        # Append assistant message
        current_history.append({"role": "assistant", "content": answer})
        
        return "", current_history
    except Exception as e:
        error_msg = f"Error during chat: {str(e)}"
        print(error_msg)
        current_history.append({"role": "user", "content": query})
        current_history.append({"role": "assistant", "content": error_msg})
        return "", current_history


# Print statement to confirm module load (optional)
print("Chat module loaded successfully.")
