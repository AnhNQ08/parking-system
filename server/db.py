import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'parking.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            plate_number TEXT,
            action TEXT,
            rfid_uid TEXT,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_log(plate, action, rfid_uid, image_url=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO logs (timestamp, plate_number, action, rfid_uid, image_url) VALUES (?, ?, ?, ?, ?)',
              (now, plate, action, rfid_uid, image_url))
    conn.commit()
    conn.close()

def get_logs(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]
