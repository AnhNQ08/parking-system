# Tổng hợp các nâng cấp & Lưu ý quan trọng - Smart Parking System

Tài liệu này ghi lại toàn bộ các vấn đề đã được khắc phục và những thay đổi quan trọng trong hệ thống để đảm bảo tính ổn định khi chạy demo và thực tế.

## 1. Khắc phục lỗi Lag/Treo STM32 khi cắm USB
**Nguyên nhân gốc:** 
Xung đột khi sử dụng chung cổng `Serial` (PA9/PA10) cho cả việc nạp/debug qua máy tính và giao tiếp với ESP32-CAM. Ngoài ra, module `serial` của Python theo mặc định sẽ gửi tín hiệu DTR/RTS làm reset vi điều khiển mỗi khi kết nối được mở.

**Cách giải quyết:**
- **Phân tách UART:** Chuyển kết nối truyền nhận ESP32-CAM sang kênh `Serial2` (Chân **PA2 [TX]** và **PA3 [RX]**). Giữ `Serial` (PA9/PA10) dành riêng để nạp code và debug qua cáp USB.
- **Vô hiệu hóa DTR/RTS:** Đã thêm cấu hình tắt tín hiệu `DTR` và `RTS` bên phía server Python (`serial_arduino.py`) để ngăn Python tự động reset STM32.
- **Chống Blocking Loop:** Quấn các lệnh `Serial.print` trong khối `if (Serial)` bên trong `rfid.cpp` để vòng lặp chính của STM32 không bị đứng khung đợi khi cáp USB bị rút ra khỏi máy tính.

> **Lưu ý phần cứng quan trọng:** 
> Đảm bảo dây `U0R` của camera đã rút khỏi `PA9` để cắm vào `PA2`, và dây `U0T` đã tháo khỏi `PA10` để cắm vào `PA3`. 

---

## 2. Logic cập nhật: Điều khiển độc lập cổng VÀO / RA 
**Nguyên nhân gốc:**
Code ban đầu không hề gọi hàm `openOut()` (mở cổng RA), khiến xe chỉ có thể đi vào không thể đi ra. Server không ghi nhớ trạng thái thẻ đang nằm ở bãi trong hay ngoài.

**Cách giải quyết:**
- **Truy vấn Toggle State:** Khi quét thẻ đúng, thay vì luôn gửi `[OPEN]`, server (`app.py`) sẽ truy xuất DB SQLite (`logs`) để xem lệnh xe thực hiện gần nhất là gì thông qua hàm `get_last_action`.
- **Cơ chế ra quyết định:** 
  - Nếu xe chưa có lịch sử, hoặc lần cuối là `OUT` -> Xe đang ở ngoài -> Gửi lệnh `[OPEN_IN]`.
  - Nếu lần cuối là `IN` -> Xe đang ở bãi -> Gửi lệnh `[OPEN_OUT]`.
- STM32 đã được cập nhật (`ParkingSystem.ino`) để đọc bắt hai chuỗi mới và điều khiển đúng servo PA8 cho cổng VÀO, servo PA1 cho cổng RA.

---

## 3. Tối ưu chụp ảnh & Khắc phục ESP32-CAM bị mất ảnh
**Nguyên nhân gốc:**
Camera thỉnh thoảng không bắt được hình do ESP32-CAM có năng lực xử lý giới hạn, không thể đồng thời thực hiện lệnh đẩy dữ liệu quét thẻ `[SCAN]`, nhận response mở cửa và gọi hàm phục vụ luồng hình ảnh `GET /capture` ở đúng cùng 1 tíc-tắc. Nền tảng quá tải, sinh ra hiện tượng timeout.

**Cách giải quyết:**
- **Background Threading:** Tại Server (`app.py`), trả output response (jsonify) mở cổng về cho STM32 ngay lập tức, rồi đẩy quá trình fetch ảnh + OCR sang một tiến trình background thread chạy nền độc lập. Không block quá trình mở cửa cơ học.
- **Delay & Retry Logic:** Trong `serial_arduino.py` API chụp, thiết lập ngắt nghỉ bắt buộc `time.sleep(1.5)` đợi camera nhả bộ nhớ làm việc UART trước khi yêu cầu nó kéo data hình. Bổ sung cơ chế thử lại (Retry) 3 lần, tự động loại bỏ các ảnh quá bé `< 1000 bytes` (do bị rách buffer).

---

## 4. Làm mới Pipeline Nhận diện Biển số (OCR) - Nâng cấp EasyOCR
**Nguyên nhân gốc:**
Tesseract (mô hình cũ) rất khó đọc các đoạn chữ ngắn (2-3 ký tự) và hay bị "ảo giác" khi gặp ảnh chất lượng thấp từ ESP32-CAM.

**Cách giải quyết:**
- **Chuyển sang EasyOCR:** Sử dụng mô hình Deep Learning mạnh mẽ hơn (Deep Learning based OCR). 
- **Nhận diện tự do:** Đã bỏ các ràng buộc Regex biển số khắt khe. Bây giờ hệ thống có thể đọc tốt cả các mẩu giấy test chỉ có 2-3 ký tự của bạn.
- **Scoring thông minh:** Ưu tiên kết quả có độ tự tin (Confidence) cao nhất từ mô hình.

## 5. Chỉnh sửa lật hình Camera (V Flip & H Mirror)
**Vấn đề:** Hình ảnh stream bị ngược 180 độ.
**Khắc phục:** Đã thêm cấu hình `s->set_vflip(s, 1);` và `s->set_hmirror(s, 1);` vào `CameraWebServer.ino`. Hình ảnh bây giờ sẽ xuôi chiều tự nhiên.

---

## Các thao tác demo
- **Cài đặt thư viện:** Đã cài đặt `easyocr` (lần đầu chạy sẽ mất khoảng 1-2 phút để server tải mô hình AI về, các lần sau sẽ rất nhanh).
- **Lưu ý ESP32-CAM:** **BẮT BUỘC** nạp lại code cho ESP32-CAM (`CameraWebServer.ino`) để áp dụng lệnh lật hình.
- **Xóa / Reset Test Data:** Chạy câu lệnh sql `DELETE FROM logs` nhưng chừa bảng `authorized_vehicles` khi muốn reset trạng thái của cả bãi xe.
- Khi chạy lại không cần nạp code STM, chỉ việc chạy lại python app (`python app.py`) là đủ.
