from flask import Flask, render_template, jsonify, request
from db import init_db, get_logs, check_auth, get_last_action, insert_log
from serial_arduino import monitor
import threading

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def api_logs():
    return jsonify(get_logs(20))

@app.route('/api/remote-log', methods=['POST'])
def remote_log():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"})
        
    log_line = data.get('log', '')
    if not log_line:
        return jsonify({"status": "success"})

    print(f"[Gateway]: {log_line}")

    # XỬ LÝ LÔGIC XÁC THỰC THẺ (TỪ XA)
    if "[SCAN]" in log_line:
        uid = log_line.split("[SCAN]")[1].strip().upper()
        plate = check_auth(uid)
        
        if plate:
            # Toggle: xe đang trong bãi (IN) → mở cổng RA, ngược lại mở cổng VÀO
            last = get_last_action(uid)
            if last == 'IN':
                direction = 'OUT'
                cmd = f'[OPEN_OUT]{plate}'
            else:
                direction = 'IN'
                cmd = f'[OPEN_IN]{plate}'

            print(f"[*] UID={uid} | Truoc={last} | Mo cong: {direction}")

            # Ghi log + chụp ảnh trong background (không chặn response về STM32)
            def capture_and_log(uid=uid, plate=plate, direction=direction):
                from plate_recognition import read_license_plate
                img_url, full_path = monitor._capture_image()
                final_plate = plate
                if full_path:
                    cam_plate = read_license_plate(full_path)
                    if cam_plate:
                        print(f"[OCR] Biển số nhận diện: {cam_plate}")
                        final_plate = cam_plate
                insert_log(plate=final_plate, action=direction, rfid_uid=uid, image_url=img_url)
                print(f"[DB] Đã ghi log: {final_plate} | {direction} | {uid}")

            threading.Thread(target=capture_and_log, daemon=True).start()

            return jsonify({
                "status": "granted",
                "plate": plate,
                "command": cmd
            })

        else:
            # XE LẠ: Gửi lệnh từ chối, vẫn ghi log 'XE LA' để cảnh báo
            monitor._process_log(f"[XE LA] {uid}")
            return jsonify({
                "status": "denied", 
                "command": "[DENIED]"
            })

    # Nếu là log thông thường (IN/OUT đã được STM32 xác nhận hoặc log hệ thống)
    monitor._process_log(log_line)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    monitor.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
