from flask import Flask, render_template, jsonify, request
from db import init_db, get_logs, check_auth, get_last_action, insert_log
from serial_arduino import monitor
import threading
import re

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

                print(f"[*] UID={uid} | Truoc={last} | Dang kiem tra bao mat AI...")
            
            # 1. Chụp ảnh (Sync)
            img_url, full_path = monitor._capture_image()
            
            # 2. Xử lý AI ngay lập tức (Sync)
            from plate_recognition import read_license_plate
            ai_plate = None
            if full_path:
                ai_plate = read_license_plate(full_path)
            
            # 3. Logic So Khớp (Security Match)
            # Biển đăng ký trong DB: plate (VD: A1)
            # Biển AI đọc được: ai_plate (VD: A1 hoặc A4)
            
            access_granted = False
            match_reason = ""
            
            if not ai_plate:
                match_reason = "KHONG THAY BIEN"
                access_granted = False 
            else:
                # SO KHOP TUYET DOI (Bỏ qua ký tự đặc biệt như dấu gạch ngang)
                # Plate DB: 30-A1 -> 30A1
                # AI Plate: 30A1
                clean_db = re.sub(r'[^A-Z0-9]', '', plate.upper())
                clean_ai = re.sub(r'[^A-Z0-9]', '', ai_plate.upper())
                
                if clean_ai == clean_db:
                    access_granted = True
                    match_reason = f"KHOP: {ai_plate}"
                else:
                    access_granted = False
                    match_reason = f"SAI: {ai_plate}!=DB:{plate}"

            if access_granted:
                if direction == 'OUT':
                    cmd = f'[OPEN_OUT]{ai_plate}'
                else:
                    cmd = f'[OPEN_IN]{ai_plate}'
                print(f">>> CHAP THUAN: {match_reason}")
                status_rsp = "granted"
                log_action = direction
            else:
                # Sửa message ngắn gọn để hiện lên LCD chuẩn
                cmd = "[DENIED]SAI BIEN SO"
                print(f">>> TU CHOI: {match_reason}")
                status_rsp = "denied"
                log_action = "SAI BIEN SO"

            # Ghi log kết quả cuối cùng
            from db import insert_log
            insert_log(plate=(ai_plate if ai_plate else "NONE"), action=log_action, rfid_uid=uid, image_url=img_url)

            return jsonify({
                "status": status_rsp,
                "plate": ai_plate if ai_plate else "UNKNOWN",
                "command": cmd
            })

        else:
            # XE LẠ: Thẻ chưa có trong Database
            monitor._process_log(f"[THE LA] {uid}")
            # Ghi log vao database
            from db import insert_log
            insert_log(plate="UNKNOWN", action="THE LA", rfid_uid=uid)
            
            return jsonify({
                "status": "denied", 
                "command": "[DENIED]THE LA"
            })

    # Nếu là log thông thường (IN/OUT đã được STM32 xác nhận hoặc log hệ thống)
    monitor._process_log(log_line)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    monitor.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
