#include "config.h"
#include "pins.h"
#include "rfid.h"
#include "vehicle.h"
#include "lcd_display.h"
#include "servo_control.h"
#include "logger.h"

char lastUID[20] = "";
unsigned long lastScan = 0;

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  lcdInit();
  servoInit();
  rfidInit();

  showWelcome();
}

void loop() {

  updateServo();

  char uidStr[20];

  if (!readUID(uidStr)) return;

  // 🔥 FIX chống quét trùng (QUAN TRỌNG)
  if (strcmp(uidStr, lastUID) == 0) {
    if (millis() - lastScan < 1200) return;
  }

  strcpy(lastUID, uidStr);
  lastScan = millis();

  digitalWrite(LED_PIN, LOW);

  showScanning();
  delay(500);   // 🔥 cho người dùng nhấc thẻ

  int viTri = timXe(uidStr);

  if (viTri == -1) {

    showUnknown(uidStr);
    Serial.println("[XE LA]");

  } else {

    const char* bienSo = danhSachXe[viTri].bienSo;

    // 🔥 FIX CHÍNH: toggle trạng thái
    if (trangThaiXe[viTri] == false) {

      trangThaiXe[viTri] = true;

      showPlate(bienSo, "VAO");
      openIn();
      logEvent(bienSo, "IN");

    } else {

      trangThaiXe[viTri] = false;

      showPlate(bienSo, "RA");
      openOut();
      logEvent(bienSo, "OUT");
    }
  }

  delay(800);  // 🔥 bắt buộc để nhả thẻ
  digitalWrite(LED_PIN, HIGH);
}