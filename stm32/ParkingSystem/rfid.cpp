#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "pins.h"

MFRC522 mfrc522(SS_PIN, RST_PIN);

void rfidInit() {
  SPI.setSCLK(SCK_PIN);
  SPI.setMISO(MISO_PIN);
  SPI.setMOSI(MOSI_PIN);
  SPI.begin();
  // Giảm tốc độ xung nhịp SPI xuống mức an toàn (chống nhiễu khi dùng dây cắm Dupont)
  // STM32 chạy ở 72MHz, DIV32 = 2.25MHz (MFRC522 cực kỳ dễ treo tịt nếu chạy > 4MHz qua dây cắm nổi)
  SPI.setClockDivider(SPI_CLOCK_DIV32);

  mfrc522.PCD_Init();
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

  // 🔥 FIX TREO
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  return true;
}