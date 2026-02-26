
# PrepGenie/interview_logic.py
"""Core logic for the mock interview process."""

import os
import tempfile
import PyPDF2
import google.generativeai as genai
from transformers import BertTokenizer, TFBertModel
import numpy as np
import speech_recognition as sr
import soundfile as sf
import json
import matplotlib.pyplot as plt
import io
import re
import time

# --- Configuration ---
# Note: text_model is passed in from app.py to avoid circular imports or global state issues.

# --- BERT Model Loading ---
try:
    model = TFBertModel.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    BERT_AVAILABLE = True
    print("BERT model loaded successfully in interview_logic.")
except Exception as e:
    print(f"Warning: Could not load BERT model/tokenizer in interview_logic: {e}")
    BERT_AVAILABLE = False
    model = None
    tokenizer = None


def safe_generate_content(text_model, prompt, fallback_message="Service temporarily unavailable. Please try again later."):
    """
    Wrapper for Gemini API calls that handles quota/rate limit errors gracefully.
    Returns a tuple: (success: bool, result_or_error_message: str)
    Includes exponential backoff for rate limits.
    """
    max_retries = 3
    initial_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = text_model.generate_content(prompt)
            response.resolve()
            return True, response.text
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for quota/rate limit errors
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                print(f"Quota/Rate limit error (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return False, "⚠️ API quota exceeded. Please wait a few minutes and try again, or check your API plan."
            
            elif "403" in error_str or "permission" in error_str:
                print(f"Permission error: {e}")
                return False, "⚠️ API access denied. Please check your API key configuration."
            
            else:
                print(f"API error: {e}")
                # For non-retriable errors, return immediately
                return False, f"⚠️ Service error: {fallback_message}"
    
    # Fallback if all retries exhausted
    return False, "⚠️ Service unavailable after multiple attempts. Please try again later."


# --- Core Logic Functions ---

def getallinfo(data, text_model):
    """Processes raw resume text into a structured overview."""
    if not data or not data.strip():
        return "No data provided or data is empty."
    
    text = f"""{data} is given by the user. Make sure you are getting the details like name, experience,
education, skills of the user like in a resume. If the details are not provided return: not a resume.
If details are provided then please try again and format the whole in a single paragraph covering all the information. """
    
    success, result = safe_generate_content(text_model, text, "Could not process resume data.")
    if not success:
        return result  # Returns the warning message
    return result


def file_processing(pdf_file_path):
    """Processes the uploaded PDF file given its path."""
    if not pdf_file_path or not os.path.exists(pdf_file_path):
        print(f"File path is invalid or file does not exist: {pdf_file_path}")
        return ""
    try:
        print(f"Attempting to process file at path: {pdf_file_path}")
        with open(pdf_file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        return text
    except FileNotFoundError:
        error_msg = f"File not found at path: {pdf_file_path}"
        print(error_msg)
        return ""
    except PyPDF2.errors.PdfReadError as e:
        error_msg = f"Error reading PDF file {pdf_file_path}: {e}"
        print(error_msg)
        return ""
    except Exception as e:
        error_msg = f"Unexpected error processing PDF from path {pdf_file_path}: {e}"
        print(error_msg)
        return ""


def get_embedding(text):
    """Generates BERT embedding for a given text."""
    if not text or not text.strip():
         return np.zeros((1, 768))
    if not BERT_AVAILABLE or not model or not tokenizer:
        print("BERT model not available for embedding in interview_logic.")
        return np.zeros((1, 768))
    try:
        encoded_text = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        output = model(encoded_text)
        embedding = output.last_hidden_state[:, 0, :]
        return embedding.numpy()
    except Exception as e:
        print(f"Error getting embedding in interview_logic: {e}")
        return np.zeros((1, 768))


def generate_feedback(question, answer):
    """Calculates similarity score between question and answer."""
    if not question or not question.strip() or not answer or not answer.strip():
        return "0.00"
    try:
        question_embedding = get_embedding(question)
        answer_embedding = get_embedding(answer)
        q_emb = np.squeeze(question_embedding)
        a_emb = np.squeeze(answer_embedding)
        dot_product = np.dot(q_emb, a_emb)
        norms = np.linalg.norm(q_emb) * np.linalg.norm(a_emb)
        if norms == 0:
            similarity_score = 0.0
        else:
            similarity_score = dot_product / norms
        return f"{similarity_score:.2f}"
    except Exception as e:
        print(f"Error generating feedback in interview_logic: {e}")
        return "0.00"


def generate_questions(roles, data, text_model):
    """Generates 5 interview questions based on resume and roles."""
    default_questions = [
        "Could you please introduce yourself based on your resume?",
        "What are your key technical skills relevant to this role?",
        "Describe a challenging project you've worked on and how you resolved it.",
        "How do you prioritize tasks when working under tight deadlines?",
        "Where do you see yourself professionally in the next 3 to 5 years?"
    ]

    if not roles or (isinstance(roles, list) and not any(roles)) or not data or not data.strip():
        return default_questions

    if isinstance(roles, list):
        roles_str = ", ".join(roles)
    else:
        roles_str = str(roles)

    text = f"""You are an experienced interviewer conducting a mock interview.
The candidate's resume overview is: {data}
The candidate has applied for the role of: {roles_str}

Generate EXACTLY 5 interview questions for this candidate. Follow these rules strictly:
1. Output ONLY the 5 questions, one per line, numbered 1 to 5.
2. Do NOT include any introduction, explanation, category labels, or extra text — just the questions.
3. Each question must end with a question mark.
4. Mix the questions across these areas:
   - 1 introduction/background question based on their resume
   - 1 technical question relevant to the role of {roles_str}
   - 1 behavioral question (teamwork, collaboration, or conflict resolution)
   - 1 problem-solving or situational question
   - 1 personal/career goals question
5. Keep questions polite, clear, and conversational.
6. Tailor the questions specifically to the candidate's background and the role applied for.

Example format (do not copy these, generate your own):
1. Can you walk us through your experience with data analysis tools mentioned in your resume?
2. How would you approach building a dashboard from scratch for a non-technical stakeholder?
3. Tell me about a time you had to collaborate with a difficult team member. How did you handle it?
4. If given an ambiguous dataset with missing values, what steps would you take to analyze it?
5. Where do you see your career heading in the next 3 to 5 years?"""

    success, result = safe_generate_content(text_model, text, "Could not generate questions.")
    
    if not success:
        print(f"Using fallback questions due to: {result}")
        # Return default questions with the warning as the first item so user sees it
        return [f"⚠️ {result}"] + default_questions[:4]

    # Parse the successful result
    questions_text = result.strip()
    questions = re.findall(r'^\d+[\.\)]\s*(.+)', questions_text, re.MULTILINE)
    questions = [q.strip() for q in questions if q.strip()]

    # Fallback: split by newline if numbered parsing fails
    if len(questions) < 3:
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and '?' in q]

    print(f"Generated {len(questions)} questions: {questions}")

    # Pad with defaults if AI returned fewer than 5
    while len(questions) < 5:
        questions.append(default_questions[len(questions)])

    return questions[:5]


def generate_overall_feedback(data, percent, answer, question, text_model):
    """Generates overall feedback for an answer."""
    if not data or not data.strip() or not answer or not answer.strip() or not question or not question.strip():
        return "Unable to generate feedback due to missing information."
    
    if isinstance(percent, float):
        percent_str = f"{percent:.2f}"
    else:
        percent_str = str(percent)
    
    prompt = f"""As an interviewer, provide concise feedback (max 150 words) for candidate {data}.
Questions asked: {question}
Candidate's answers: {answer}
Score: {percent_str}
Feedback should include:
1. Overall performance assessment (2-3 sentences)
2. Key strengths (2-3 points)
3. Areas for improvement (2-3 points)
Be honest and constructive. Do not mention the exact score, but rate the candidate out of 10 based on their answers."""
    
    success, result = safe_generate_content(text_model, prompt, "Could not generate feedback.")
    if not success:
        return f"Feedback unavailable: {result}"
    
    return result


def generate_metrics(data, answer, question, text_model):
    """Generates skill metrics for an answer."""
    default_metrics = {
        "Communication skills": 0.0,
        "Teamwork and collaboration": 0.0,
        "Problem-solving and critical thinking": 0.0,
        "Time management and organization": 0.0,
        "Adaptability and resilience": 0.0
    }
    
    if not data or not data.strip() or not answer or not answer.strip() or not question or not question.strip():
        return default_metrics
    
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
    
    success, result = safe_generate_content(text_model, text, "Could not generate metrics.")
    if not success:
        print(f"Metrics generation failed: {result}")
        return default_metrics

    metrics = {}
    metrics_text = result.strip()
    for line in metrics_text.split('\n'):
        if ':' in line:
            key, value_str = line.split(':', 1)
            key = key.strip()
            try:
                value_clean = value_str.strip().split()[0]
                value = float(value_clean)
                metrics[key] = value
            except (ValueError, IndexError):
                metrics[key] = 0.0
    
    # Ensure all expected keys exist
    expected_metrics = [
        "Communication skills", "Teamwork and collaboration",
        "Problem-solving and critical thinking", "Time management and organization",
        "Adaptability and resilience"
    ]
    for m in expected_metrics:
        if m not in metrics:
            metrics[m] = 0.0
    
    return metrics


def getmetrics(interaction, resume, text_model):
    """Gets overall metrics from AI based on interaction."""
    interaction_text = "\n".join([f"{q}: {a}" for q, a in interaction.items()])
    text = f"""This is the user's resume: {resume}.
And here is the interaction of the interview: {interaction_text}.
Please evaluate the interview based on the interaction and the resume.
Rate me the following metrics on a scale of 1 to 10. 1 being the lowest and 10 being the highest.
Communication skills, Teamwork and collaboration, Problem-solving and critical thinking,
Time management and organization, Adaptability and resilience. Just give the ratings for the metrics.
I do not need the feedback. Just the ratings in the format:
Communication skills: X
Teamwork and collaboration: Y
Problem-solving and critical thinking: Z
Time management and organization: A
Adaptability and resilience: B
"""
    success, result = safe_generate_content(text_model, text, "Could not fetch final metrics.")
    if not success:
        print(f"Final metrics fetch failed: {result}")
        return "" # Return empty string, parser will handle it
    return result


def parse_metrics(metric_text):
    """Parses raw metric text into a dictionary."""
    metrics = {
        "Communication skills": 0,
        "Teamwork and collaboration": 0,
        "Problem-solving and critical thinking": 0,
        "Time management and organization": 0,
        "Adaptability and resilience": 0
    }
    if not metric_text:
        return metrics
    for line in metric_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value and value not in ['N/A', 'nan'] and not value.isspace():
                try:
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        metrics[key] = int(float(numbers[0]))
                    else:
                        metrics[key] = 0
                except (ValueError, IndexError, TypeError):
                    print(f"Warning: Could not parse metric value '{value}' for '{key}' in interview_logic. Setting to 0.")
                    metrics[key] = 0
            else:
                metrics[key] = 0
    return metrics


def create_metrics_chart(metrics_dict):
    """Creates a pie chart image from metrics."""
    try:
        labels = list(metrics_dict.keys())
        sizes = list(metrics_dict.values())
        if not any(sizes):
             fig, ax = plt.subplots(figsize=(4, 4))
             ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
             ax.axis('off')
        else:
            fig, ax = plt.subplots(figsize=(6, 6))
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        print(f"Error creating chart in interview_logic: {e}")
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.text(0.5, 0.5, 'Chart Error', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf


def generate_evaluation_report(metrics_data, average_rating, feedback_list, interaction_dict):
    """Generates a formatted evaluation report."""
    try:
        report_lines = [f"## Hey Candidate, here is your interview evaluation:\n"]
        report_lines.append("### Skill Ratings:\n")
        for metric, rating in metrics_data.items():
            report_lines.append(f"* **{metric}:** {rating}/10\n")
        report_lines.append(f"\n### Overall Average Rating: {average_rating:.2f}/10\n")
        report_lines.append("### Feedback Summary:\n")
        if feedback_list:
            last_feedback = feedback_list[-1] if feedback_list else "No feedback available."
            report_lines.append(last_feedback)
        else:
             report_lines.append("No detailed feedback was generated.")
        report_lines.append("\n### Interview Interaction:\n")
        if interaction_dict:
            for q, a in interaction_dict.items():
                report_lines.append(f"* **{q}**\n  {a}\n")
        else:
             report_lines.append("Interaction data not available.")
        improvement_content = """
### Areas for Improvement:
*   **Communication:** Focus on clarity, conciseness, and tailoring your responses to the audience. Use examples and evidence to support your points.
*   **Teamwork and collaboration:** Highlight your teamwork skills through specific examples and demonstrate your ability to work effectively with others.
*   **Problem-solving and critical thinking:** Clearly explain your problem-solving approach and thought process. Show your ability to analyze information and arrive at logical solutions.
*   **Time management and organization:** Emphasize your ability to manage time effectively and stay organized during challenging situations.
*   **Adaptability and resilience:** Demonstrate your ability to adapt to new situations and overcome challenges. Share examples of how you have handled unexpected situations or setbacks in the past.
**Remember:** This is just a starting point. Customize the feedback based on the specific strengths and weaknesses identified in your interview.
"""
        report_lines.append(improvement_content)
        report_text = "".join(report_lines)
        return report_text
    except Exception as e:
        error_msg = f"Error generating evaluation report in interview_logic: {e}"
        print(error_msg)
        return error_msg


# --- Interview State Management Functions ---

def process_resume_logic(file_obj):
    """Handles resume upload and processing logic."""
    print(f"process_resume_logic called with: {file_obj}")
    if not file_obj:
        return {
            "status": "Please upload a PDF resume.",
            "processed_data": "",
            "ui_updates": {
                "role_selection": "gr_hide", "start_interview_btn": "gr_hide",
                "question_display": "gr_hide", "answer_instructions": "gr_hide",
                "audio_input": "gr_hide", "submit_answer_btn": "gr_hide",
                "next_question_btn": "gr_hide", "submit_interview_btn": "gr_hide",
                "answer_display": "gr_hide", "feedback_display": "gr_hide",
                "metrics_display": "gr_hide"
            }
        }
    try:
        if hasattr(file_obj, 'name'):
            file_path = file_obj.name
        else:
            file_path = str(file_obj)
        print(f"File path to process: {file_path}")
        raw_text = file_processing(file_path)
        print(f"Raw text extracted (length: {len(raw_text) if raw_text else 0})")
        if not raw_text or not raw_text.strip():
             print("Failed to extract text or text is empty.")
             return {
                "status": "Could not extract text from the PDF.",
                "processed_data": "",
                "ui_updates": {
                    "role_selection": "gr_hide", "start_interview_btn": "gr_hide",
                    "question_display": "gr_hide", "answer_instructions": "gr_hide",
                    "audio_input": "gr_hide", "submit_answer_btn": "gr_hide",
                    "next_question_btn": "gr_hide", "submit_interview_btn": "gr_hide",
                    "answer_display": "gr_hide", "feedback_display": "gr_hide",
                    "metrics_display": "gr_hide"
                }
             }
        # processed_data = getallinfo(raw_text, text_model) # text_model needs to be passed
        # Placeholder, actual call in app.py
        return {
            "status": f"File processed successfully!",
            "processed_data": raw_text, # Return raw text, let app.py call getallinfo
            "ui_updates": {
                "role_selection": "gr_show", "start_interview_btn": "gr_show",
                "question_display": "gr_hide", "answer_instructions": "gr_hide",
                "audio_input": "gr_hide", "submit_answer_btn": "gr_hide",
                "next_question_btn": "gr_hide", "submit_interview_btn": "gr_hide",
                "answer_display": "gr_hide", "feedback_display": "gr_hide",
                "metrics_display": "gr_hide"
            }
        }
    except Exception as e:
        error_msg = f"Error processing file in interview_logic: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "status": error_msg,
            "processed_data": "",
            "ui_updates": {
                "role_selection": "gr_hide", "start_interview_btn": "gr_hide",
                "question_display": "gr_hide", "answer_instructions": "gr_hide",
                "audio_input": "gr_hide", "submit_answer_btn": "gr_hide",
                "next_question_btn": "gr_hide", "submit_interview_btn": "gr_hide",
                "answer_display": "gr_hide", "feedback_display": "gr_hide",
                "metrics_display": "gr_hide"
            }
        }


def start_interview_logic(roles, processed_resume_data, text_model):
    """Starts the interview process logic."""
    if not roles or (isinstance(roles, list) and not any(roles)) or not processed_resume_data or not processed_resume_data.strip():
        return {
            "status": "Please select a role and ensure resume is processed.",
            "initial_question": "",
            "all_questions": "",
            "interview_state": {},
            "ui_updates": {
                "audio_input": "gr_show",
                "submit_answer_btn": "gr_show",
                "next_question_btn": "gr_hide",
                "submit_interview_btn": "gr_hide",
                "feedback_display": "gr_hide",
                "metrics_display": "gr_hide",
                "question_display": "gr_show",
                "answer_instructions": "gr_show"
            }
        }
    try:
        questions = generate_questions(roles, processed_resume_data, text_model)
        default_questions = [
            "Could you please introduce yourself based on your resume?",
            "What are your key technical skills relevant to this role?",
            "Describe a challenging project you've worked on and how you handled it.",
            "Where do you see yourself in 5 years?",
            "Do you have any questions for us?"
        ]
        while len(questions) < 5:
            questions.append(default_questions[len(questions)])
        questions = questions[:5]  # cap at 5
        
        # Display all 5 questions at once
        all_questions_text = "\n\n".join([f"**Question {i+1}:** {q}" for i, q in enumerate(questions)])
        initial_question = questions[0]
        
        interview_state = {
            "questions": questions,
            "current_q_index": 0,
            "answers": [],
            "feedback": [],
            "interactions": {},
            "metrics_list": [],
            "resume_data": processed_resume_data,
            "selected_roles": roles
        }
        return {
            "status": "Interview started. All 5 questions are displayed below. Answer them one by one.",
            "initial_question": all_questions_text,  # Show all questions
            "all_questions": all_questions_text,
            "interview_state": interview_state,
            "ui_updates": {
                "audio_input": "gr_show", 
                "submit_answer_btn": "gr_show", 
                "next_question_btn": "gr_hide",
                "submit_interview_btn": "gr_hide", 
                "feedback_display": "gr_hide", 
                "metrics_display": "gr_hide",
                "question_display": "gr_show", 
                "answer_instructions": "gr_show"
            }
        }
    except Exception as e:
        error_msg = f"Error starting interview in interview_logic: {str(e)}"
        print(error_msg)
        return {
            "status": error_msg,
            "initial_question": "",
            "all_questions": "",
            "interview_state": {},
            "ui_updates": {
                "audio_input": "gr_hide", 
                "submit_answer_btn": "gr_hide", 
                "next_question_btn": "gr_hide",
                "submit_interview_btn": "gr_hide", 
                "feedback_display": "gr_hide", 
                "metrics_display": "gr_hide",
                "question_display": "gr_hide", 
                "answer_instructions": "gr_hide"
            }
        }


def submit_answer_logic(audio, interview_state, text_model):
    """Handles submitting an answer via audio logic."""
    if not audio or not interview_state:
        return {
            "status": "No audio recorded or interview not started.",
            "answer_text": "",
            "interview_state": interview_state,
            "feedback_text": "",
            "metrics": {},
            "ui_updates": {
                "feedback_display": "gr_hide", "metrics_display": "gr_hide",
                "audio_input": "gr_show", "submit_answer_btn": "gr_show", "next_question_btn": "gr_hide",
                "submit_interview_btn": "gr_hide", "question_display": "gr_show", "answer_instructions": "gr_show"
            }
        }
    try:
        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, "recorded_audio.wav")
        sample_rate, audio_data = audio
        sf.write(audio_file_path, audio_data, sample_rate)
        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data_sr = r.record(source)
        answer_text = r.recognize_google(audio_data_sr)
        print(f"Recognized Answer: {answer_text}")
        os.remove(audio_file_path)
        os.rmdir(temp_dir)
        interview_state["answers"].append(answer_text)
        current_q_index = interview_state["current_q_index"]
        current_question = interview_state["questions"][current_q_index]
        interview_state["interactions"][f"Q{current_q_index + 1}: {current_question}"] = f"A{current_q_index + 1}: {answer_text}"
        percent_str = generate_feedback(current_question, answer_text)
        try:
            percent = float(percent_str)
        except ValueError:
            percent = 0.0
        feedback_text = generate_overall_feedback(interview_state["resume_data"], percent_str, answer_text, current_question, text_model)
        interview_state["feedback"].append(feedback_text)
        metrics = generate_metrics(interview_state["resume_data"], answer_text, current_question, text_model)
        interview_state["metrics_list"].append(metrics)
        interview_state["current_q_index"] += 1
        total_questions = len(interview_state["questions"])
        is_last_question = interview_state["current_q_index"] >= total_questions
        
        return {
            "status": f"Answer submitted! {'All questions answered — click Submit Interview.' if is_last_question else 'Click Next Question to continue.'}",
            "answer_text": answer_text,
            "interview_state": interview_state,
            "feedback_text": feedback_text,
            "metrics": metrics,
            "ui_updates": {
                "feedback_display": "gr_show_and_update",
                "metrics_display": "gr_show_and_update",
                "audio_input": "gr_hide",
                "submit_answer_btn": "gr_hide",
                "next_question_btn": "gr_hide" if is_last_question else "gr_show",
                "submit_interview_btn": "gr_show" if is_last_question else "gr_hide",
                "question_display": "gr_show",
                "answer_instructions": "gr_show"
            }
        }
    except Exception as e:
        print(f"Error processing audio answer in interview_logic: {e}")
        return {
            "status": "Error processing audio. Please try again.",
            "answer_text": "",
            "interview_state": interview_state,
            "feedback_text": "",
            "metrics": {},
            "ui_updates": {
                "feedback_display": "gr_hide", "metrics_display": "gr_hide",
                "audio_input": "gr_show", "submit_answer_btn": "gr_show", "next_question_btn": "gr_show",
                "submit_interview_btn": "gr_hide", "question_display": "gr_show", "answer_instructions": "gr_show"
            }
        }


