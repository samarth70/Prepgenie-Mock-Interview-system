import streamlit as st
from firebase_admin import auth
import PyPDF2
import os
import google.generativeai as genai
import tensorflow as tf
from transformers import BertTokenizer, TFBertModel
import numpy as np
import math
import speech_recognition as sr
import evaluate
import pyttsx3
from gtts import gTTS
from io import BytesIO
import pygame

from dotenv import load_dotenv
load_dotenv()
st.session_state.interaction = {}
st.session_state.feedback = []
st.session_state.resume = ""
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
text_model= genai.GenerativeModel("gemini-pro")
# Load the pre-trained BERT model
model = TFBertModel.from_pretrained("bert-base-uncased")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")


def getallinfo(data):
    text = f"{data} is given by the user. Make sure you are getting the details like name, experience, education, skills of the user like in a resume. If the details are not provided return: not a resume. If details are provided then please try again and format the whole in a single paragraph covering all the information. "
    response = text_model.generate_content(text)
    # st.write(response)
    response.resolve()
    return response.text

def file_processing(uploaded_file):
    # upload pdf of resume
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

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
    text = f"If this is not a resume then return text uploaded pdf is not a resume. this is a resume overview of the candidate. The candidate details are in {data}. The candidate has applied for the role of {roles}. Generate questions for the candidate based on the role applied and on the Resume of the candidate. Not always necceassary to ask only technical questions related to the role but the logic of question should include the job applied for because there might be some deep tech questions which the user might not know. Ask some personal questions too. Ask no additional questions. Dont categorize the questions. ask 2 questions only. directly ask the questions not anything else. Also ask the questions in a polite way. Ask the questions in a way that the candidate can understand the question. and make sure the questions are related to these metrics: Communication skills, Teamwork and collaboration, Problem-solving and critical thinking, Time management and organization, Adaptability and resilience. dont tell anything else just give me the questions. if there is a limit in no of questions, ask or try questions that covers all need."
    # if needed ask multiple questions. but ask one question at a time only and note more than 7. 
    response = text_model.generate_content(text)
    response.resolve()
    # slipt the response into questions either by \n or by ? or by . or by !
    questions = response.text.split("\n")
    
    return questions


def generate_overall_feedback(data, percent, answer, questions):
    test = f"Here is the overview of the candidate {data}. Be just like a interviewer you need to give a feedback about the process. In the interview the questions asked were {questions}. The candidate has answered the questions as follows: {answer}. Based on the answers provided, the candidate has scored {percent}. dont tell the percent of the candidate, but rate them on 10 based on their answers. Make sure the answers are making sense and dont say over good on feedback you are interviewer, but make sure you are talking point to point. If the logic behind the answer is not provided in a good way, directly tell the candidate the point to point answer was not provided. then tell the important mistakes candidate made and how to improve it.The candidate has scored {percent} in the interview. If the candidate has answered the questions well and has a good understanding of the concepts. The candidate has scored well in the interview. If the answers are not good then tell the candidate has to improve alot with the answers. Give me 2 paragraphs of feedback. 1st para about how was the interview and 2nd para about how the candidate can improve. dont fake. just write about what answer was given by the candidate. dont write anything else. just the feedback."
    # st.write(test)
    response = text_model.generate_content(test)
    response.resolve()
    return response.text

def store_audio_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # 2 columns
        col1, col2 = st.columns([10,10])
        with col1:
            st.error("Speak now")
        # with col2:
        #     st.button("stop recording", on_click=stop_recording)
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            # st.success(f"Your Answer: {text}")
            return text
        except:
            st.error("Sorry could not recognize your voice")
            return " "
        
def stop_recording():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        st.error("Recording stopped")
        return    


def speak(text, language='en'):
    mp3_fo = BytesIO()
    tts = gTTS(text=text, lang=language)
    tts.write_to_fp(mp3_fo)
    return mp3_fo

    
        
