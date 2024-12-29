import streamlit as st
import mysql.connector
import pandas as pd
from db import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
from decimal import Decimal
def profile(user_id):
    st.title("Profile Dashboard")

    # Fetch user details
    connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_details = cursor.fetchone()
    cursor.close()
    connection.close()

    # Display user details
    if user_details:
        st.subheader("User Details")
        st.write(f"**Name:** {user_details['first_name']} {user_details['last_name']}")
        st.write(f"**Email:** {user_details['email_id']}")
        st.write(f"**Phone:** {user_details['phone_number']}")

        # Create the four grid boxes
        col1, col2, col3, col4 = st.columns(4)

        if "show_balance" not in st.session_state:
            st.session_state["show_balance"] = False

        if "show_credit" not in st.session_state:
            st.session_state["show_credit"] = False

        if "show_goals" not in st.session_state:
            st.session_state["show_goals"] = False

        if "show_shared_goals" not in st.session_state:
            st.session_state["show_shared_goals"] = False

        with col1:
            if st.button("Balance"):
                st.session_state["show_balance"] = not st.session_state["show_balance"]
                st.session_state["show_credit"] = False
                st.session_state["show_goals"] = False
                st.session_state["show_shared_goals"] = False

        with col2:
            if st.button("Credit"):
                st.session_state["show_credit"] = not st.session_state["show_credit"]
                st.session_state["show_balance"] = False
                st.session_state["show_goals"] = False
                st.session_state["show_shared_goals"] = False

        with col3:
            if st.button("Goals"):
                st.session_state["show_goals"] = not st.session_state["show_goals"]
                st.session_state["show_balance"] = False
                st.session_state["show_credit"] = False
                st.session_state["show_shared_goals"] = False
        with col4:
            if st.button("show_shared_goals"):
                st.session_state["show_shared_goals"] = not st.session_state["show_shared_goals"]
                st.session_state["show_balance"] = False
                st.session_state["show_credit"] = False
                st.session_state["show_goals"] = False

        # Show Balance Section
        if st.session_state["show_balance"]:
            show_balance(user_id)

        # Show Credit Section
        if st.session_state["show_credit"]:
            show_credit(user_id)

        # Show Goals Section
        if st.session_state["show_goals"]:
            manage_goals(user_id)

        if st.session_state["show_shared_goals"]:
            manage_shared_goals_and_contributions(user_id)

    with st.expander("Transactions"):
        show_transactions(user_id)

def show_balance(user_id):
    connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT SUM(amount) AS balance FROM balance_credit_transactions WHERE user_id = %s AND type = 0", (user_id,))
    result = cursor.fetchone()
    balance = result['balance'] if result['balance'] else 0

    st.subheader(f"Current Balance: ${balance}")

    amount = st.number_input("Enter amount to add or reduce:", step=0.01, format="%.2f", key="balance_amount")
    action = st.radio("Action", ("Add", "Reduce"), key="balance_action")
    description = st.text_input("Description", "Balance Update", key="balance_description")

    if st.button("Update Balance", key="update_balance"):
        new_amount = amount if action == "Add" else -amount
        try:
            cursor.execute("INSERT INTO balance_credit_transactions (user_id, amount, description, type) VALUES (%s, %s, %s, 0)", (user_id, new_amount, description))
            connection.commit()
            st.success("Balance updated successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error updating balance: {err}")

    cursor.execute("SELECT * FROM balance_credit_transactions WHERE user_id = %s AND type = 0 ORDER BY transaction_date DESC LIMIT 5", (user_id,))
    transactions = cursor.fetchall()
    st.write("Recent Transactions:")
    st.dataframe(pd.DataFrame(transactions))

    cursor.close()
    connection.close()

def show_credit(user_id):
    connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT SUM(amount) AS credit FROM balance_credit_transactions WHERE user_id = %s AND type = 1", (user_id,))
    result = cursor.fetchone()
    credit = result['credit'] if result['credit'] else 0

    st.subheader(f"Current Credit: ${credit}")

    amount = st.number_input("Enter amount to add or reduce:", step=0.01, format="%.2f", key="credit_amount")
    action = st.radio("Action", ("Add", "Reduce"), key="credit_action")
    description = st.text_input("Description", "Credit Update", key="credit_description")

    if st.button("Update Credit", key="update_credit"):
        new_amount = amount if action == "Add" else -amount
        try:
            cursor.execute("INSERT INTO balance_credit_transactions (user_id, amount, description, type) VALUES (%s, %s, %s, 1)", (user_id, new_amount, description))
            connection.commit()
            st.success("Credit updated successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error updating credit: {err}")

    cursor.execute("SELECT * FROM balance_credit_transactions WHERE user_id = %s AND type = 1 ORDER BY transaction_date DESC LIMIT 5", (user_id,))
    transactions = cursor.fetchall()
    st.write("Recent Credit Transactions:")
    st.dataframe(pd.DataFrame(transactions))

    cursor.close()
    connection.close()


