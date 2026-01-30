import sqlite3
import json
from datetime import datetime

DB_NAME = "expenses.db"

def init_database():
    """Initialize database tables with automatic migration"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT
            )
        """)
        
        # Income table - NEW
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                remaining REAL NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """)
        
        # Check if expenses table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
        expenses_exists = cursor.fetchone() is not None
        
        if expenses_exists:
            # Table exists - check if it has income_id column
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'income_id' not in columns:
                # Migration needed - add income_id column
                print("Migrating expenses table: adding income_id column...")
                cursor.execute("ALTER TABLE expenses ADD COLUMN income_id INTEGER")
                print("Migration complete!")
        else:
            # Create new table with income_id
            cursor.execute("""
                CREATE TABLE expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    income_id INTEGER,
                    FOREIGN KEY(username) REFERENCES users(username),
                    FOREIGN KEY(income_id) REFERENCES income(id)
                )
            """)
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(username, name)
            )
        """)
        
        conn.commit()

def add_user(username, password, email=""):
    """Add new user"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users(username, password, email) VALUES(?,?,?)", 
                         (username, password, email))
            conn.commit()
            
            # Add default categories
            default_categories = ["Food", "Transportation", "Clothing", "Bills", 
                                "Health", "Entertainment", "Other"]
            for cat in default_categories:
                cursor.execute("INSERT OR IGNORE INTO categories(username, name) VALUES(?,?)",
                             (username, cat))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    """Authenticate user login"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                      (username, password))
        return cursor.fetchone() is not None

# ============================================================
# INCOME FUNCTIONS - NEW
# ============================================================

def add_income(username, name, amount, date):
    """Add income"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO income(username, name, amount, date, remaining) 
            VALUES(?,?,?,?,?)
        """, (username, name, amount, date, amount))
        conn.commit()
        return cursor.lastrowid

def get_user_incomes(username):
    """Get all incomes for user"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, amount, date, remaining 
            FROM income 
            WHERE username=? 
            ORDER BY date DESC
        """, (username,))
        rows = cursor.fetchall()
        
        incomes = []
        for row in rows:
            incomes.append({
                "id": row[0],
                "name": row[1],
                "amount": row[2],
                "date": row[3],
                "remaining": row[4]
            })
        return incomes

def update_income_remaining(income_id, new_remaining):
    """Update remaining amount for income"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE income 
            SET remaining=? 
            WHERE id=?
        """, (new_remaining, income_id))
        conn.commit()

def delete_income(income_id):
    """Delete income by ID"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # First, unlink all expenses from this income
        cursor.execute("UPDATE expenses SET income_id=NULL WHERE income_id=?", (income_id,))
        # Then delete the income
        cursor.execute("DELETE FROM income WHERE id=?", (income_id,))
        conn.commit()

def update_income(income_id, name, amount, date):
    """Update income"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Get current remaining and original amount
        cursor.execute("SELECT amount, remaining FROM income WHERE id=?", (income_id,))
        result = cursor.fetchone()
        if result:
            old_amount, old_remaining = result
            spent = old_amount - old_remaining
            new_remaining = max(0, amount - spent)
            
            cursor.execute("""
                UPDATE income 
                SET name=?, amount=?, date=?, remaining=? 
                WHERE id=?
            """, (name, amount, date, new_remaining, income_id))
            conn.commit()

# ============================================================
# EXPENSE FUNCTIONS - UPDATED
# ============================================================

def add_expense(username, name, category, date, amount, income_id=None):
    """Add expense"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses(username, name, category, date, amount, income_id) 
            VALUES(?,?,?,?,?,?)
        """, (username, name, category, date, amount, income_id))
        
        # Update income remaining if linked
        if income_id:
            cursor.execute("SELECT remaining FROM income WHERE id=?", (income_id,))
            result = cursor.fetchone()
            if result:
                new_remaining = max(0, result[0] - amount)
                cursor.execute("UPDATE income SET remaining=? WHERE id=?", (new_remaining, income_id))
        
        conn.commit()

