# PrepGenie/interview_history.py
import firebase_admin
from firebase_admin import firestore
import datetime
import json

# --- Firestore Client ---
# Assumes Firebase Admin is initialized in app.py
try:
    db = firestore.client()
    print("Firestore client for history initialized successfully.")
    FIRESTORE_AVAILABLE = True
except Exception as e:
    print(f"Error initializing Firestore client for history: {e}")
    db = None
    FIRESTORE_AVAILABLE = False

def save_interview_history(user_id, interview_data):
    """
    Saves the mock interview results to Firestore under the user's document.

    Args:
        user_id (str): The unique ID of the logged-in user (from Firebase Auth).
        interview_data (dict): A dictionary containing interview details.
            Expected structure:
            {
                "timestamp": str (ISO format datetime),
                "resume_overview": str,
                "selected_roles": list,
                "questions": list,
                "answers": list,
                "feedback": list,
                "interactions": dict,
                "metrics_list": list,
                "final_metrics": dict,
                "average_rating": float,
                "evaluation_report": str,
                # ... other relevant data ...
            }

    Returns:
        bool: True if successful, False otherwise.
    """
    if not FIRESTORE_AVAILABLE or not db:
        print("Firestore client not available. Cannot save history.")
        return False
    if not user_id:
        print("User ID is required to save history.")
        return False

    try:
        # Reference to the user's document in the 'users' collection
        user_ref = db.collection('users').document(user_id)

        # Add the interview data to a subcollection 'interview_history'
        history_ref = user_ref.collection('interview_history')

        # Add the data with an auto-generated ID
        history_ref.add(interview_data)

        print(f"Interview history saved for user {user_id}")
        return True
    except Exception as e:
        print(f"Error saving interview history for user {user_id}: {e}")
        return False

def load_interview_history(user_id, limit=5):
    """
    Loads the mock interview history for a specific user from Firestore.

    Args:
        user_id (str): The unique ID of the logged-in user.
        limit (int): The maximum number of recent interviews to retrieve.

    Returns:
        list: A list of dictionaries, each representing an interview record.
              Returns an empty list if no history is found or on error.
    """
    if not FIRESTORE_AVAILABLE or not db:
        print("Firestore client not available. Cannot load history.")
        return []
    if not user_id:
        print("User ID is required to load history.")
        return []

    try:
        # Reference to the user's interview history subcollection
        history_ref = db.collection('users').document(user_id).collection('interview_history')

        # Query the history, ordered by timestamp descending (most recent first), limited
        docs = history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()

        history_list = []
        for doc in docs:
            # Convert Firestore document to dictionary
            interview_record = doc.to_dict()
            # Add the document ID if needed (optional)
            # interview_record['doc_id'] = doc.id
            history_list.append(interview_record)

        print(f"Loaded {len(history_list)} interview records for user {user_id}")
        return history_list
    except Exception as e:
        print(f"Error loading interview history for user {user_id}: {e}")
        return []

# Example usage (for testing or understanding structure):
# Assuming you have a user ID and interview data after an interview session:
# user_uid = "some_user_id_from_firebase_auth"
# interview_summary_data = {
#     "timestamp": datetime.datetime.now().isoformat(),
#     "resume_overview": "Overview of the resume...",
#     "selected_roles": ["Software Engineer"],
#     "questions": ["Question 1?", "Question 2?"],
#     "answers": ["Answer 1", "Answer 2"],
#     "feedback": ["Feedback 1", "Feedback 2"],
#     # ... other fields ...
# }
# save_interview_history(user_uid, interview_summary_data)

# Load last 3 interviews
# past_interviews = load_interview_history(user_uid, limit=3)
# print(past_interviews)