def generate_metrics(data, answer, question):
    metrics = []
    text = f"Here is the overview of the candidate {data}. In the interview the question asked was {question}. The candidate has answered the question as follows: {answer}. Based on the answers provided, give me the metrics related to: Communication skills, Teamwork and collaboration, Problem-solving and critical thinking, Time management and organization, Adaptability and resilience. give me the metrics for each of the above mentioned skills. just give me the ratings out of 10 for each of the skills nothing else. if there is nothing then give minimum 4. dont even write /10. just give me the numbers"
    response = text_model.generate_content(text)
    response.resolve()
    metrics.append(response.text)
    return metrics
  

def user_interview():
    ttts = pyttsx3.init()
    st.title('Welcome to Mock Interview ' + st.session_state["username"] + '\n :violet[Good luck]')


    st.write("Welcome to the mock interview app. This app will help you prepare for your next interview. You can practice your responses to common interview questions and receive feedback on your responses.")

    # check if login
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    # if user is not logged in then go to login page
    if st.session_state.username == '':
        st.title('Welcome to your :violet[Mock Interview]')
        st.write('This is a mock interview app')
        st.write('Here you can give a mock interview and get feedback on your performance.')
        st.subheader('Please login to continue')
        st.subheader('You can login from the sidebar')
        return
    
    else:   
        # logged in
        pygame.init()
        pygame.mixer.init()

        uploaded_file = st.file_uploader("Upload your resume in simple Document Format", type=["pdf"])
        roles_applied = []
        if uploaded_file is not None:
            st.write("File uploaded successfully!")
            data = file_processing(uploaded_file)

            # st.write(data)
            # st.write(getallinfo(data))
            updated_data = getallinfo(data)
            st.session_state.resume = updated_data
            # if the data contains not in the response then return the response
            # # st.write(updated_data)
            # if "not" in updated_data:
            #     return "The uploaded pdf is not a resume. Please upload a resume to continue."
            #     st.stop()
            # st.write(updated_data)
            roles = st.multiselect("Select your job role:", ["Data Scientist", "Software Engineer", "Product Manager", "Data Analyst", "Business Analyst"])
            if roles:
                roles_applied.append(roles)
                st.write(f"Selected roles: {roles}")
                questions = generate_questions(roles, updated_data)
                print(questions)
                feedback = []
                answers = []
                ans = ""
                interaction = {}
                metrics = []
                import time
                st.write("Please wait for the questions to load (this may take a few seconds)")
                time.sleep(5)
                for i in range(len(questions)):
                    st.write(questions[i])
                    # ttts.say(questions[i])
                    # ques = speak(questions[i])
                    # pygame.mixer.music.load(ques, 'mp3')
                    # pygame.mixer.music.play()
                    ans = store_audio_text()
                    # st.button("stop recording", on_click=stop_recording)
                    st.success(ans)
                    answers.append(ans)
                    percent = 0.0
                    percent = generate_feedback(questions[i], answers[i])
                    print(percent)
                    feedback.append(generate_overall_feedback(data, percent, answers[i], questions[i]))
                    metrics.append(generate_metrics(data, answers[i], questions[i]))
                    # store the interaction into a dictionary
                    interaction["Question Asked:: "+ questions[i]] = "Answer by user:: "+ answers[i]
                    st.session_state.feedback = feedback
                    st.session_state.interaction = interaction
                print(st.session_state.interaction)
                print(metrics)
                print(feedback)
                st.button("Submit", on_click=evaluate.evaluate_app)
                st.stop()
                # if st.button("Submit"):
                #     print(feedback)
                #     print(metrics)
                #     # get only the numbers from metrics 
                #     metrics = [i for i in metrics if i.isdigit()]
                #     print(metrics)
                #     # add metrics to the session state
                #     st.session_state.metrics = metrics
                #     print(st.session_state.interaction)
                #     evaluate.evaluate_app()
                        # st.write("Thank you for your responses!")
                

            else:
                st.write("Please select a role to continue")
                return
        else:
            st.write("Please upload your resume to continue")
            return
                    