def manage_goals(user_id):
    st.subheader("Personal Goals")

    connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = connection.cursor(dictionary=True)

    # Create New Goal
    st.write("Create a New Goal")
    goal_name = st.text_input("Goal Name")
    expected_amount = st.number_input("Expected Amount", min_value=0.0, format="%.2f")
    if st.button("Create Goal"):
        if goal_name and expected_amount > 0:
            try:
                cursor.execute('''
                    INSERT INTO personal_goals (user_id, goal_name, expected_amount)
                    VALUES (%s, %s, %s)
                ''', (user_id, goal_name, expected_amount))
                connection.commit()
                st.success(f"Goal '{goal_name}' created successfully.")
            except mysql.connector.Error as err:
                st.error(f"Error creating goal: {err}")
        else:
            st.error("Please provide a valid goal name and expected amount.")

    # View Existing Goals
    st.write("Your Goals")
    cursor.execute('''
        SELECT goal_id, goal_name, expected_amount, current_savings 
        FROM personal_goals
        WHERE user_id = %s
    ''', (user_id,))
    goals = cursor.fetchall()

    if goals:
        for i in range(0, len(goals), 2):
            cols = st.columns(2)  # Create two columns for each row
            for idx in range(2):
                if i + idx < len(goals):
                    goal = goals[i + idx]
                    with cols[idx]:
                        # Display goal inside a bordered container
                        st.markdown(
                            f"""
                            <div style="border: 2px solid #4CAF50; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <strong>{goal['goal_name']}</strong><br>
                                Expected Amount: ${goal['expected_amount']:.2f}<br>
                                Current Savings: ${goal['current_savings']:.2f}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Calculate progress as a percentage
                        progress = float(goal['current_savings'] / goal['expected_amount']) if goal[
                                                                                                   'expected_amount'] > 0 else 0.0
                        st.progress(progress)  # Add progress bar

                        # Update Savings
                        savings_update = st.number_input(f"Add to Savings for {goal['goal_name']}", min_value=0.0,
                                                         format="%.2f", key=f"savings_{goal['goal_id']}")
                        if st.button(f"Update Savings for {goal['goal_name']}",
                                     key=f"update_savings_{goal['goal_id']}"):
                            try:
                                new_savings = goal['current_savings'] + Decimal(
                                    str(savings_update))  # Convert to Decimal
                                cursor.execute('''
                                    UPDATE personal_goals
                                    SET current_savings = %s
                                    WHERE goal_id = %s
                                ''', (new_savings, goal['goal_id']))
                                connection.commit()
                                st.success(f"Savings updated for goal '{goal['goal_name']}'.")
                                st.rerun()
                            except mysql.connector.Error as err:
                                st.error(f"Error updating savings: {err}")

                        # Delete Goal
                        if st.button(f"Delete Goal '{goal['goal_name']}'", key=f"delete_goal_{goal['goal_id']}"):
                            try:
                                cursor.execute('''
                                    DELETE FROM personal_goals
                                    WHERE goal_id = %s
                                ''', (goal['goal_id'],))
                                connection.commit()
                                st.success(f"Goal '{goal['goal_name']}' deleted successfully.")
                                st.rerun()
                            except mysql.connector.Error as err:
                                st.error(f"Error deleting goal: {err}")
    else:
        st.write("No personal goals set.")

from decimal import Decimal


def show_transactions(user_id):
    pass


def manage_shared_goals_and_contributions(user_id):
    st.subheader("Shared Financial Goals")

    connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = connection.cursor(dictionary=True)

    # Share a New Financial Goal
    st.write("Share a New Goal")
    share_goal_name = st.text_input("Goal Name", key=f"share_goal_name_{user_id}")
    share_expected_amount = st.number_input("Expected Amount", min_value=0.0, format="%.2f",
                                            key=f"share_expected_amount_{user_id}")
    shared_user_input = st.text_input("Enter email or username of the user to share with",
                                      key=f"shared_user_input_{user_id}")

    if st.button("Share Goal", key=f"share_goal_button_{user_id}"):
        if share_goal_name and share_expected_amount > 0 and shared_user_input:
            try:
                # Check if the shared user exists
                cursor.execute('''
                    SELECT user_id FROM users WHERE email_id = %s OR username = %s
                ''', (shared_user_input, shared_user_input))
                shared_user = cursor.fetchone()

                if shared_user:
                    shared_with_user_id = shared_user['user_id']
                    # Insert the shared goal
                    cursor.execute('''
                        INSERT INTO shared_goals (owner_user_id, shared_with_user_id, goal_name, expected_amount)
                        VALUES (%s, %s, %s, %s)
                    ''', (user_id, shared_with_user_id, share_goal_name, share_expected_amount))
                    connection.commit()
                    st.success(f"Goal '{share_goal_name}' shared successfully with {shared_user_input}.")
                else:
                    st.error("User not found. Please enter a valid email or username.")
            except mysql.connector.Error as err:
                st.error(f"Error sharing goal: {err}")
        else:
            st.error("Please fill in all fields.")

    st.markdown("---")  # Separator

    # View Existing Shared Goals
    st.write("Your Shared Goals")
    cursor.execute('''
        SELECT sg.goal_id, sg.goal_name, sg.expected_amount, u.first_name, u.last_name
        FROM shared_goals sg
        JOIN users u ON sg.shared_with_user_id = u.user_id
        WHERE sg.owner_user_id = %s
    ''', (user_id,))
    shared_goals = cursor.fetchall()

    cursor.execute('''
        SELECT sg.goal_id, sg.goal_name, sg.expected_amount, u.first_name, u.last_name
        FROM shared_goals sg
        JOIN users u ON sg.owner_user_id = u.user_id
        WHERE sg.shared_with_user_id = %s
    ''', (user_id,))
    received_shared_goals = cursor.fetchall()

    all_shared_goals = shared_goals + received_shared_goals

    if all_shared_goals:
        for goal in all_shared_goals:
            # Fetch total contributions for the specified shared goal
            try:
                cursor.execute('''
                    SELECT SUM(contribution_amount) as total_contributions
                    FROM shared_goal_contributions
                    WHERE shared_goal_id = %s
                ''', (goal['goal_id'],))
                total_contributions_result = cursor.fetchone()
                total_contributions = total_contributions_result['total_contributions'] or 0.0
            except mysql.connector.Error as err:
                st.error(f"Error fetching total contributions: {err}")
                continue

            # Display goal details
            progress = float(total_contributions / goal['expected_amount']) if goal['expected_amount'] > 0 else 0.0
            st.markdown(
                f"""
                <div style="border: 2px solid #2196F3; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <strong>{goal['goal_name']}</strong><br>
                    Expected Amount: ${goal['expected_amount']:.2f}<br>
                    Total Contributions: ${total_contributions:.2f}<br>
                    Progress: {progress * 100:.2f}%<br>
                    Shared With: {goal['first_name']} {goal['last_name']}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.progress(progress)

            # Fetch contributions for the specified shared goal
            try:
                cursor.execute('''
                    SELECT u.first_name, u.last_name, sgc.contribution_amount, sgc.contribution_date
                    FROM shared_goal_contributions sgc
                    JOIN users u ON sgc.user_id = u.user_id
                    WHERE sgc.shared_goal_id = %s
                ''', (goal['goal_id'],))
                contributions = cursor.fetchall()
            except mysql.connector.Error as err:
                st.error(f"Error fetching contributions: {err}")
                continue

            # Display contributions
            if contributions:
                for contribution in contributions:
                    st.write(
                        f"{contribution['first_name']} {contribution['last_name']} contributed "
                        f"${contribution['contribution_amount']:.2f} on {contribution['contribution_date']}"
                    )
            else:
                st.write("No contributions yet.")

            # Contribution Section for the current user
            st.write("Add Your Contribution")

            # Calculate the maximum allowable contribution
            max_contribution = float(goal['expected_amount'] - total_contributions)
            contribution_amount = st.number_input(
                f"Contribution Amount for Shared Goal {goal['goal_id']} (Max: ${max_contribution:.2f})",
                min_value=0.0,
                max_value=max_contribution,
                format="%.2f",
                key=f"contribution_amount_{goal['goal_id']}"
            )

            # Assign a unique key to the "Contribute" button to ensure proper behavior
            if st.button(f"Contribute to Shared Goal {goal['goal_id']}", key=f"contribute_button_{goal['goal_id']}"):
                st.write(f"Button clicked with contribution amount: {contribution_amount}")  # Debugging confirmation

                if contribution_amount > 0:
                    try:
                        # Insert contribution into the shared_goal_contributions table
                        st.write("Attempting to contribute to the goal...")  # Debugging confirmation
                        cursor.execute('''
                            INSERT INTO shared_goal_contributions (shared_goal_id, user_id, contribution_amount)
                            VALUES (%s, %s, %s)
                        ''', (goal['goal_id'], user_id, Decimal(str(contribution_amount))))
                        connection.commit()
                        st.success(f"You have successfully contributed ${contribution_amount:.2f} to the shared goal.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Error contributing to the goal: {err}")
                else:
                    st.error("Please enter a valid contribution amount.")

            st.markdown("---")  # Separator between goals
    else:
        st.write("No shared goals available.")

    cursor.close()
    connection.close()

