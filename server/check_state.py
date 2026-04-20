from db import get_last_action
import sqlite3

conn = sqlite3.connect('parking.db')
c = conn.cursor()
c.execute('SELECT rfid_uid, action, timestamp FROM logs ORDER BY id DESC LIMIT 6')
print('6 log moi nhat:')
for row in c.fetchall():
    print(f'  {row}')

print()
print('Trang thai hien tai:')
print(f'  6272125C: last={get_last_action("6272125C")}')
print(f'  D5B94F06: last={get_last_action("D5B94F06")}')
conn.close()
