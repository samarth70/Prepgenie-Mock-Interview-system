# PrepGenie/app.py
"""Main Gradio application file."""

import gradio as gr
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import datetime

# --- Import Logic Modules ---
import interview_logic
import interview_history
# import auth_logic # If you move auth logic
# import chat_logic # If chat logic is moved

# --- Environment and Configuration ---
load_dotenv()

# --- Firebase Admin SDK Setup (in app.py or auth_logic) ---
import firebase_admin
from firebase_admin import credentials, auth, firestore # Added firestore

def initialize_firebase():
    """Attempts to initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        print("Firebase app already initialized in app.py.")
        return firebase_admin.get_app()
    cred = None
    try:
        firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if firebase_credentials_path and os.path.exists(firebase_credentials_path):
            print(f"Initializing Firebase with credentials file in app.py: {firebase_credentials_path}")
            cred = credentials.Certificate(firebase_credentials_path)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized successfully using credentials file in app.py.")
            return firebase_app
        elif not firebase_credentials_path:
             print("FIREBASE_CREDENTIALS_PATH is not set or is None in app.py.")
        else:
             print(f"Firebase credentials file not found at {firebase_credentials_path} in app.py.")
    except Exception as e:
        print(f"Failed to initialize Firebase using credentials file in app.py: {e}")
    try:
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_credentials_json:
            print("Initializing Firebase with credentials from FIREBASE_CREDENTIALS_JSON environment variable in app.py.")
            cred_dict = json.loads(firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized successfully using FIREBASE_CREDENTIALS_JSON in app.py.")
            return firebase_app
        else:
             print("FIREBASE_CREDENTIALS_JSON environment variable not set in app.py.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing FIREBASE_CREDENTIALS_JSON in app.py: {e}")
    except Exception as e:
        print(f"Failed to initialize Firebase using FIREBASE_CREDENTIALS_JSON in app.py: {e}")
    print("Warning: Firebase Admin SDK could not be initialized in app.py. Authentication features will not work.")
    return None

FIREBASE_APP = initialize_firebase()
FIREBASE_AVAILABLE = FIREBASE_APP is not None

# --- Generative AI Setup ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or "YOUR_DEFAULT_API_KEY_HERE")
TEXT_MODEL = genai.GenerativeModel("gemini-1.5-flash") # Global model instance
print("Using Generative AI model: gemini-1.5-flash in app.py")

# --- Import Chat Module Functions ---
try:
    from login_module import chat as chat_module # Assuming this is external
    CHAT_MODULE_AVAILABLE = True
    print("Chat module imported successfully in app.py.")
except ImportError as e:
    print(f"Warning: Could not import chat module in app.py: {e}")
    CHAT_MODULE_AVAILABLE = False
    chat_module = None

# --- Helper Functions for UI Updates ---
def apply_ui_updates(updates_dict):
    """Converts logic function UI update instructions to Gradio updates."""
    gr_updates = {}
    for component_name, instruction in updates_dict.items():
        if instruction == "gr_hide":
            gr_updates[component_name] = gr.update(visible=False)
        elif instruction == "gr_show":
            gr_updates[component_name] = gr.update(visible=True)
        elif instruction == "gr_show_and_update":
             # This needs specific handling in the calling function
             # Placeholder, logic should set value in calling function
             gr_updates[component_name] = gr.update(visible=True)
        elif instruction == "gr_show_and_update_error":
             gr_updates[component_name] = gr.update(visible=True)
        elif instruction == "gr_clear":
             gr_updates[component_name] = "" # For textboxes
        elif instruction == "gr_clear_dict":
             gr_updates[component_name] = {} # For JSON
        # Add more instructions as needed
        else:
            # Default or pass through
            gr_updates[component_name] = gr.update()
    return gr_updates

# --- Navigation Functions ---
def navigate_to_interview():
    return (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False))

def navigate_to_chat():
    return (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False))

def navigate_to_history():
    return (gr.update(visible=False), gr.update(visible=False), gr.update(visible=True))

# --- Event Handler Functions (Orchestrators) ---
def process_resume_handler(file_obj):
    """Handles resume processing event."""
    result = interview_logic.process_resume_logic(file_obj)
    ui_updates = apply_ui_updates(result["ui_updates"])
    # Unpack ui_updates in the correct order for outputs
    return (
        result["status"],
        ui_updates.get("role_selection", gr.update()),
        ui_updates.get("start_interview_btn", gr.update()),
        ui_updates.get("question_display", gr.update()),
        ui_updates.get("answer_instructions", gr.update()),
        ui_updates.get("audio_input", gr.update()),
        ui_updates.get("submit_answer_btn", gr.update()),
        ui_updates.get("next_question_btn", gr.update()),
        ui_updates.get("submit_interview_btn", gr.update()),
        ui_updates.get("answer_display", gr.update()),
        ui_updates.get("feedback_display", gr.update()),
        ui_updates.get("metrics_display", gr.update()),
        result["processed_data"] # Pass processed data
    )

def start_interview_handler(roles, processed_resume_data):
    """Handles interview start event."""
    # First, format the resume data using the AI model
    formatted_resume_data = interview_logic.getallinfo(processed_resume_data, TEXT_MODEL)
    result = interview_logic.start_interview_logic(roles, formatted_resume_data, TEXT_MODEL)
    ui_updates = apply_ui_updates(result["ui_updates"])
    return (
        result["status"],
        result["initial_question"],
        ui_updates.get("audio_input", gr.update()),
        ui_updates.get("submit_answer_btn", gr.update()),
        ui_updates.get("next_question_btn", gr.update()),
        ui_updates.get("submit_interview_btn", gr.update()),
        ui_updates.get("feedback_display", gr.update()),
        ui_updates.get("metrics_display", gr.update()),
        ui_updates.get("question_display", gr.update()),
        ui_updates.get("answer_instructions", gr.update()),
        result["interview_state"]
    )

def submit_answer_handler(audio, interview_state):
    """Handles answer submission event."""
    result = interview_logic.submit_answer_logic(audio, interview_state, TEXT_MODEL)
    ui_updates = apply_ui_updates(result["ui_updates"])
    # Handle special updates for feedback and metrics that need value setting
    feedback_update = ui_updates.get("feedback_display", gr.update())
    if "gr_show_and_update" in result["ui_updates"].values():
        feedback_update = gr.update(visible=True, value=result["feedback_text"])
    metrics_update = ui_updates.get("metrics_display", gr.update())
    if "gr_show_and_update" in result["ui_updates"].values():
        metrics_update = gr.update(visible=True, value=result["metrics"])

    return (
        result["status"],
        result["answer_text"],
        result["interview_state"],
        feedback_update,
        metrics_update,
        ui_updates.get("audio_input", gr.update()),
        ui_updates.get("submit_answer_btn", gr.update()),
        ui_updates.get("next_question_btn", gr.update()),
        ui_updates.get("submit_interview_btn", gr.update()),
        ui_updates.get("question_display", gr.update()),
        ui_updates.get("answer_instructions", gr.update())
    )

def next_question_handler(interview_state):
    """Handles next question event."""
    result = interview_logic.next_question_logic(interview_state)
    ui_updates = apply_ui_updates(result["ui_updates"])
    return (
        result["status"],
        result["next_q"],
        result["interview_state"],
        ui_updates.get("audio_input", gr.update()),
        ui_updates.get("submit_answer_btn", gr.update()),
        ui_updates.get("next_question_btn", gr.update()),
        ui_updates.get("feedback_display", gr.update()),
        ui_updates.get("metrics_display", gr.update()),
        ui_updates.get("submit_interview_btn", gr.update()),
        ui_updates.get("question_display", gr.update()),
        ui_updates.get("answer_instructions", gr.update()),
        ui_updates.get("answer_display", ""), # Clear
        ui_updates.get("metrics_display_clear", {}) # Clear
    )

def submit_interview_handler(interview_state, user_id_state=""):
    """Handles interview submission event."""
    result = interview_logic.submit_interview_logic(interview_state, TEXT_MODEL)
    ui_updates = apply_ui_updates(result["ui_updates"])

    # --- NEW: Save Interview History ---
    if FIREBASE_AVAILABLE and user_id_state and "report_text" in result and "chart_buffer" in result:
        print(f"Attempting to save history for user: {user_id_state} in submit_interview_handler")
        # Package data for saving (using data from interview_state and result)
        interview_summary_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "resume_overview": interview_state.get("resume_data", ""),
            "selected_roles": interview_state.get("selected_roles", []),
            "questions": list(interview_state.get("interactions", {}).keys()),
            "answers": list(interview_state.get("interactions", {}).values()),
            "feedback": interview_state.get("feedback", []),
            "interactions": interview_state.get("interactions", {}),
            "metrics_list": interview_state.get("metrics_list", []),
            "final_metrics": interview_logic.parse_metrics(interview_logic.getmetrics(interview_state.get("interactions", {}), interview_state.get("resume_data", ""), TEXT_MODEL)), # Recalculate or pass from logic?
            # Use average from report text parsing or recalculate if needed, or pass from logic if stored
            "average_rating": sum(interview_logic.parse_metrics(interview_logic.getmetrics(interview_state.get("interactions", {}), interview_state.get("resume_data", ""), TEXT_MODEL)).values()) / len(interview_logic.parse_metrics(interview_logic.getmetrics(interview_state.get("interactions", {}), interview_state.get("resume_data", ""), TEXT_MODEL))) if interview_logic.parse_metrics(interview_logic.getmetrics(interview_state.get("interactions", {}), interview_state.get("resume_data", ""), TEXT_MODEL)) else 0.0,
            "evaluation_report": result["report_text"]
        }
        save_success = interview_history.save_interview_history(user_id_state, interview_summary_data)
        if save_success:
            print("Interview history saved successfully in submit_interview_handler.")
            # Optionally append to report text
            # result["report_text"] += "\n\n---\n*Interview history saved successfully.*"
        else:
            print("Failed to save interview history in submit_interview_handler.")
            # result["report_text"] += "\n\n---\n*Failed to save interview history.*"
    else:
        if not user_id_state:
            print("User not logged in. Skipping history save in submit_interview_handler.")
        else:
            print("Firestore not available. Skipping history save in submit_interview_handler.")

    # Handle special updates for report and chart that need value setting
    report_update = ui_updates.get("evaluation_report_display", gr.update())
    if "gr_show_and_update" in result["ui_updates"].values():
        report_update = gr.update(visible=True, value=result["report_text"])
    elif "gr_show_and_update_error" in result["ui_updates"].values():
         report_update = gr.update(visible=True, value=result["report_text"]) # Show error

    chart_update = ui_updates.get("evaluation_chart_display", gr.update())
    if "gr_show_and_update" in result["ui_updates"].values():
        chart_update = gr.update(visible=True, value=result["chart_buffer"])
    elif "gr_show_and_update_error" in result["ui_updates"].values():
         chart_update = gr.update(visible=False) # Hide chart on error

    return (
        result["status"],
        result["interview_state"], # Pass through
        report_update,
        chart_update
    )

# --- Login/Logout Logic (Simplified here, could be in auth_logic) ---
def login(email, password):
    if not FIREBASE_AVAILABLE:
        return (
            "Firebase not initialized. Login unavailable.",
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            "", "", "", ""
        )
    if not email or not password:
        return (
            "Please enter email and password.",
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            email, password, "", ""
        )
    try:
        user = auth.get_user_by_email(email)
        welcome_msg = f"Welcome, {user.display_name or user.uid}!"
        return (
            welcome_msg,
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=True),
            "", "", user.uid, user.email
        )
    except auth.UserNotFoundError:
        return (
            "User not found. Please check your email or sign up.",
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            email, password, "", ""
        )
    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        print(error_msg)
        return (
            error_msg,
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            email, password, "", ""
        )

def signup(email, password, username):
    if not FIREBASE_AVAILABLE:
        return (
            "Firebase not initialized. Signup unavailable.",
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            "", "", "", "", ""
        )
    if not email or not password or not username:
        return (
            "Please fill all fields.",
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
            email, password, username, "", ""
        )
    try:
        user = auth.create_user(email=email, password=password, uid=username, display_name=username)
        success_msg = f"Account created successfully for {username}!"
        return (
            success_msg,
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            "", "", "", user.uid, user.email
        )
    except auth.UidAlreadyExistsError:
        return (
            "Username already exists. Please choose another.",
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
            email, password, username, "", ""
        )
    except auth.EmailAlreadyExistsError:
        return (
            "Email already exists. Please use another email.",
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
            email, password, username, "", ""
        )
    except Exception as e:
        error_msg = f"Signup failed: {str(e)}"
        print(error_msg)
        return (
            error_msg,
            gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
            email, password, username, "", ""
        )

def logout():
    return (
        "",
        gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
        "", "", "", "", ""
    )

# --- Gradio Interface ---
with gr.Blocks(title="PrepGenie - Mock Interviewer") as demo:
    interview_state = gr.State({})
    user_state = gr.State("") # Holds user.uid
    user_email_state = gr.State("") # Holds user.email
    processed_resume_data_state = gr.State("")

    # --- Header Section ---
    with gr.Row():
        gr.Markdown(
            """
            <h1 style="display: flex; justify-content: center; align-items: center;">
                PrepGenie- Interview Preparation App
            </h1>
            """,
            elem_id="title"
        )

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
                history_btn = gr.Button("My Interview History")

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

                # --- History Section ---
                with gr.Column(visible=False) as history_selection:
                    gr.Markdown("## Your Interview History")
                    load_history_btn = gr.Button("Load My Past Interviews")
                    history_output = gr.Textbox(label="Past Interviews", max_lines=30, interactive=False, visible=True)

        # Assign view variables for navigation
        interview_view = interview_selection
        chat_view = chat_selection
        history_view = history_selection

        # Navigation button listeners
        interview_btn.click(fn=navigate_to_interview, inputs=None, outputs=[interview_view, chat_view, history_view])
        if CHAT_MODULE_AVAILABLE:
            chat_btn.click(fn=navigate_to_chat, inputs=None, outputs=[interview_view, chat_view, history_view])
        history_btn.click(fn=navigate_to_history, inputs=None, outputs=[interview_view, chat_view, history_view])

    # --- Event Listeners for Interview ---
    process_btn_interview.click(
        fn=process_resume_handler,
        inputs=[file_upload_interview],
        outputs=[
            file_status_interview, role_selection, start_interview_btn,
            question_display, answer_instructions, audio_input,
            submit_answer_btn, next_question_btn, submit_interview_btn,
            answer_display, feedback_display, metrics_display,
            processed_resume_data_hidden_interview
        ]
    )
    start_interview_btn.click(
        fn=start_interview_handler,
        inputs=[role_selection, processed_resume_data_hidden_interview],
        outputs=[
            file_status_interview, question_display,
            audio_input, submit_answer_btn, next_question_btn,
            submit_interview_btn, feedback_display, metrics_display,
            question_display, answer_instructions,
            interview_state
        ]
    )
    submit_answer_btn.click(
        fn=submit_answer_handler,
        inputs=[audio_input, interview_state],
        outputs=[
            file_status_interview, answer_display, interview_state,
            feedback_display, metrics_display,
            audio_input, submit_answer_btn, next_question_btn,
            submit_interview_btn, question_display, answer_instructions
        ]
    )
    next_question_btn.click(
        fn=next_question_handler,
        inputs=[interview_state],
        outputs=[
            file_status_interview, question_display, interview_state,
            audio_input, submit_answer_btn, next_question_btn,
            feedback_display, metrics_display, submit_interview_btn,
            question_display, answer_instructions,
            answer_display, metrics_display # Clear previous
        ]
    )
    submit_interview_btn.click(
        fn=submit_interview_handler,
        inputs=[interview_state, user_state], # Pass user_state for history saving
        outputs=[
            file_status_interview,
            interview_state,
            evaluation_report_display,
            evaluation_chart_display
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

    # --- NEW: Event Listener for History ---
    load_history_btn.click(fn=interview_history.load_user_history, inputs=[user_state], outputs=[history_output])

    # --- Login/Logout Event Listeners ---
    login_btn.click(
        fn=login,
        inputs=[login_email_input, login_password_input],
        outputs=[login_status, login_section, signup_section, main_app,
                 login_email_input, login_password_input, user_state, user_email_state]
    )
    signup_btn.click(
        fn=signup,
        inputs=[signup_email_input, signup_password_input, signup_username_input],
        outputs=[signup_status, login_section, signup_section, main_app,
                 signup_email_input, signup_password_input, signup_username_input,
                 user_state, user_email_state]
    )
    logout_btn.click(
        fn=logout,
        inputs=None,
        outputs=[login_status, login_section, signup_section, main_app,
                 login_email_input, login_password_input, signup_username_input,
                 user_state, user_email_state]
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
    demo.launch(server_name="0.0.0.0")