def get_user_expenses(username):
    """Get all expenses for user"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, category, date, amount, income_id 
            FROM expenses 
            WHERE username=? 
            ORDER BY date DESC
        """, (username,))
        rows = cursor.fetchall()
        
        expenses = []
        for row in rows:
            expenses.append({
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "date": row[3],
                "amount": row[4],
                "income_id": row[5]
            })
        return expenses

def delete_expense(expense_id):
    """Delete expense by ID"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Get expense details to refund income
        cursor.execute("SELECT amount, income_id FROM expenses WHERE id=?", (expense_id,))
        result = cursor.fetchone()
        
        if result and result[1]:  # If linked to income
            amount, income_id = result
            cursor.execute("SELECT remaining FROM income WHERE id=?", (income_id,))
            income_result = cursor.fetchone()
            if income_result:
                new_remaining = income_result[0] + amount
                cursor.execute("UPDATE income SET remaining=? WHERE id=?", (new_remaining, income_id))
        
        cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()

def update_expense(expense_id, name, category, date, amount, income_id=None):
    """Update expense"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Get old expense data
        cursor.execute("SELECT amount, income_id FROM expenses WHERE id=?", (expense_id,))
        old_data = cursor.fetchone()
        
        if old_data:
            old_amount, old_income_id = old_data
            
            # Refund old income if it was linked
            if old_income_id:
                cursor.execute("SELECT remaining FROM income WHERE id=?", (old_income_id,))
                result = cursor.fetchone()
                if result:
                    new_remaining = result[0] + old_amount
                    cursor.execute("UPDATE income SET remaining=? WHERE id=?", (new_remaining, old_income_id))
            
            # Deduct from new income if linked
            if income_id:
                cursor.execute("SELECT remaining FROM income WHERE id=?", (income_id,))
                result = cursor.fetchone()
                if result:
                    new_remaining = max(0, result[0] - amount)
                    cursor.execute("UPDATE income SET remaining=? WHERE id=?", (new_remaining, income_id))
        
        cursor.execute("""
            UPDATE expenses 
            SET name=?, category=?, date=?, amount=?, income_id=? 
            WHERE id=?
        """, (name, category, date, amount, income_id, expense_id))
        conn.commit()

def get_categories(username):
    """Get categories for user"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories WHERE username=? ORDER BY name", 
                      (username,))
        return [row[0] for row in cursor.fetchall()]

def add_category(username, category):
    """Add category"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories(username, name) VALUES(?,?)", 
                         (username, category))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def delete_category(username, category):
    """Delete category"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE username=? AND name=?", 
                      (username, category))
        conn.commit()

def get_total_expenses(username):
    """Get total expenses amount"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE username=?", 
                      (username,))
        result = cursor.fetchone()[0]
        return result if result else 0

def get_all_expenses(username):
    """Get all expenses for a user"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, category, date, amount, income_id 
            FROM expenses 
            WHERE username=?
            ORDER BY date DESC
        """, (username,))
        
        rows = cursor.fetchall()
        expenses = []
        for row in rows:
            expenses.append({
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "date": row[3],
                "amount": row[4],
                "income_id": row[5]
            })
        return expenses

def get_expense_count(username):
    """Get count of expenses"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses WHERE username=?", 
                      (username,))
        return cursor.fetchone()[0]

def filter_expenses_by_period(username, year, month=None):
    """Filter expenses by year and optional month"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if month:
            cursor.execute("""
                SELECT id, name, category, date, amount, income_id 
                FROM expenses 
                WHERE username=? AND strftime('%Y', date)=? AND strftime('%m', date)=?
                ORDER BY date DESC
            """, (username, str(year), f"{month:02d}"))
        else:
            cursor.execute("""
                SELECT id, name, category, date, amount, income_id 
                FROM expenses 
                WHERE username=? AND strftime('%Y', date)=?
                ORDER BY date DESC
            """, (username, str(year)))
        
        rows = cursor.fetchall()
        expenses = []
        for row in rows:
            expenses.append({
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "date": row[3],
                "amount": row[4],
                "income_id": row[5]
            })
        return expenses

def get_income_name(income_id):
    """Get income name by ID"""
    if not income_id:
        return "General"
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM income WHERE id=?", (income_id,))
        result = cursor.fetchone()
        return result[0] if result else "General"

# Initialize database on import
init_database()