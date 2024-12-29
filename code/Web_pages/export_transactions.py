import streamlit as st
from db import get_transactions, get_categories
import pandas as pd
from io import BytesIO
from db import create_connection

def get_transactions_with_dates(user_id, from_date=None, to_date=None, category_name=None):
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        query = '''
            SELECT t.transaction_date, t.amount, t.transaction_name, c.category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
        '''
        params = [user_id]

        if from_date:
            query += " AND t.transaction_date >= %s"
            params.append(from_date)
        if to_date:
            query += " AND t.transaction_date <= %s"
            params.append(to_date)
        if category_name and category_name != "All Categories":
            query += " AND c.category_name = %s"
            params.append(category_name)

        query += " ORDER BY t.transaction_date DESC"
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        return transactions
    except Error as e:
        print(f"Error fetching transactions: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def export_transactions(user_id):
    st.header("Export Transactions")

    # Date Range Selection
    st.subheader("Select Date Range")
    from_date = st.date_input("From Date")
    to_date = st.date_input("To Date")

    # Category Filter
    st.subheader("Filter by Category")
    categories = get_categories(user_id)
    category_names = [cat['category_name'] for cat in categories]
    category_names.append('Uncategorized')  # Include Uncategorized
    selected_categories = st.multiselect("Select Categories", ["All Categories"] + category_names, default="All Categories")

    # Fetch transactions based on filter
    if "All Categories" in selected_categories:
        transactions = get_transactions_with_dates(user_id, from_date=from_date, to_date=to_date)
    else:
        transactions = []
        for category in selected_categories:
            transactions += get_transactions_with_dates(user_id, from_date=from_date, to_date=to_date, category_name=category)

    # Display Transactions
    st.subheader("Filtered Transactions")
    if transactions:
        # Convert to DataFrame for better display
        df_transactions = pd.DataFrame(transactions)
        st.dataframe(df_transactions)


        # Export Button
        if st.button("Export Transactions"):
                csv = df_transactions.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name='transactions.csv',
                    mime='text/csv'
                )
    else:
        st.info("No transactions found for the selected filters.")
