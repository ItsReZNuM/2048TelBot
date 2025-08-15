import sqlite3
from config import logger

DB_NAME = "bot.db"

def init_db():
    """Create tables if they don't exist"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        score INTEGER,
        time INTEGER
    )
    """)

    conn.commit()
    conn.close()

def save_user(user_id, username):
    """Save new user if not exists"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username if username else "ندارد"))
        logger.info(f"Saved user {user_id} to database")
    conn.commit()
    conn.close()

def get_all_users():
    """Return all saved users"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "username": row[1]} for row in rows]

def get_leaderboard():
    """Return leaderboard as dict"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, score, time FROM leaderboard")
    rows = cursor.fetchall()
    conn.close()
    return {str(row[0]): {"name": row[1], "score": row[2], "time": row[3]} for row in rows}

def save_leaderboard_entry(user_id, name, score, time_value):
    """Insert or update leaderboard entry"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO leaderboard (user_id, name, score, time)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        name = excluded.name,
        score = excluded.score,
        time = excluded.time
    """, (user_id, name, score, time_value))
    conn.commit()
    conn.close()
