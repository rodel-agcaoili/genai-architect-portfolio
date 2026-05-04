import sqlite3
import os
import time
from datetime import datetime
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "analytics.db")

def init_analytics_db():
    """Initialize the analytics database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Conversations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            session_id TEXT,
            guest_name TEXT,
            question TEXT,
            response TEXT,
            is_off_topic INTEGER DEFAULT 0
        )
    ''')
    
    # Visitor info table
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            session_id TEXT PRIMARY KEY,
            first_seen DATETIME,
            guest_name TEXT,
            last_active DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

def log_chat_interaction(question, response, guest_name=None, is_off_topic=0):
    """Log a single chat interaction."""
    session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Log the chat
    c.execute('''
        INSERT INTO chat_logs (timestamp, session_id, guest_name, question, response, is_off_topic)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, session_id, guest_name, question, response, is_off_topic))
    
    # Update visitor info
    c.execute('''
        INSERT INTO visitors (session_id, first_seen, guest_name, last_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET 
            last_active = excluded.last_active,
            guest_name = COALESCE(excluded.guest_name, visitors.guest_name)
    ''', (session_id, timestamp, guest_name, timestamp))
    
    conn.commit()
    conn.close()

def get_chat_logs(limit=100):
    """Retrieve recent chat logs."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM chat_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return logs

def get_visitor_summary():
    """Retrieve visitor summary."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM visitors ORDER BY last_active DESC')
    visitors = [dict(row) for row in c.fetchall()]
    conn.close()
    return visitors

def update_guest_name(name):
    """Update the guest name for the current session."""
    session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE visitors SET guest_name = ? WHERE session_id = ?', (name, session_id))
    c.execute('UPDATE chat_logs SET guest_name = ? WHERE session_id = ?', (name, session_id))
    conn.commit()
    conn.close()
