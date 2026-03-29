# PrepGenie/interview_history.py
"""Session-based interview history with localStorage persistence."""

import json
import os
from datetime import datetime

# Local storage file path for persistence
HISTORY_FILE_PATH = os.path.join(os.path.dirname(__file__), "interview_history_data.json")

def load_history_from_file():
    """Load interview history from local JSON file."""
    try:
        if os.path.exists(HISTORY_FILE_PATH):
            with open(HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading history from file: {e}")
    return []

def save_history_to_file(history_list):
    """Save interview history to local JSON file."""
    try:
        with open(HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving history to file: {e}")
        return False

def save_interview_history(session_history, interview_data):
    """
    Appends a new interview record to the session history list.
    Also persists to local file for cross-session storage.
    """
    if session_history is None:
        session_history = []
    
    # Ensure interview_data has required fields
    if not isinstance(interview_data, dict):
        print("Invalid interview data format")
        return session_history
    
    # Add timestamp if not present
    if "timestamp" not in interview_data:
        interview_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Append to session history
    session_history.append(interview_data)
    
    # Persist to file
    save_history_to_file(session_history)
    
    print(f"Interview saved. Total interviews in history: {len(session_history)}")
    return session_history

def get_all_history():
    """Get all interview history from file."""
    return load_history_from_file()

def clear_history():
    """Clear all interview history."""
    try:
        if os.path.exists(HISTORY_FILE_PATH):
            os.remove(HISTORY_FILE_PATH)
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False

def delete_interview(session_history, index):
    """Delete a specific interview from history by index."""
    if not session_history or index < 0 or index >= len(session_history):
        return session_history
    
    session_history.pop(index)
    save_history_to_file(session_history)
    return session_history

def format_history_for_display(session_history):
    """Formats session history for display in the UI."""
    if not session_history:
        # Try loading from file
        session_history = load_history_from_file()
        if not session_history:
            return "No interview history found. Complete a mock interview to see it here!"

    output = "**Your Interview History:**\n\n"
    
    # Show most recent first
    for idx, record in enumerate(reversed(session_history)):
        roles = record.get("selected_roles", ["N/A"])
        if isinstance(roles, list):
            roles_str = ", ".join(roles)
        else:
            roles_str = str(roles)
        
        avg_rating = record.get("average_rating", 0.0)
        timestamp = record.get("timestamp", "Unknown time")

        output += f"### 📝 Interview #{len(session_history) - idx} ({timestamp})\n"
        output += f"**Roles:** {roles_str}\n"
        
        if isinstance(avg_rating, (int, float)):
            # Rating visualization
            stars = "⭐" * round(avg_rating / 2)
            output += f"**Average Rating:** {avg_rating:.1f}/10 {stars}\n\n"
        else:
            output += f"**Average Rating:** {avg_rating}\n\n"

        # Show Q&A snippets
        interactions = record.get("interactions", {})
        if interactions:
            output += "**Questions & Answers:**\n"
            count = 0
            for q_key, a_val in list(interactions.items()):
                q = q_key.split(":", 1)[1].strip() if ":" in q_key else q_key
                a = a_val.split(":", 1)[1].strip() if ":" in a_val else a_val
                
                # Truncate long text
                q_display = q[:100] + "..." if len(q) > 100 else q
                a_display = a[:150] + "..." if len(a) > 150 else a
                
                output += f"- **Q:** {q_display}\n"
                output += f"  **A:** {a_display}\n\n"
                
                count += 1
                if count >= 3:  # Show only first 3 Q&A
                    break
            
            if len(interactions) > 3:
                output += f"_... and {len(interactions) - 3} more questions_\n\n"
        else:
            output += "**Details:** Not available.\n\n"

        # Show metrics if available
        metrics_list = record.get("metrics_list", [])
        if metrics_list and len(metrics_list) > 0:
            last_metrics = metrics_list[-1] if isinstance(metrics_list, list) else metrics_list
            if isinstance(last_metrics, dict):
                output += "**Final Metrics:**\n"
                for skill, score in last_metrics.items():
                    if isinstance(score, (int, float)):
                        bar = "█" * int(score / 2) + "░" * (5 - int(score / 2))
                        output += f"- {skill}: {bar} ({score:.1f})\n"
                output += "\n"

        output += "---\n\n"

    return output


def get_history_statistics(session_history):
    """Calculate statistics from interview history."""
    if not session_history:
        session_history = load_history_from_file()
    
    if not session_history:
        return {
            "total_interviews": 0,
            "average_score": 0.0,
            "best_score": 0.0,
            "roles_taken": []
        }
    
    total = len(session_history)
    scores = []
    all_roles = set()
    
    for record in session_history:
        avg_rating = record.get("average_rating", 0.0)
        if isinstance(avg_rating, (int, float)):
            scores.append(avg_rating)
        
        roles = record.get("selected_roles", [])
        if isinstance(roles, list):
            all_roles.update(roles)
    
    return {
        "total_interviews": total,
        "average_score": sum(scores) / len(scores) if scores else 0.0,
        "best_score": max(scores) if scores else 0.0,
        "roles_taken": list(all_roles)
    }
