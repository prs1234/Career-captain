import bcrypt
import sqlite3
from backend.database import get_db

def signup_user(email, password):
    db = get_db()
    cursor = db.cursor()

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
        db.commit()
        return True, "✅ Signup successful!"
    except sqlite3.IntegrityError:
        return False, "⚠ User already exists."
    finally:
        db.close()

def login_user(email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    db.close()

    if row and bcrypt.checkpw(password.encode("utf-8"), row[0]):
        return True, "✅ Login successful!"
    return False, "❌ Invalid credentials."
