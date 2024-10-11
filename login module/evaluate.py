import streamlit as st
from firebase_admin import auth
import os
import matplotlib.pyplot as plt
import google.generativeai as genai

# access the session state from start_interview.py
from start_interview import st

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
text_model= genai.GenerativeModel("gemini-pro")



def getmetrics(interaction, resume):
    text = f"This is the users resume: {resume}. And here is the interaction of the interview: {interaction}. Please evaluate the interview based on the interaction and the resume. rate me the following metrics on a scale of 1 to 10. 1 being the lowest and 10 being the highest. Communication skills, Teamwork and collaboration, Problem-solving and critical thinking, Time management and organization, Adaptability and resilience. just give the ratings for the metrics. You can also give the overall rating. i dont need the feedback. just the ratings. no other text is required. just the ratings. give me plain text not bold text."

    response = text_model.generate_content(text)
    response.resolve()
    # st.write(response.text)
    return response.text


def evaluate_app():
    # check if login
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    # if not login then go to login page
    if st.session_state.username == '':
        st.title('Welcome user to your :violet[Evaluation of Interview]')
        st.write('Evaluate your interview skills.')
        st.subheader('Please login to continue')
        st.subheader('You can login from the sidebar')
        return

    else:
        # goto start_interview.py
        st.title('Welcome ' + st.session_state["username"] + ' to your :violet[Evaluation of Interview]')
        # print the metrics from start_interview.py in sesssion state
        # st.write('Your interview has been evaluated')
        st.markdown('---')
        resume = st.session_state.resume

        metric = getmetrics(st.session_state.interaction, resume)
        # st.write(metric)
        # ['Communication skills: N/A\nTeamwork and collaboration: N/A\nProblem-solving and critical thinking: N/A\nTime management and organization: N/A\nAdaptability and resilience: N/A'] this is how metric will return the value
        # convert the string to dictionary
        metrics = {}
        for line in metric.split("\n"):
            key, value = line.split(":")
            metrics[key] = (value.strip())

        # convert the string to integer
        for key in metrics:
            if metrics[key] == 'N/A':
                metrics[key] = 0
            else:
                metrics[key] = int(metrics[key])
                
        st.write(metrics)

        # metrics = {
        #     "Communication skills": 7,
        #     "Teamwork and collaboration": 8,
        #     "Problem-solving and critical thinking": 9,
        #     "Time management and organization": 6,
        #     "Adaptability and resilience": 8,
        # }

        # Calculate overall average rating
        average_rating = sum(metrics.values()) / len(metrics)

        # Option 1: Full width containers
        st.header("Hey " + st.session_state.username + ", we have evaluated your interview:")
        # Display metrics and progress bars
        for metric, rating in metrics.items():
            st.subheader(metric)
            st.write(f"Rating: {rating}")
            progress_bar_width = int(200 * rating / 10)
            st.markdown(f"<div style='background-color: lightblue; width: {progress_bar_width}px; height: 10px;'></div>", unsafe_allow_html=True)

        st.header("Stats:")
        # Create and display pie chart
        plt.figure(figsize=(4, 4))
        plt.pie(metrics.values(), labels=metrics.keys(), autopct="%1.1f%%")
        plt.axis("equal")
        st.pyplot(use_container_width=True)

        st.subheader(f"Overall average rating: {average_rating:.2f}")
        # Use Markdown for rich text and flexibility
        st.markdown(st.session_state.feedback)
        st.markdown("---")
        st.write('You can see the interaction below:')
        st.write(st.session_state.interaction)
        # st.markdown('---')
        # st.success(st.session_state.feedback)