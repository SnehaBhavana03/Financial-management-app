# login.py
import streamlit as st
from db import create_connection
import mysql.connector
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username and password:
            hashed_pw = hash_password(password)
            connection = mysql.connector.connect(
                user='root',
                password='abdul',
                host='localhost',
                database='finance_app'
            )
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, hashed_pw))
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user['username']
                st.session_state['user_id'] = user['user_id']
                st.success("Logged in successfully!")
            else:
                st.error("Invalid credentials.")
        else:
            st.error("Please enter both username and password.")

if __name__ == "__main__":
    login()
