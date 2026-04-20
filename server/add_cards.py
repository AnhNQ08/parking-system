import sys

from db import get_db_connection, init_db


def manage_cards():
    init_db()
    conn = get_db_connection()
    c = conn.cursor()

    print("\n" + "=" * 30)
    print(" DANH SACH XE TRONG HE THONG")
    print("=" * 30)
    c.execute("SELECT rfid_uid, plate_number FROM authorized_vehicles ORDER BY rfid_uid")
    rows = c.fetchall()
    if not rows:
        print(" (Trong - Chua co xe nao)")
    for i, row in enumerate(rows, 1):
        print(f" {i}. UID: {row['rfid_uid']} | Bien so: {row['plate_number']}")
    print("=" * 30 + "\n")

    if len(sys.argv) == 3:
        uid = sys.argv[1].upper()
        plate = sys.argv[2].upper()
    else:
        uid = input("Nhap UID the moi (hoac Enter de thoat): ").strip().upper()
        if not uid:
            conn.close()
            return
        plate = input(f"Nhap bien so cho the {uid}: ").strip().upper()
        if not plate:
            conn.close()
            return

    try:
        c.execute("SELECT rfid_uid FROM authorized_vehicles WHERE rfid_uid = %s", (uid,))
        exists = c.fetchone()

        if exists:
            confirm = input(f"-> The {uid} da ton tai. Ban co muon DOI sang bien so {plate} khong? (y/n): ")
            if confirm.lower() == 'y':
                c.execute("UPDATE authorized_vehicles SET plate_number = %s WHERE rfid_uid = %s", (plate, uid))
                print(f"[OK] Da cap nhat bien so moi: {plate}")
            else:
                print("[!] Huy bo cap nhat.")
        else:
            c.execute(
                "INSERT INTO authorized_vehicles (rfid_uid, plate_number) VALUES (%s, %s)",
                (uid, plate),
            )
            print(f"[OK] Da them xe moi thanh cong: {uid} -> {plate}")

        conn.commit()
    except Exception as e:
        print(f"[LOI] Khong the thao tac: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    manage_cards()
