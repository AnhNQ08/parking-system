# Smart Parking System

An IoT-based Smart Parking management system combining RFID access control, video streaming, and a real-time web dashboard.

## 🚀 Tính Năng (Features)

- **STM32 Core Logic**: Cốt lõi quản lý hệ thống nằm ở bo mạch kiểm soát vật lý. Nhận diện thẻ RFID (RC522), điều khiển Barie tự động, và hiển thị trạng thái bằng LCD 16x2. Code khắc phục hoàn toàn tính trạng quét đụng độ, chống nhiễu MISO/MOSI ổn định.
- **ESP32-CAM Stream**: Tạo luồng phát sóng Video chất lượng cao qua WiFi dùng làm Camera giám sát. Giới hạn quy hoạch bộ nhớ RAM kỹ để không bị sập nguồn.
- **Web Dashboard**: Giao diện Giám sát hiện đại xây dựng theo thiết kế Glassmorphism (Dark Mode). Tự động cập nhật thời gian thực sự kiện VÀO/RA/XE LẠ và xem Live Camera từ xa.
- **Python Backend**: Xây dựng bằng Flask. Hoạt động trên cơ chế bám tín hiệu Serial đa luồng không bị nghẽn (Robust Auto-Reconnect). Tự động phát hiện khi thẻ được quét và nháy lấy hình ảnh capture trên Camera để lưu lại.
- **Database Logs**: Lưu vết trên SQLite. Toàn bộ lịch sử hành vi (thời gian, loại sự kiện, UID RFID và ảnh chụp ảnh) đều được lưu trữ hoàn hảo.

## 📁 Cấu Trúc Dự Án

- `stm32/`: Mã nguồn C/C++ lập trình trên chip STM32 đúc nối các linh kiện module phần cứng.
- `esp32-cam/`: Mã nguồn dùng để nạp cho ESP32-Cam.
- `server/`: Backend Python (Flask), Trình giao tiếp Pyserial đa luồng, SQLite Database, UI Dashboard.

## 🛠 Yêu Cầu Cài Đặt

- Python 3.9+
- Arduino IDE (Đã thiết lập board môi trường STM32 và ESP32).
- Khái niệm về dòng/điện áp (Cần cấp nguồn nuôi Servo riêng).

## 🔧 Triển Khai (Setup)

1. **Phần cứng**:
   - Nạp code ở thư mục `esp32-cam` vào vi điều khiển tĩnh.
   - Nạp mã `ParkingSystem.ino` vào STM32. 
   - *Lưu ý quan trọng: Nhớ cắm nối chung dây điện cực âm (GND) giữa tất cả các nguồn với nhau!*

2. **Chạy Server**:
   ```bash
   cd server
   pip install -r requirements.txt
   python app.py
   ```

3. **Truy cập**: 
   - Đảm bảo mạch kết nối qua cáp USB vào máy tính.
   - Truy cập vào: `http://localhost:5000/`

## 📜 License
MIT License.
