# db.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

DB_USER = 'root'
DB_PASSWORD = 'abdul'
DB_HOST = 'localhost'
DB_NAME = 'finance_app'


# Security user setup
USER_CONFIG = {
    'new_user': 'finance_user',
    'new_user_password': 'user_password'
}

def create_connection():
    """Create and return a new database connection."""
    try:
        connection = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_tables():
    """Create necessary tables if they don't exist."""
    connection = create_connection()
    if connection is None:
        return
    cursor = connection.cursor()
    try:
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email_id VARCHAR(100) UNIQUE NOT NULL,
                phone_number VARCHAR(15) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                date_of_birth DATE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                category_name VARCHAR(100) NOT NULL,
                UNIQUE(user_id, category_name),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                year YEAR NOT NULL,
                month TINYINT NOT NULL, -- 1 for January, 2 for February, etc.
                category_id INT NOT NULL,
                budget DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
                UNIQUE(user_id, year, month, category_id)
            );
        ''')
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                transaction_date DATE NOT NULL,
                amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
                transaction_name VARCHAR(255) NOT NULL,
                category_id INT,
                type TINYINT NOT NULL,  -- 0: Cash, 1: Card, 2: Credit
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_credit_transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                description VARCHAR(255),
                type TINYINT NOT NULL,  -- 0: Balance, 1: Credit
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_goals (
                goal_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                goal_name VARCHAR(255) NOT NULL,
                expected_amount DECIMAL(10, 2) NOT NULL,
                current_savings DECIMAL(10, 2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_goals (
                goal_id INT AUTO_INCREMENT PRIMARY KEY,
                owner_user_id INT NOT NULL,
                shared_with_user_id INT NOT NULL,
                goal_name VARCHAR(255) NOT NULL,
                expected_amount DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (shared_with_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_goal_contributions (
                contribution_id INT AUTO_INCREMENT PRIMARY KEY,
                shared_goal_id INT NOT NULL,
                user_id INT NOT NULL,
                contribution_amount DECIMAL(10, 2) NOT NULL,
                contribution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shared_goal_id) REFERENCES shared_goals(goal_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        ''')

        trigger_sql = """
        DELIMITER //

        CREATE TRIGGER IF NOT EXISTS check_contribution_before_insert
        BEFORE INSERT ON shared_goal_contributions
        FOR EACH ROW
        BEGIN
            DECLARE total_contributions DECIMAL(10, 2);
            DECLARE expected_amount DECIMAL(10, 2);

            -- Get the expected amount for the shared goal
            SELECT expected_amount INTO expected_amount
            FROM shared_goals
            WHERE goal_id = NEW.shared_goal_id;

            -- Calculate the total contributions already made for this goal
            SELECT SUM(contribution_amount) INTO total_contributions
            FROM shared_goal_contributions
            WHERE shared_goal_id = NEW.shared_goal_id;

            -- Ensure the new contribution does not exceed the expected amount
            IF (total_contributions + NEW.contribution_amount) > expected_amount THEN
                SIGNAL SQLSTATE '45000' 
                SET MESSAGE_TEXT = 'Contribution exceeds the expected amount for this shared goal';
            END IF;
        END;
        //

        DELIMITER ;
        """

        # Security setup - create a new user for end-user access
        cursor.execute(
            f"CREATE USER IF NOT EXISTS '{USER_CONFIG['new_user']}'@'{DB_HOST}' IDENTIFIED BY '{USER_CONFIG['new_user_password']}'"
        )

        # Granting limited privileges to the new user
        cursor.execute(
            f"GRANT SELECT, INSERT, UPDATE ON {DB_NAME}.* TO '{USER_CONFIG['new_user']}'@'{DB_HOST}'"
        )
        cursor.execute("FLUSH PRIVILEGES")

        cursor.execute(trigger_sql)
        connection.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        connection.close()


