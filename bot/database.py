import sqlite3
import json
import os
from datetime import datetime

DB_NAME = os.path.join("data", "bot_data.db")

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Takip Listesi Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        date_key TEXT PRIMARY KEY,
        owner_email TEXT,
        account_id TEXT,
        account_name TEXT,
        draft_name TEXT,
        loc TEXT,
        max_mile INTEGER,
        targets TEXT,
        found_warehouses TEXT
    )''')

    # Log Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        message TEXT,
        type TEXT
    )''')
    
    conn.commit()
    conn.close()

# --- GÖREV İŞLEMLERİ ---
def add_task(owner_email, data):
    conn = get_connection()
    try:
        # Listeleri JSON string'e çeviriyoruz çünkü SQLite array tutamaz
        found_wh_str = json.dumps(data.get('found_warehouses', []))
        
        conn.execute('''INSERT OR REPLACE INTO tasks 
                        (date_key, owner_email, account_id, account_name, draft_name, loc, max_mile, targets, found_warehouses)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (data['date'], owner_email, data.get('account_id'), data.get('account_name'), 
                         data['name'], data['loc'], data['max_mile'], 
                         data['targets'], found_wh_str))
        conn.commit()
    finally:
        conn.close()

def remove_task(owner_email, date_key):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE date_key = ? AND owner_email = ?", (date_key, owner_email))
    conn.commit()
    conn.close()

def get_all_tasks(owner_email):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    # SADECE KENDİ TASLAKLARINI ÇEK
    cursor = conn.execute("SELECT * FROM tasks WHERE owner_email = ?", (owner_email,))
    rows = cursor.fetchall()
    conn.close()
    
    tasks = {}
    for row in rows:
        d = dict(row)
        d['name'] = row['draft_name']
        d['date'] = row['date_key']
        d['found_warehouses'] = json.loads(row['found_warehouses']) if row['found_warehouses'] else []
        tasks[row['date_key']] = d
    return tasks

# --- LOG İŞLEMLERİ ---
def add_log_db(message, log_type):
    conn = get_connection()
    ts = datetime.now().strftime("%H:%M:%S")
    conn.execute("INSERT INTO logs (timestamp, message, type) VALUES (?, ?, ?)", (ts, message, log_type))
    conn.commit()
    conn.close()

def get_logs_db(limit=50):
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [f"{r[1]} {r[2]}" for r in rows] # "14:00 Mesaj" formatı