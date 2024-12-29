# app.py
import streamlit as st
from Web_pages.signup import signup
from Web_pages.login import login
from Web_pages.dashboard import dashboard
from db import create_tables
from profile import profile
from Web_pages.export_transactions import export_transactions

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", ["Login", "Signup", "Dashboard","Profile","Export Data"])

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = ''

    if selection == "Signup":
        signup()
    elif selection == "Login":
        login()
    elif selection == "Dashboard":
        if st.session_state['logged_in']:
            dashboard(st.session_state['user_id'], st.session_state['username'])
        else:
            st.warning("Please log in to access the dashboard.")
    elif selection == "Profile":
        if 'logged_in' in st.session_state and st.session_state['logged_in']:
            profile(st.session_state['user_id']);
        else:
            st.warning("Please login first.")
    elif selection == "Export Data":
        if 'logged_in' in st.session_state and st.session_state['logged_in']:
            export_transactions(st.session_state['user_id']);
        else:
            st.warning("Please login first.")

if __name__ == "__main__":
    create_tables()
    main()
