"""
SQLite Database Layer for Quantellix Chatbot & Order Fulfillment Portal.
Manages user sessions, emails, uploaded datasets, and generated EDA reports.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "quantellix.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if not already present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_name TEXT DEFAULT '',
                email TEXT DEFAULT '',
                stage TEXT DEFAULT 'awaiting_name',
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Uploaded Files Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                filename TEXT,
                file_path TEXT,
                file_size_bytes INTEGER,
                row_count INTEGER,
                col_count INTEGER,
                uploaded_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
        """)

        # EDA Reports Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eda_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                file_id INTEGER,
                summary_json TEXT,
                report_html_path TEXT,
                created_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id),
                FOREIGN KEY(file_id) REFERENCES uploaded_files(id)
            )
        """)
        conn.commit()

def get_or_create_session(session_id: str, user_name: str = "", stage: str = "awaiting_name") -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        
        cursor.execute("""
            INSERT INTO sessions (session_id, user_name, email, stage, created_at, updated_at)
            VALUES (?, ?, '', ?, ?, ?)
        """, (session_id, user_name, stage, now, now))
        conn.commit()
        return {
            "session_id": session_id,
            "user_name": user_name,
            "email": "",
            "stage": stage,
            "created_at": now,
            "updated_at": now
        }

def update_session(session_id: str, user_name: Optional[str] = None, email: Optional[str] = None, stage: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            get_or_create_session(session_id, user_name or "", stage or "awaiting_name")
        
        updates = ["updated_at = ?"]
        params = [now]
        if user_name is not None:
            updates.append("user_name = ?")
            params.append(user_name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if stage is not None:
            updates.append("stage = ?")
            params.append(stage)
        params.append(session_id)
        
        query = f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        return dict(cursor.fetchone())

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def record_uploaded_file(session_id: str, filename: str, file_path: str, file_size_bytes: int, row_count: int, col_count: int) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO uploaded_files (session_id, filename, file_path, file_size_bytes, row_count, col_count, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, filename, file_path, file_size_bytes, row_count, col_count, now))
        conn.commit()
        return cursor.lastrowid

def record_eda_report(session_id: str, file_id: int, summary_dict: Dict[str, Any], report_html_path: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO eda_reports (session_id, file_id, summary_json, report_html_path, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, file_id, json.dumps(summary_dict), report_html_path, now))
        conn.commit()
        return cursor.lastrowid

def get_latest_eda_report(session_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, f.filename, f.file_path as source_file_path, f.file_size_bytes
            FROM eda_reports r
            LEFT JOIN uploaded_files f ON r.file_id = f.id
            WHERE r.session_id = ?
            ORDER BY r.id DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            if res.get("summary_json"):
                try:
                    res["summary"] = json.loads(res["summary_json"])
                except Exception:
                    res["summary"] = {}
            return res
def clear_session_data(session_id: str):
    """Deletes all session data, uploaded files, and eda reports for the specified session."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM eda_reports WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM uploaded_files WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

# Auto initialize on module import
init_db()

