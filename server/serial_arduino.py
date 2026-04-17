import serial
import serial.tools.list_ports
import threading
import time
import requests
import os
import sys
from datetime import datetime
from db import insert_log

# Fix Windows console encoding for Vietnamese prints
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

CAMERA_IP = "http://10.206.163.165"

class SerialMonitor:
    def __init__(self, port=None, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.thread = None

    def start(self):
        if not self.port:
            self.port = self.find_stm32_port()
            
        if self.port:
            try:
                self.serial_conn = serial.Serial()
                self.serial_conn.port = self.port
                self.serial_conn.baudrate = self.baudrate
                self.serial_conn.timeout = 1
                self.serial_conn.setDTR(False)
                self.serial_conn.setRTS(False)
                self.serial_conn.open()
                
                self.running = True
                self.thread = threading.Thread(target=self._read_loop, daemon=True)
                self.thread.start()
                print(f"[*] Đã kết nối ổn định với Serial trên cổng {self.port}")
            except Exception as e:
                print(f"[!] Không thể mở cổng {self.port}: {e}")
        else:
            print("[!] Không tìm thấy thiết bị STM32/Arduino nào được cắm vào.")

    def stop(self):
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()

    def find_stm32_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "CH340" in port.description or "CP2102" in port.description or "STM32" in port.description or "USB" in port.description:
                return port.device
        if ports:
            return ports[0].device
        return None

    def _capture_image(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            save_path = os.path.join(static_dir, 'captures')
            os.makedirs(save_path, exist_ok=True)
            
            print(f"[*] Đang chụp ảnh từ {CAMERA_IP}...")
            resp = requests.get(f"{CAMERA_IP}/capture", timeout=5)
            if resp.status_code == 200:
                full_path = os.path.join(save_path, filename)
                with open(full_path, 'wb') as f:
                    f.write(resp.content)
                return f"/static/captures/{filename}"
            else:
                print(f"[!] Lỗi chụp từ camera. Status code: {resp.status_code}")
        except Exception as e:
            print(f"[!] Không thể gọi API Camera ESP32: {e}")
        return ""

    def _read_loop(self):
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    if self.serial_conn.in_waiting > 0:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            print(f"[STM32]: {line}")
                            self._process_log(line)
                else:
                    self._reconnect()
            except Exception as e:
                err_msg = str(e)
                # Chỉ in lỗi nếu không dính spam PermissionError
                if "PermissionError" not in err_msg and "ClearCommError" not in err_msg:
                    print(f"[!] Mất kết nối Serial: {e}")
                
                # Cố gắng đóng và kết nối lại
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
                
                time.sleep(2)
                self._reconnect()

    def _reconnect(self):
        try:
            if not self.serial_conn.is_open:
                self.serial_conn.open()
                print(f"[*] Đã kết nối lại thành công với cổng {self.port}!")
        except:
            time.sleep(1)

    def _process_log(self, line):
        action = "UNKNOWN"
        plate = "UNKNOWN"
        uid = "UNKNOWN"
        
        # Dựa vào cách code trong ParkingSystem.ino
        if "[XE LA]" in line:
            action = "UNAUTHORIZED"
            uid = line.replace("[XE LA]", "").strip()
        elif "IN" in line or "VAO" in line:
            action = "IN"
            # Cố gắng lấy biển số (ví dụ: "IN - 29A-1234") -> tùy theo code ở ESP/STM
            parts = line.split()
            if len(parts) > 1:
                plate = parts[-1]
        elif "OUT" in line or "RA" in line:
            action = "OUT"
            parts = line.split()
            if len(parts) > 1:
                plate = parts[-1]
            
        # Nếu có sự kiện xảy ra, chạy ở dạng Thread rẽ nhánh (Không chặn luồng quét thẻ)
        if action in ["IN", "OUT", "UNAUTHORIZED"]:
            def run_capture_and_log():
                img_path = self._capture_image()
                insert_log(plate=plate, action=action, rfid_uid=uid, image_url=img_path)
            
            threading.Thread(target=run_capture_and_log, daemon=True).start()
            
monitor = SerialMonitor()
