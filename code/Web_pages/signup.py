# signup.py
import streamlit as st
from db import create_tables, add_category
import mysql.connector
from datetime import datetime
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_username(first_name, dob, cursor):
    base_username = f"{first_name}_{dob.month}_{dob.day}"
    username = base_username
    count = 1
    while True:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if not cursor.fetchone():
            break
        username = f"{base_username}_{count}"
        count += 1
    return username


def signup():
    st.title("Signup")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    dob = st.date_input("Date of Birth")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        if first_name and last_name and email and phone and password:
            try:
                connection = mysql.connector.connect(
                    user='root',
                    password='abdul',
                    host='localhost',
                    database='finance_app'
                )
                cursor = connection.cursor(dictionary=True)

                # Generate unique username
                username = generate_username(first_name, dob, cursor)

                hashed_pw = hash_password(password)

                cursor.execute('''
                    INSERT INTO users (first_name, last_name, email_id, phone_number, username, date_of_birth, password)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (first_name, last_name, email, phone, username, dob, hashed_pw))

                connection.commit()
                user_id = cursor.lastrowid

                # Insert predefined categories
                predefined_categories = ["Transport", "Grocery", "Utilities", "Education", "Personal Care"]
                for category in predefined_categories:
                    add_category(user_id, category)

                st.success(f"Signup successful! Your username is {username}. You can now log in.")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")
            finally:
                cursor.close()
                connection.close()
        else:
            st.error("Please fill all fields.")


if __name__ == "__main__":
    create_tables()
    signup()
