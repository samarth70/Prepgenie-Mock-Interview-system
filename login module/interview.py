import streamlit as st
from firebase_admin import firestore

import time, start_interview

def test_app():
    # check if login
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    # if not login then go to login page
    if st.session_state.username == '':
        st.title('Welcome user to your :violet[Mock Interview]')
        st.write('This is a mock interview app, where you can practice your interview skills.')
        st.write('You can also get feedback on your answers.')
        st.write('please make sure you are in a calm and quiet place to give your interview.')

        st.subheader('Please login to continue')
        st.subheader('You can login from the sidebar')
        return

    else:
        # goto start_interview.py
        start_interview.user_interview()


        