def next_question_logic(interview_state):
    """Moves to the next question or ends the interview logic."""
    if not interview_state:
        return {
            "status": "Interview not started.",
            "next_q": "",
            "interview_state": interview_state,
            "ui_updates": {
                "audio_input": "gr_show", "submit_answer_btn": "gr_show", "next_question_btn": "gr_hide",
                "feedback_display": "gr_hide", "metrics_display": "gr_hide", "submit_interview_btn": "gr_hide",
                "question_display": "gr_show", "answer_instructions": "gr_show",
                "answer_display": "gr_clear", "metrics_display_clear": "gr_clear"
            }
        }
    current_q_index = interview_state["current_q_index"]
    total_questions = len(interview_state["questions"])
    if current_q_index < total_questions:
        next_q = interview_state["questions"][current_q_index]
        return {
            "status": f"Question {current_q_index + 1}/{total_questions}",
            "next_q": next_q,
            "interview_state": interview_state,
            "ui_updates": {
                "audio_input": "gr_show",
                "submit_answer_btn": "gr_show",
                "next_question_btn": "gr_hide",
                "feedback_display": "gr_hide",
                "metrics_display": "gr_hide",
                "submit_interview_btn": "gr_hide",
                "question_display": "gr_show",
                "answer_instructions": "gr_show",
                "answer_display": "gr_clear",
                "metrics_display_clear": "gr_clear"
            }
        }
    else:
        return {
            "status": "Interview completed! Click 'Submit Interview' to see your evaluation.",
            "next_q": "Interview Finished",
            "interview_state": interview_state,
            "ui_updates": {
                "audio_input": "gr_hide", "submit_answer_btn": "gr_hide", "next_question_btn": "gr_hide",
                "feedback_display": "gr_hide", "metrics_display": "gr_hide", "submit_interview_btn": "gr_show",
                "question_display": "gr_show", "answer_instructions": "gr_hide",
                "answer_display": "gr_clear", "metrics_display_clear": "gr_clear"
            }
        }


