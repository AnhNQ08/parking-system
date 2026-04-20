import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'parking.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Bảng lịch sử log xe ra vào
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
    # Bảng danh sách xe được phép (Whitelist)
    c.execute('''
        CREATE TABLE IF NOT EXISTS authorized_vehicles (
            rfid_uid TEXT PRIMARY KEY,
            plate_number TEXT,
            owner_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def check_auth(uid):
    """Kiểm tra xem thẻ UID có trong danh sách được phép không"""
    if not uid: return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT plate_number FROM authorized_vehicles WHERE rfid_uid = ?', (uid.strip().upper(),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def insert_log(plate, action, rfid_uid, image_url=""):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('INSERT INTO logs (timestamp, plate_number, action, rfid_uid, image_url) VALUES (?, ?, ?, ?, ?)',
                  (now, plate, action, rfid_uid, image_url))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Error logging to DB: {e}")

def get_logs(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

def get_last_action(rfid_uid):
    """Lấy hành động cuối cùng của xe (IN/OUT) để toggle cổng"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT action FROM logs WHERE rfid_uid = ? AND action IN ('IN','OUT') ORDER BY id DESC LIMIT 1",
        (rfid_uid.strip().upper(),)
    )
    result = c.fetchone()
    conn.close()
    # None = chưa có lịch sử -> xe đang ngoài -> mở cổng VÀO
    return result[0] if result else None
