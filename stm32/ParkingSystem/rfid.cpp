#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "pins.h"

MFRC522 mfrc522(SS_PIN, RST_PIN);

void rfidInit() {
  // Cấu hình chân SPI2 cho đối tượng SPI mặc định
  SPI.setSCLK(SCK_PIN);
  SPI.setMISO(MISO_PIN);
  SPI.setMOSI(MOSI_PIN);
  
  // Khởi động SPI
  SPI.begin();
  
  // Thiết lập tốc độ SPI an toàn cho dây cắm (2MHz)
  SPI.setClockDivider(SPI_CLOCK_DIV32);

  // Khởi tạo RFID
  mfrc522.PCD_Init();
  
  if (Serial) {
    Serial.println("[SYSTEM] Dang kiem tra ket noi RFID...");
    byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
    if (v == 0x00 || v == 0xFF) {
      Serial.println("[ERROR] ! Khong tim thay modul RFID RC522. Hay kiem tra lai day cam !");
    } else {
      Serial.print("[SYSTEM] Da tim thay RFID Version: 0x");
      Serial.println(v, HEX);
    }
  }
}

bool readUID(char* uidStr) {
  if (!mfrc522.PICC_IsNewCardPresent()) return false;
  if (!mfrc522.PICC_ReadCardSerial()) return false;

  uidStr[0] = '\0';
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    char buf[3];
    sprintf(buf, "%02X", mfrc522.uid.uidByte[i]);
    strcat(uidStr, buf);
  }

  if (Serial) {
    Serial.print("[RFID] Quet thanh cong UID: ");
    Serial.println(uidStr);
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  return true;
}