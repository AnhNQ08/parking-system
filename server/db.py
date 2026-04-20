import os
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "parking_system")


def get_db_connection(use_database=True):
    config = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
    }
    if use_database:
        config["database"] = MYSQL_DATABASE
    return pymysql.connect(**config)


def init_db():
    conn = get_db_connection(use_database=False)
    c = conn.cursor()
    c.execute(
        f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    conn.close()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INT NOT NULL AUTO_INCREMENT,
            timestamp DATETIME DEFAULT NULL,
            plate_number VARCHAR(64) DEFAULT NULL,
            action VARCHAR(64) DEFAULT NULL,
            rfid_uid VARCHAR(64) DEFAULT NULL,
            image_url VARCHAR(512) DEFAULT NULL,
            PRIMARY KEY (id),
            KEY idx_logs_rfid_uid (rfid_uid),
            KEY idx_logs_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS authorized_vehicles (
            rfid_uid VARCHAR(64) NOT NULL,
            plate_number VARCHAR(64) DEFAULT NULL,
            owner_name VARCHAR(255) DEFAULT NULL,
            PRIMARY KEY (rfid_uid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    conn.commit()
    conn.close()


def check_auth(uid):
    """Kiem tra xem the UID co trong danh sach duoc phep khong."""
    if not uid:
        return None
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT plate_number FROM authorized_vehicles WHERE rfid_uid = %s",
        (uid.strip().upper(),),
    )
    result = c.fetchone()
    conn.close()
    return result["plate_number"] if result else None


def insert_log(plate, action, rfid_uid, image_url=""):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO logs (timestamp, plate_number, action, rfid_uid, image_url) VALUES (%s, %s, %s, %s, %s)",
            (now, plate, action, rfid_uid, image_url),
        )
        log_id = int(c.lastrowid)
        conn.commit()
        conn.close()
        return log_id
    except Exception as e:
        print(f"[!] Error logging to DB: {e}")
        return None


def update_log(log_id, plate=None, image_url=None):
    try:
        if log_id is None:
            return
        conn = get_db_connection()
        c = conn.cursor()
        if plate and image_url:
            c.execute(
                "UPDATE logs SET plate_number = %s, image_url = %s WHERE id = %s",
                (plate, image_url, log_id),
            )
        elif plate:
            c.execute("UPDATE logs SET plate_number = %s WHERE id = %s", (plate, log_id))
        elif image_url:
            c.execute("UPDATE logs SET image_url = %s WHERE id = %s", (image_url, log_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Error updating log: {e}")


def get_logs(limit=20):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT %s", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_last_action(rfid_uid):
    """Lay hanh dong cuoi cung cua xe (IN/OUT) de toggle cong."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT action FROM logs WHERE rfid_uid = %s AND action IN ('IN','OUT') ORDER BY id DESC LIMIT 1",
        (rfid_uid.strip().upper(),),
    )
    result = c.fetchone()
    conn.close()
    return result["action"] if result else None
