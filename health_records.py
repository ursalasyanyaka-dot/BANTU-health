import sqlite3
import os

DB_NAME = 'queries.db'

def init_db():
    """Initializes the SQLite database with queries and clinics tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create queries telemetry table
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symptom TEXT NOT NULL,
            language TEXT NOT NULL,
            district TEXT NOT NULL,
            advice_given TEXT NOT NULL
        )
    ''')
    
    # Create clinics reference table
    c.execute('''
        CREATE TABLE IF NOT EXISTS clinics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            phone TEXT,
            nhima_accepted TEXT,
            hours TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_query(timestamp, symptom, language, district, advice_given):
    """Safely insert a query log using parameterized SQL."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO queries (timestamp, symptom, language, district, advice_given)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, symptom, language, district, advice_given))
    conn.commit()
    conn.close()

def get_all_queries():
    """Retrieve all query logs."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM queries ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return rows

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with queries and clinics tables!")