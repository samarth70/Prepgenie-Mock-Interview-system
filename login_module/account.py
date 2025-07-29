import streamlit as st
from firebase_admin import firestore

def account_app():
    # st.title('User :violet[Account]')
    # check if login
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''

    # if not login then go to login page
    if st.session_state.username == '':
        st.title('Welcome to your :violet[Account]')
        st.write('This is your account page.')
        st.write('Here you can see your account details and change your password.')
        st.subheader('Please login to continue')
        st.subheader('You can login from the sidebar')
        return

    else:
        st.title('Welcome ' + st.session_state["username"] + ' to your :violet[Account]')
        st.write('You are logged in as: ' + st.session_state['username'])
        st.write('Your email is: ' + st.session_state['useremail'])
        st.write('You can also logout from here.')
        if st.button('Logout'):
            st.session_state.username = ''
            st.session_state.useremail = ''
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success('You have been logged out')
            st.write('You can login from the sidebar')
        return