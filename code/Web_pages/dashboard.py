# dashboard.py
import streamlit as st
from db import (
    get_categories,
    add_category,
    set_budget,
    add_transaction,
    get_transactions,
    get_budgets,
    get_budget_and_expenses  # New function
)
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd


def dashboard(user_id, username):
    st.header(f"Welcome, {username}!")

    dashboard_selection = st.selectbox("Select Option",
                                       ["View Transactions", "Add Transaction", "Set Budget", "Manage Categories"])

    # dashboard.py

    if dashboard_selection == "View Transactions":
        st.subheader("Your Transactions Overview")

        # **Year and Month Selection**
        current_year = datetime.today().year
        years = list(range(current_year - 10, current_year + 11))  # Last 10 years to next 10 years
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Select Year", years, index=10)  # Default to current year
        with col2:
            selected_month_name = st.selectbox("Select Month", months, index=datetime.today().month - 1)

        # Convert selected month to integer
        month_number = months.index(selected_month_name) + 1

        # Fetch budget and expenses data
        data = get_budget_and_expenses(user_id, selected_year, month_number)

        if data:
            # Prepare data for the bar chart
            df = pd.DataFrame(data)

            # Separate data into budget and expenses
            df_budget = df[['category_name', 'budget']].copy()
            df_expenses = df[['category_name', 'expenses']].copy()

            # Replace NaN budgets with 0 for plotting
            df_budget['budget'] = df_budget['budget'].fillna(0)

            # Create bar chart
            fig = go.Figure()

            # Add Budget Bars
            fig.add_trace(go.Bar(
                x=df_budget['category_name'],
                y=df_budget['budget'],
                name='Budget',
                marker_color='indianred',
                hovertemplate='Budget: $%{y:.2f}<extra></extra>'
            ))

            # Add Expenses Bars
            fig.add_trace(go.Bar(
                x=df_expenses['category_name'],
                y=df_expenses['expenses'],
                name='Expenses',
                marker_color='lightsalmon',
                hovertemplate='Expenses: $%{y:.2f}<extra></extra>'
            ))

            # Update layout
            fig.update_layout(
                barmode='group',
                title=f"Budget vs Expenses for {selected_month_name} {selected_year}",
                xaxis_title="Category",
                yaxis_title="Amount",
                legend_title="Legend",
                template='plotly_white',
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display Total Budget and Expenses
            total_budget = df['budget'].sum()
            total_expenses = df['expenses'].sum()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Budget", f"${total_budget:.2f}")
            with col2:
                st.metric("Total Expenses", f"${total_expenses:.2f}")

            # Over-Budget Notifications
            over_budget = df[df['budget'] < df['expenses']]
            if not over_budget.empty:
                st.warning("You have exceeded your budget in the following categories:")
                for index, row in over_budget.iterrows():
                    st.write(f"- **{row['category_name']}**: Budget = ${row['budget']:.2f}, Expenses = ${row['expenses']:.2f}")
        else:
            st.info("No data available for the selected month.")

        st.markdown("---")

        # **Category Filter for Transactions**
        st.subheader("Filter Transactions by Category")
        categories = get_categories(user_id)
        category_names = [cat['category_name'] for cat in categories]
        category_names.append('Uncategorized')  # Include Uncategorized
        selected_filter_category = st.selectbox("Select Category", ["All Categories"] + category_names)

        # Fetch transactions based on filter
        if selected_filter_category == "All Categories":
            transactions = get_transactions(user_id)
        else:
            transactions = get_transactions(user_id, selected_filter_category)

        st.subheader("Your Transactions")
        if transactions:
            # Convert to DataFrame for better display
            df_transactions = pd.DataFrame(transactions)

            # Convert transaction_date to datetime for sorting
            df_transactions['transaction_date'] = pd.to_datetime(df_transactions['transaction_date'])

            # Allow user to sort
            sort_option = st.selectbox("Sort By", ["Date Descending", "Date Ascending", "Amount Descending", "Amount Ascending"])

            if sort_option == "Date Descending":
                df_transactions = df_transactions.sort_values(by='transaction_date', ascending=False)
            elif sort_option == "Date Ascending":
                df_transactions = df_transactions.sort_values(by='transaction_date', ascending=True)
            elif sort_option == "Amount Descending":
                df_transactions = df_transactions.sort_values(by='amount', ascending=False)
            elif sort_option == "Amount Ascending":
                df_transactions = df_transactions.sort_values(by='amount', ascending=True)

            st.dataframe(df_transactions)
        else:
            st.info("No transactions found.")


    elif dashboard_selection == "Add Transaction":
        st.subheader("Add New Transaction")
        transaction_name = st.text_input("Transaction Name")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        transaction_date = st.date_input("Transaction Date", datetime.today())

        categories = get_categories(user_id)
        category_names = [cat['category_name'] for cat in categories]
        selected_category = st.selectbox("Select Category", category_names + ["Add New Category"])

        if selected_category == "Add New Category":
            new_category = st.text_input("New Category Name")
            if st.button("Add Category"):
                if new_category:
                    success = add_category(user_id, new_category)
                    if success:
                        st.success(f"Category '{new_category}' added.")
                        st.rerun()
                    else:
                        st.error("Failed to add category. It might already exist.")
                else:
                    st.error("Please enter a category name.")

        # Select Payment Type
        transaction_type = st.radio("Payment Type", ["Cash", "Card", "Credit"])
        type_mapping = {"Cash": 0, "Card": 1, "Credit": 2}

        if st.button("Add Transaction"):
            if transaction_name and amount and selected_category != "Add New Category":
                # Get category_id
                category = next((cat for cat in categories if cat['category_name'] == selected_category), None)
                if category:
                    success = add_transaction(user_id, transaction_date, amount, transaction_name,
                                              category['category_id'], type_mapping[transaction_type])
                    if success:
                        st.success("Transaction added successfully.")
                    else:
                        st.error("Failed to add transaction.")
                else:
                    st.error("Selected category does not exist.")
            else:
                st.error("Please fill all fields.")

    elif dashboard_selection == "Set Budget":
        st.subheader("Set Monthly Budget")

        # **Year and Month Selection**
        current_year = datetime.today().year
        years = list(range(current_year - 10, current_year + 11))  # Last 10 years to next 10 years
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Select Year", years, index=10)  # Default to current year
        with col2:
            selected_month_name = st.selectbox("Select Month", months, index=datetime.today().month - 1)

        # Convert selected month to integer
        month_number = months.index(selected_month_name) + 1

        categories = get_categories(user_id)
        if categories:
            for cat in categories:
                # Fetch existing budget for the specific category
                existing_budget = get_budgets(user_id, selected_year, month_number, cat['category_id'])
                if existing_budget:
                    existing_budget = float(existing_budget[0]['budget'])
                else:
                    existing_budget = 0.0

                # Unique key for each input to prevent Streamlit conflicts
                budget_key = f"budget_{cat['category_id']}_{selected_year}_{month_number}"
                budget = st.number_input(
                    f"Budget for {cat['category_name']}",
                    min_value=0.0,
                    format="%.2f",
                    key=budget_key,
                    value=existing_budget  # Pre-fill with existing budget
                )
                set_btn = st.button(f"Set Budget for {cat['category_name']}", key=f"set_btn_{cat['category_id']}_{selected_year}_{month_number}")
                if set_btn:
                    if budget > 0:
                        set_success = set_budget(user_id, selected_year, month_number, cat['category_id'], budget)
                        if set_success:
                            st.success(f"Budget for {cat['category_name']} set to ${budget:.2f} for {selected_month_name} {selected_year}.")
                        else:
                            st.error("Failed to set budget.")
                    else:
                        st.error("Budget amount must be greater than zero.")
        else:
            st.info("No categories found. Please add a category first.")


    elif dashboard_selection == "Manage Categories":
        st.subheader("Your Categories")
        categories = get_categories(user_id)
        if categories:
            category_names = [cat['category_name'] for cat in categories]
            st.table(category_names)
        else:
            st.info("No categories found.")

        st.subheader("Add New Category")
        new_category = st.text_input("New Category Name")
        if st.button("Add Category"):
            if new_category:
                success = add_category(user_id, new_category)
                if success:
                    st.success(f"Category '{new_category}' added.")
                    st.rerun()
                else:
                    st.error("Failed to add category. It might already exist.")
            else:
                st.error("Please enter a category name.")