def submit_interview_logic(interview_state, text_model):
    """Handles final submission, triggers evaluation, prepares results logic."""
    if not interview_state or not isinstance(interview_state, dict):
        return {
            "status": "Interview state is missing or invalid.",
            "interview_state": interview_state,
            "report_text": "",
            "chart_buffer": None,
            "ui_updates": {
                "evaluation_report_display": "gr_hide", "evaluation_chart_display": "gr_hide"
            }
        }
    try:
        print("Interview submitted for evaluation in interview_logic.")
        interactions = interview_state.get("interactions", {})
        resume_data = interview_state.get("resume_data", "")
        feedback_list = interview_state.get("feedback", [])
        metrics_history = interview_state.get("metrics_list", [])

        if not interactions:
            error_msg = "No interview interactions found to evaluate."
            print(error_msg)
            return {
                "status": error_msg,
                "interview_state": interview_state,
                "report_text": "",
                "chart_buffer": None,
                "ui_updates": {
                    "evaluation_report_display": "gr_hide", "evaluation_chart_display": "gr_hide"
                }
            }
        raw_metrics_text = getmetrics(interactions, resume_data, text_model)
        print(f"Raw Metrics Text:\n{raw_metrics_text}")
        final_metrics = parse_metrics(raw_metrics_text)
        print(f"Parsed Metrics: {final_metrics}")
        if final_metrics:
            average_rating = sum(final_metrics.values()) / len(final_metrics)
        else:
            average_rating = 0.0
        report_text = generate_evaluation_report(final_metrics, average_rating, feedback_list, interactions)
        print("Evaluation report generated in interview_logic.")
        chart_buffer = create_metrics_chart(final_metrics)
        print("Evaluation chart generated in interview_logic.")

        return {
            "status": "Evaluation Complete! See your results below.",
            "interview_state": interview_state,
            "report_text": report_text,
            "chart_buffer": chart_buffer,
            "ui_updates": {
                "evaluation_report_display": "gr_show_and_update", "evaluation_chart_display": "gr_show_and_update"
            }
        }
    except Exception as e:
        error_msg = f"Error during evaluation submission in interview_logic: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "status": error_msg,
            "interview_state": interview_state,
            "report_text": error_msg,
            "chart_buffer": None,
            "ui_updates": {
                "evaluation_report_display": "gr_show_and_update_error", "evaluation_chart_display": "gr_hide"
            }
        }