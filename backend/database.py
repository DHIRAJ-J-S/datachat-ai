import sqlite3
import os
from typing import Any, Dict, List, Optional

DEFAULT_DB_FILE = os.getenv("DATABASE_PATH", "ecommerce.db")

def get_db_connection(db_name: Optional[str] = None) -> sqlite3.Connection:
    """Gets a connection to the SQLite database. Supports custom database path."""
    target_db = db_name if (db_name and os.path.exists(db_name)) else DEFAULT_DB_FILE
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the default database using seed.sql if it doesn't exist."""
    if not os.path.exists(DEFAULT_DB_FILE):
        print(f"Initializing database '{DEFAULT_DB_FILE}'...")
        conn = sqlite3.connect(DEFAULT_DB_FILE)
        seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
        conn.close()
        print("Database initialized successfully.")

def execute_query(query: str, params: tuple = (), db_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Executes a query and returns the results as a list of dicts."""
    conn = get_db_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("PRAGMA"):
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            conn.commit()
            return []
    finally:
        conn.close()
