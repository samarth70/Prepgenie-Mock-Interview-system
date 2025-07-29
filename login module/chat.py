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
text_model = genai.GenerativeModel("gemini-pro")

# --- Helper Functions (Logic from Streamlit Chat) ---

def file_processing_chat(pdf_file_path):
    """Processes the uploaded PDF file."""
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

def getallinfo_chat(data):
    """Formats resume data."""
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

# --- Gradio Chat Interface ---

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
            "" # Clear previous chat history display
        )
    except Exception as e:
        return f"Error processing file: {str(e)}", "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def chat_with_resume(query, resume_data, history):
    """Handles the chat interaction."""
    if not query or not resume_data:
        # Return existing history if inputs are missing
        return "", history or []

    try:
        answer = get_answer(query, resume_data)
        # Update history
        new_history = history or []
        new_history.append((query, answer))
        return "", new_history # Clear input, update history
    except Exception as e:
        error_msg = f"Error during chat: {str(e)}"
        new_history = history or []
        new_history.append((query, error_msg))
        return "", new_history

# --- Gradio Interface for Chat ---

with gr.Blocks(title="PrepGenie - Chat with Resume") as chat_demo:
    gr.Markdown("# 🦈 PrepGenie - Chat with Resume")
    gr.Markdown("Upload your resume and ask questions about it.")

    # State for chat history
    chat_history = gr.State([])

    with gr.Row():
        with gr.Column():
            file_upload_chat = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
            process_chat_btn = gr.Button("Process Resume")
        with gr.Column():
            file_status_chat = gr.Textbox(label="Status", interactive=False)

    # Hidden textbox for processed resume data
    processed_resume_data_chat = gr.Textbox(visible=False)

    # Chat Section (Initially hidden)
    chatbot = gr.Chatbot(label="Chat History", visible=False)
    query_input = gr.Textbox(label="Ask about your resume", placeholder="Type your question here...", visible=False)
    send_btn = gr.Button("Send", visible=False)

    # --- Event Listeners for Chat ---

    # Process Resume for Chat
    process_chat_btn.click(
        fn=process_resume_chat,
        inputs=[file_upload_chat],
        outputs=[file_status_chat, processed_resume_data_chat, query_input, send_btn, chatbot]
    )

    # Chat Interaction
    send_btn.click(
        fn=chat_with_resume,
        inputs=[query_input, processed_resume_data_chat, chat_history],
        outputs=[query_input, chat_history]
    )
    query_input.submit( # Allow submitting with Enter key
        fn=chat_with_resume,
        inputs=[query_input, processed_resume_data_chat, chat_history],
        outputs=[query_input, chat_history]
    )

    # Update chatbot display when history changes
    chat_history.change(
        fn=lambda hist: hist,
        inputs=[chat_history],
        outputs=[chatbot]
    )

# Run the chat app separately or integrate into main app
# if __name__ == "__main__":
#     chat_demo.launch()