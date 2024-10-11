import streamlit as st
import PyPDF2
import os
import google.generativeai as genai
import tensorflow as tf
from transformers import BertTokenizer, TFBertModel
import numpy as np
import math
import speech_recognition as sr
import gtts
from streamlit.components.v1 import html
import time


from dotenv import load_dotenv
load_dotenv()
# no wide mode
st.set_page_config(page_title="Streamlit App", page_icon=":shark:", layout="centered", initial_sidebar_state="auto")

st.title("Mock Interview")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
text_model= genai.GenerativeModel("gemini-pro")

st.write("Welcome to the mock interview app. This app will help you prepare for your next interview. You can practice your responses to common interview questions and receive feedback on your responses.")

def getallinfo(data):
    text = f"{data} is not properly formatted for this model. Please try again and format the whole in a single paragraph covering all the information."
    response = text_model.generate_content(text)
    response.resolve()
    return response.text

def file_processing(uploaded_file):
    # upload pdf of resume
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


# Load the pre-trained BERT model
model = TFBertModel.from_pretrained("bert-base-uncased")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Function to preprocess text and get embeddings
def get_embedding(text):
    encoded_text = tokenizer(text, return_tensors="tf")
    output = model(encoded_text)
    embedding = output.last_hidden_state[:, 0, :]
    return embedding

# Function to generate feedback (replace with your logic)
def generate_feedback(question, answer):
    # Ensure correct variable name (case-sensitive)
    question_embedding = get_embedding(question)
    answer_embedding = get_embedding(answer)

    # Enable NumPy-like behavior for transpose
    tf.experimental.numpy.experimental_enable_numpy_behavior()

    # Calculate similarity score (cosine similarity)
    similarity_score = np.dot(question_embedding, answer_embedding.T) / (np.linalg.norm(question_embedding) * np.linalg.norm(answer_embedding))

    # Generate basic feedback based on similarity score
    corrected_string = f"Feedback: {np.array2string(similarity_score, precision=2)}"
    # print(corrected_string)
    return np.array2string(similarity_score, precision=2)

def generate_questions(roles, data):
    questions = []
    text = f"If this is not a resume then return text uploaded pdf is not a resume. this is a resume overview of the candidate. The candidate details are in {data}. The candidate has applied for the role of {roles}. Generate questions for the candidate based on the role applied and on the Resume of the candidate. Not always necceassary to ask only technical questions related to the role. Ask some personal questions too. Ask no additional questions. Dont categorize the questions. No of questions should range from 1-3 questions only. Ask one question at a time only."
    response = text_model.generate_content(text)
    response.resolve()
    # slipt the response into questions either by \n or by ? or by . or by !
    questions = response.text.split("\n")
    
    return questions


def generate_overall_feedback(data, percent, answer, questions):
    percent = float(percent)
    if percent > 0.5:
        test = f"Here is the overview of the candidate {data}. In the interview the questions asked were {questions}. The candidate has answered the questions as follows: {answer}. Based on the answers provided, the candidate has scored {percent}. The candidate has done well in the interview. The candidate has answered the questions well and has a good understanding of the concepts. The candidate has scored well in the interview. The candidate has scored {percent} in the interview. The candidate has done well in the interview. The candidate has answered the questions well and has a good understanding of the concepts. The candidate has scored well in the interview. The candidate has scored {percent} in the interview."
    else:
        test = f"Here is the overview of the candidate {data}. In the interview the questions asked were {questions}. The candidate has answered the questions as follows: {answer}. Based on the answers provided, the candidate has scored {percent}. tell the average percent and rate the interview out of 10. Give the feedback to the candidate about the interview and areas of improvements. While talking to candidate always take their name. give the candidate various ways to improve their interview skills. The candidate needs to know about where they are going wrong and the solution to the issues they are having during the interview."
    # st.write(test)
    response = text_model.generate_content(test)
    response.resolve()
    return response.text

def store_audio_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.error("Speak now")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            # st.success(f"Your Answer: {text}")
            return text
        except:
            st.error("Sorry could not recognize your voice")
            return " "
        
uploaded_file = st.file_uploader("Upload your resume in simple Document Format", type=["pdf"])
roles_applied = []
if uploaded_file is not None:
    st.write("File uploaded successfully!")
    data = file_processing(uploaded_file)
    # st.write(data)
    # st.write(getallinfo(data))
    updated_data = getallinfo(data)
    # st.write(updated_data)
    roles = st.multiselect("Select your job role:", ["Data Scientist", "Software Engineer", "Product Manager", "Data Analyst", "Business Analyst"])
    if roles:
        roles_applied.append(roles)
        st.write(f"Selected roles: {roles}")
        questions = generate_questions(roles, updated_data)
        feedback = []
        answers = []
        ans = ""
        interaction = {}
        for i in range(len(questions)):
            st.write(questions[i])
            ans = store_audio_text()
            st.success(ans)
            answers.append(ans)
            percent = 0.0
            percent = generate_feedback(questions[i], answers[i])
            print(percent)
            feedback.append(generate_overall_feedback(data, percent, answers[i], questions[i]))
            interaction[questions[i]] = answers[i]
        if st.button("Submit"):
            for i in range(len(questions)):
                st.write(interaction[questions[i]])
                st.write(feedback[i])
                # st.write("Thank you for your responses!")
