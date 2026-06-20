import sqlite3
from datetime import datetime
import json

DB_FILE = "inferno_legacy.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # User Profile Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            matches INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            runs INTEGER DEFAULT 0,
            wickets INTEGER DEFAULT 0,
            highest_score INTEGER DEFAULT 0,
            best_bowling TEXT DEFAULT '0/0',
            rating INTEGER DEFAULT 0,
            badges TEXT DEFAULT '[]'
        )
    ''')
    
    # Match History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            mode TEXT,
            winner_id TEXT,
            match_data TEXT,
            timestamp DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id, username="Player"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)", 
            (user_id, username)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def update_stats(user_id, runs=0, wickets=0, win=False, loss=False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET matches = matches + 1,
            runs = runs + ?,
            wickets = wickets + ?,
            wins = wins + ?,
            losses = losses + ?,
            rating = rating + ?
        WHERE user_id = ?
    """, (runs, wickets, 1 if win else 0, 1 if loss else 0, 25 if win else -15, user_id))
    
    conn.commit()
    conn.close()

# Initialize database on module execution
init_db()
