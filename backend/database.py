import sqlite3
import os

DB_PATH = "soc_data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Table for raw parsed logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parsed_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            status TEXT,
            timestamp TEXT,
            username TEXT,
            raw_log TEXT
        )
    ''')
    
    # Table for alerts
    # If the file already exists with old schema we shouldn't wipe data just yet for safety,
    # but since this is a local dev project, we can DROP and re-create to keep logic simple
    # OR better, since the instructions allow, let's keep the user's data and try to alter or just drop.
    # Let's drop it so we get a clean slate for the 'real' SOC platform data.
    # Note: Removed DROP TABLE IF EXISTS alerts so data persists across restarts.
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT,
            username TEXT,
            attack_type TEXT,
            attempt_count INTEGER,
            severity TEXT,
            country TEXT,
            city TEXT,
            reputation TEXT,
            abuse_reports INTEGER,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
