import sqlite3
from datetime import datetime


def setup_database():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales_status (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 website TEXT NOT NULL,
                 is_on_sale INTEGER NOT NULL);''')

    c.execute('''CREATE TABLE IF NOT EXISTS bot_state (
                 state_key TEXT PRIMARY KEY,
                 state_value TEXT);''')

    c.execute('''CREATE TABLE IF NOT EXISTS historical_sales (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     website TEXT NOT NULL,
                     sale_price REAL NOT NULL,
                     sale_date TEXT NOT NULL);''')

    conn.commit()
    conn.close()


setup_database()


def update_sale_status(website, is_on_sale):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("REPLACE INTO sales_status (website, is_on_sale) VALUES (?, ?)", (website, is_on_sale))
    conn.commit()
    conn.close()


def get_previous_sale_status(website):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("SELECT is_on_sale FROM sales_status WHERE website = ?", (website,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def set_bot_state(key, value):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("REPLACE INTO bot_state (state_key, state_value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_bot_state(key):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("SELECT state_value FROM bot_state WHERE state_key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def log_historical_sale(website, sale_price):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()

    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Log the sale with the price
    c.execute("INSERT INTO historical_sales (website, sale_price, sale_date) VALUES (?, ?, ?)",
              (website, sale_price, current_date))
    conn.commit()
    conn.close()
