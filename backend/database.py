import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "career_captain.db")

def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password BLOB NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        keywords TEXT,
        location TEXT,
        job_title TEXT,
        company TEXT,
        matched_skills TEXT,
        missing_skills TEXT,
        summary TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()
    db.close()

def get_db():
    return sqlite3.connect(DB_PATH)
