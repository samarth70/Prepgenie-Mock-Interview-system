import streamlit as st

from streamlit_option_menu import option_menu
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import auth

# Initialize Firebase Admin once (outside the run function)
cred = credentials.Certificate("pondering-5ff7c-c033cfade319.json")
# firebase_admin.initialize_app(cred)

import account, chat, interview

st.set_page_config(
    page_title="Interview",
    page_icon=":shark:",
    layout="centered",
    initial_sidebar_state="auto",
)


def run():
    with st.sidebar:
        app = option_menu(
            menu_title='Mock Interview',
            options=['Login / Signup', 'Mock Interview', 'Chat with Resume'],
            icons=['lock-fill','chat-text-fill', 'file-pdf-fill', 'person-fill'],
            menu_icon="🦈",
            default_index=0,
        )


    if app == "Login / Signup":
        def f(): 
            try:
                user = auth.get_user_by_email(email)
                print(user.uid)
                st.session_state.username = user.uid
                st.session_state.useremail = user.email

                global Usernm
                Usernm=(user.uid)

                st.session_state.signedout = True
                st.session_state.signout = True    


            except: 
                st.warning('Login Failed')

        def t():
            st.session_state.signout = False
            st.session_state.signedout = False   
            st.session_state.username = ''





        if "signedout"  not in st.session_state:
            st.session_state["signedout"] = False
        if 'signout' not in st.session_state:
            st.session_state['signout'] = False    




        if  not st.session_state["signedout"]: # only show if the state is False, hence the button has never been clicked
            choice = st.selectbox('Login/Signup',['Login','Sign up'])
            email = st.text_input('Email Address')
            password = st.text_input('Password',type='password')



            if choice == 'Sign up':
                username = st.text_input("Enter  your unique username")

                if st.button('Create my account'):
                    user = auth.create_user(email = email, password = password,uid=username)

                    st.success('Account created successfully!')
                    st.markdown('Please Login using your email and password')
                    st.balloons()
            else:
                # st.button('Login', on_click=f)          
                st.button('Login', on_click=f)


        if st.session_state.signout:
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success('You have been logged in')
            st.write('You can now use the app from the sidebar')
            # add divider
            st.markdown('---')
            st.subheader('You are logged in as :violet['+st.session_state.username+']')
            st.write('Your email is: '+st.session_state.useremail)
            st.markdown('---')
            st.write('You can logout from here or refresh the page to logout.')
            if st.button('Logout'):
                st.session_state.username = ''
                st.session_state.useremail = ''
                st.session_state.signedout = True
                st.session_state.signout = True
                st.success('You have been logged out')
                st.write('You can login from the sidebar')
            return
        

    if app == "Mock Interview":
        interview.test_app()

    if app == "Chat with Resume":
        chat.chat_app()

    # if app == "Account":
    #     account.account_app()


run()
