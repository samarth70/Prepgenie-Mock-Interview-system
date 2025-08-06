# PrepGenie_Gradio/interview_logic.py

# ... (existing imports) ...
import datetime # Add this import at the top
import interview_history # Import the new history module

# ... (existing functions: file_processing, getallinfo, etc.) ...

def finish_interview(all_questions_list, all_answers_list, all_feedback_list, resume_overview, selected_roles, user_id):
    """Gradio function to compile final results and save history."""
    if not all_questions_list or not all_answers_list:
        return "No interview data to display."

    # --- Compile Results for Display ---
    results = "**Interview Summary:**\n\n"
    for i, q in enumerate(all_questions_list):
        results += f"**Q{i+1}:** {q}\n"
        if i < len(all_answers_list):
            results += f"**Your Answer:** {all_answers_list[i]}\n"
        if i < len(all_feedback_list):
            results += f"**Feedback:** {all_feedback_list[i]}\n\n"
        else:
            results += "**Feedback:** Not available.\n\n"

    # --- Prepare Data for Saving ---
    # Only save if user is logged in (user_id is provided)
    if user_id:
        interview_summary_data = {
            "timestamp": datetime.datetime.now().isoformat(), # Add timestamp
            "resume_overview": resume_overview,
            "selected_roles": selected_roles, # Make sure this is passed
            "questions": all_questions_list,
            "answers": all_answers_list,
            "feedback": all_feedback_list,
            "summary": results # Save the formatted summary as well
        }
        # --- Save to Firestore ---
        success = interview_history.save_interview_history(user_id, interview_summary_data)
        if success:
            results += "\n---\n*Interview history saved successfully.*"
        else:
            results += "\n---\n*Failed to save interview history.*"
    else:
        results += "\n---\n*Not logged in. Interview history was not saved.*"

    return results

# ... (rest of the file remains mostly the same, but update the call to finish_interview) ...

# In the part of interview_logic.py where `finish_interview` is called from the Gradio interface:
# Update the call to pass the additional arguments:
# OLD:
# finish_interview_btn.click(
#     fn=finish_interview_wrapper,
#     inputs=[user_state],
#     outputs=[interview_results]
# )
# NEW (inside the wrapper function or by modifying the wrapper):
# You need to pass resume_overview, selected_roles, and user_id to the actual `finish_interview` function.
# This requires modifying the `finish_interview_wrapper` or the way it's called.
# Let's modify the wrapper function definition in app.py to pass these values.
