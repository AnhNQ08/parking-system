import sqlite3, os

db = os.path.join(os.path.dirname(__file__), 'parking.db')
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("INSERT OR REPLACE INTO authorized_vehicles (rfid_uid, plate_number, owner_name) VALUES ('6272125C', '51A-12345', 'Chu xe 1')")
c.execute("INSERT OR REPLACE INTO authorized_vehicles (rfid_uid, plate_number, owner_name) VALUES ('D5B94F06', '51B-67890', 'Chu xe 2')")
conn.commit()

print("Da dang ky 2 the thanh cong!")
c.execute("SELECT * FROM authorized_vehicles")
for row in c.fetchall():
    print(row)

conn.close()
