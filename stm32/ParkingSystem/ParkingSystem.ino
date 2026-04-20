#include "config.h"
#include "pins.h"
#include "rfid.h"
#include "lcd_display.h"
#include "servo_control.h"

// Trạng thái hệ thống
enum SystemState { IDLE, WAITING_AUTH, GRANTED, DENIED };
SystemState currentState = IDLE;

unsigned long stateStartTime = 0;
char scannedUID[20] = "";

void setup() {
  Serial.begin(115200);   // PA9/PA10 - chỉ dùng debug qua USB
  Serial2.begin(115200);  // PA2/PA3  - giao tiếp ESP32-CAM

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  lcdInit();
  servoInit();
  rfidInit();

  showWelcome();
}

void loop() {
  updateServo(); // Luôn cập nhật vị trí servo mượt mà

  switch (currentState) {
    case IDLE:
      if (readUID(scannedUID)) {
        Serial2.print("[SCAN] ");   // Gửi lên ESP32-CAM qua PA2/PA3
        Serial2.println(scannedUID);

        digitalWrite(LED_PIN, LOW);
        showScanning();

        stateStartTime = millis();
        currentState = WAITING_AUTH;
      }
      break;

    case WAITING_AUTH:
      // Đợi phản hồi từ ESP32-CAM qua Serial2 (PA2/PA3)
      if (Serial2.available()) {
        String cmd = Serial2.readStringUntil('\n');
        cmd.trim();

        if (cmd.startsWith("[OPEN_IN]")) {
          String plate = cmd.substring(9);
          showPlate(plate.c_str(), "VAO - OK");
          openIn();
          stateStartTime = millis();
          currentState = GRANTED;
        }
        else if (cmd.startsWith("[OPEN_OUT]")) {
          String plate = cmd.substring(10);
          showPlate(plate.c_str(), "RA - OK");
          openOut();
          stateStartTime = millis();
          currentState = GRANTED;
        }
        else if (cmd.startsWith("[DENIED]")) {
          String reason = cmd.substring(8); // Lay chu sau [DENIED]
          showUnknown(reason.c_str());
          stateStartTime = millis();
          currentState = DENIED;
        }
      }

      // Timeout nếu Server không phản hồi sau 15 giây (Luồng bảo mật AI)
      if (millis() - stateStartTime > 15000) {
        showUnknown("SRV TIMEOUT");
        stateStartTime = millis();
        currentState = DENIED;
      }
      break;

    case GRANTED:
    case DENIED:
      // Giữ màn hình hiển thị kết quả trong 3 giây rồi quay lại IDLE
      if (millis() - stateStartTime > 3000) {
        digitalWrite(LED_PIN, HIGH);
        showWelcome();
        currentState = IDLE;
      }
      break;
  }
}