# PrepGenie/interview_history.py
"""Handles saving and loading interview history to/from Firestore."""

import firebase_admin
from firebase_admin import firestore
import datetime
import json

# --- Firestore Client ---
# Assumes Firebase Admin is initialized in app.py
try:
    db = firestore.client()
    print("Firestore client for history initialized successfully in interview_history.")
    FIRESTORE_AVAILABLE = True
except Exception as e:
    print(f"Error initializing Firestore client for history in interview_history: {e}")
    db = None
    FIRESTORE_AVAILABLE = False

def save_interview_history(user_id, interview_data):
    """
    Saves the mock interview results to Firestore under the user's document.
    """
    if not FIRESTORE_AVAILABLE or not db:
        print("Firestore client not available in interview_history. Cannot save history.")
        return False
    if not user_id:
        print("User ID is required in interview_history to save history.")
        return False

    try:
        user_ref = db.collection('users').document(user_id)
        history_ref = user_ref.collection('interview_history')
        history_ref.add(interview_data)
        print(f"Interview history saved for user {user_id} in interview_history")
        return True
    except Exception as e:
        print(f"Error saving interview history for user {user_id} in interview_history: {e}")
        return False

def load_interview_history(user_id, limit=5):
    """
    Loads the mock interview history for a specific user from Firestore.
    """
    if not FIRESTORE_AVAILABLE or not db:
        print("Firestore client not available in interview_history. Cannot load history.")
        return []
    if not user_id:
        print("User ID is required in interview_history to load history.")
        return []

    try:
        history_ref = db.collection('users').document(user_id).collection('interview_history')
        docs = history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()

        history_list = []
        for doc in docs:
            interview_record = doc.to_dict()
            history_list.append(interview_record)

        print(f"Loaded {len(history_list)} interview records for user {user_id} in interview_history")
        return history_list
    except Exception as e:
        print(f"Error loading interview history for user {user_id} in interview_history: {e}")
        return []

# --- History Loading Function for UI ---
def load_user_history(user_id_state):
    """Function to load and format interview history for display in the UI."""
    if not FIRESTORE_AVAILABLE:
        return "History feature is not available (Firestore not initialized)."
    if not user_id_state:
        return "Please log in to view your interview history."

    try:
        history_list = load_interview_history(user_id_state, limit=5)

        if not history_list:
            return "No interview history found."

        output_text = "**Your Recent Mock Interviews:**\n\n"
        for idx, record in enumerate(history_list):
            timestamp = record.get('timestamp', 'Unknown Time')
            try:
                if 'Z' in timestamp:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error parsing timestamp {timestamp} in load_user_history: {e}")
                formatted_time = timestamp

            roles = ", ".join(record.get('selected_roles', ['N/A']))
            avg_rating = record.get('average_rating', 'N/A')
            output_text += f"--- **Interview #{len(history_list) - idx} ({formatted_time})** ---\n"
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
    except Exception as e:
        error_msg = f"Error loading interview history in load_user_history: {str(e)}"
        print(error_msg)
        return error_msg