# Category Operations
def get_categories(user_id):
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM categories WHERE user_id = %s", (user_id,))
        categories = cursor.fetchall()
        return categories
    except Error as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def add_category(user_id, category_name):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO categories (user_id, category_name)
            VALUES (%s, %s)
        ''', (user_id, category_name))
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding category: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


# Budget Operations
# db.py

def set_budget(user_id, year, month, category_id, budget):
    """
    Set or update the budget for a specific user, year, month, and category.
    """
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO budgets (user_id, year, month, category_id, budget)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE budget = VALUES(budget)
        ''', (user_id, year, month, category_id, budget))
        connection.commit()
        return True
    except Error as e:
        print(f"Error setting budget: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_budgets(user_id, year, month, category_id=None):
    """
    Fetch budgets. If category_id is provided, fetch budget for that category, year, and month.
    Otherwise, fetch all budgets for the user for the specified year and month.
    """

    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        if category_id:
            cursor.execute('''
                SELECT budget
                FROM budgets
                WHERE user_id = %s AND year = %s AND month = %s AND category_id = %s
            ''', (user_id, year, month, category_id))
        else:
            cursor.execute('''
                SELECT b.budget, c.category_name
                FROM budgets b
                JOIN categories c ON b.category_id = c.category_id
                WHERE b.user_id = %s AND b.year = %s AND b.month = %s
            ''', (user_id, year, month))
        budgets = cursor.fetchall()
        print("budgets", budgets,user_id, year, month)  # Debugging Statement
        return budgets
    except Error as e:
        print(f"Error fetching budgets: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


# Transaction Operations
def add_transaction(user_id, transaction_date, amount, transaction_name, category_id, transaction_type):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        # Add the transaction to the transactions table
        cursor.execute('''
            INSERT INTO transactions (user_id, transaction_date, amount, transaction_name, category_id, type)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, transaction_date, amount, transaction_name, category_id, transaction_type))

        # Update balance or credit based on transaction type
        if transaction_type in [0, 1]:  # Cash or Card, decrease balance
            update_balance_credit(user_id, -abs(amount), 0, f"t_name: {transaction_name}")  # 0 represents balance
        elif transaction_type == 2:  # Credit, increase credit
            update_balance_credit(user_id, amount, 1, f"t_name: {transaction_name}")  # 1 represents credit

        connection.commit()
        return True
    except Error as e:
        print(f"Error adding transaction: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def update_balance_credit(user_id, amount, balance_type, description):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        # Insert the balance or credit update
        cursor.execute('''
            INSERT INTO balance_credit_transactions (user_id, amount, type, description)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, amount, balance_type, description))

        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error updating balance/credit: {err}")
    finally:
        cursor.close()
        connection.close()


def get_transactions(user_id, category_name=None):
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        if category_name and category_name != "All Categories":
            cursor.execute('''
                SELECT t.transaction_date, t.amount, t.transaction_name, c.category_name
                FROM transactions t
                JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = %s AND c.category_name = %s
                ORDER BY t.transaction_date DESC
            ''', (user_id, category_name))
        else:
            cursor.execute('''
                SELECT t.transaction_date, t.amount, t.transaction_name, c.category_name
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = %s
                ORDER BY t.transaction_date DESC
            ''', (user_id,))
        transactions = cursor.fetchall()
        return transactions
    except Error as e:
        print(f"Error fetching transactions: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_budget_and_expenses(user_id, year, month):
    """
    Fetch budgets and total expenses per category for a given year and month.
    Returns a list of dictionaries with category_name, budget, and expenses.
    """
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor(dictionary=True)
    try:
        # Fetch budgets
        cursor.execute('''
            SELECT c.category_name, b.budget
            FROM budgets b
            JOIN categories c ON b.category_id = c.category_id
            WHERE b.user_id = %s AND b.year = %s AND b.month = %s
        ''', (user_id, year, month))
        budgets = cursor.fetchall()
        budget_dict = {item['category_name']: float(item['budget']) for item in budgets}
        print(f"Budgets: {budget_dict}")  # Debugging Statement

        # Fetch total expenses per category, including Uncategorized
        cursor.execute('''
            SELECT IFNULL(c.category_name, 'Uncategorized') AS category_name, SUM(t.amount) as total_expense
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s
            GROUP BY IFNULL(c.category_name, 'Uncategorized')
        ''', (user_id, year, month))
        expenses = cursor.fetchall()
        expense_dict = {item['category_name']: float(item['total_expense']) for item in expenses}
        print(f"Expenses: {expense_dict}")  # Debugging Statement

        # Get all categories for the user
        cursor.execute("SELECT category_name FROM categories WHERE user_id = %s", (user_id,))
        categories = cursor.fetchall()
        category_names = [cat['category_name'] for cat in categories]
        category_names.append('Uncategorized')  # Include Uncategorized
        print(f"Categories: {category_names}")  # Debugging Statement

        # Combine budgets and expenses
        combined_data = []
        for category in category_names:
            budget = budget_dict.get(category, None)
            expense = expense_dict.get(category, 0.0)
            combined_data.append({
                'category_name': category,
                'budget': budget,
                'expenses': expense
            })

        print(f"Combined Data: {combined_data}")  # Debugging Statement
        return combined_data
    except Error as e:
        print(f"Error fetching budget and expenses: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    create_tables()