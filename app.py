# PrepGenie/app.py
"""Main Gradio application file."""

import gradio as gr
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import datetime

# --- Environment and Configuration ---
load_dotenv()

# --- Generative AI Setup ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or "YOUR_DEFAULT_API_KEY_HERE")
TEXT_MODEL = genai.GenerativeModel("gemini-1.5-flash") # Global model instance
print("Using Generative AI model: gemini-1.5-flash")

# --- Import Logic Modules ---
import interview_logic
import interview_history
# import chat_logic # If chat logic is moved

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

def submit_interview_handler(interview_state):
    """Handles interview submission event."""
    result = interview_logic.submit_interview_logic(interview_state, TEXT_MODEL)
    ui_updates = apply_ui_updates(result["ui_updates"])

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

# --- Chat Module Functions ---
try:
    from login_module import chat as chat_module
    CHAT_MODULE_AVAILABLE = True
    print("Chat module imported successfully.")
except ImportError as e:
    print(f"Warning: Could not import chat module: {e}")
    CHAT_MODULE_AVAILABLE = False
    chat_module = None

# --- Gradio Interface ---
with gr.Blocks(title="PrepGenie - Mock Interviewer") as demo:
    # --- Remove user_state ---
    interview_state = gr.State({})
    # Create a new state to hold interview history for this session
    interview_history_state = gr.State([]) # List of past interviews for this session
    
    # Define the state variable that was causing the error
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

    # --- Main App Sections ---
    with gr.Column(visible=True) as main_app:
        with gr.Row():
            with gr.Column(scale=1):
                # Remove logout button
                # logout_btn = gr.Button("Logout")
            with gr.Column(scale=4):
                welcome_display = gr.Markdown("### Welcome, User!")

        with gr.Row():
            with gr.Column(scale=1):
                # Remove login/signup buttons
                # interview_btn = gr.Button("Mock Interview")
                # if CHAT_MODULE_AVAILABLE:
                #     chat_btn = gr.Button("Chat with Resume")
                # else:
                #     chat_btn = gr.Button("Chat with Resume (Unavailable)", interactive=False)
                # history_btn = gr.Button("My Interview History")

                # Replace with direct buttons
                mock_interview_btn = gr.Button("Mock Interview")
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
                    # Use the new history_state to load past interviews
                    load_history_btn = gr.Button("Load My Past Interviews")
                    history_output = gr.Textbox(label="Past Interviews", max_lines=30, interactive=False, visible=True)

        # Assign view variables for navigation
        interview_view = interview_selection
        chat_view = chat_selection
        history_view = history_selection

        # Navigation button listeners
        mock_interview_btn.click(fn=navigate_to_interview, inputs=None, outputs=[interview_view, chat_view, history_view])
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
        inputs=[interview_state],
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
    # This function will use the interview_history_state to display past interviews
    def load_user_history_local(interview_history_state):
        """Function to load and format interview history for display in the UI."""
        if not interview_history_state:
            return "No interview history found for this session."
        output_text = "**Your Recent Mock Interviews:**\n\n"
        for idx, record in enumerate(interview_history_state):
            timestamp = record.get('timestamp', 'Unknown Time')
            try:
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error parsing timestamp {timestamp}: {e}")
                formatted_time = timestamp

            roles = ", ".join(record.get('selected_roles', ['N/A']))
            avg_rating = record.get('average_rating', 'N/A')
            output_text += f"--- **Interview #{len(interview_history_state) - idx} ({formatted_time})** ---\n"
            output_text += f"**Roles Applied:** {roles}\n"
            output_text += f"**Average Rating:** {avg_rating:.2f}\n\n"

            interactions = record.get('interactions', {})
            if interactions:
                output_text += "**Interview Snippets:**\n"
                count = 0
                for q_key, a_val in list(interactions.items())[:3]:
                    q_display = q_key.split(':', 1)[1].strip() if ':' in q_key else q_key
                    a_display = a_val.split(':', 1)[1].strip() if ':' in a_val else a_val
                    output_text += f"- **Q:** {q_display[:100]}{'...' if len(q_display) > 100 else ''}\n"
                    output_text += f"  **A:** {a_display[:100]}{'...' if len(a_display) > 100 else ''}\n"
                    count += 1
                    if count >= 3:
                        break
                if len(interactions) > 3:
                    output_text += f"... (and {len(interactions) - 3} more questions)\n"
            else:
                 output_text += "**Details:** Not available.\n"
            output_text += "\n---\n\n"

        return output_text

    load_history_btn.click(fn=load_user_history_local, inputs=[interview_history_state], outputs=[history_output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")