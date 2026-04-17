#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

void lcdInit() {
  lcd.init();
  lcd.backlight();
}

void showWelcome() {
  lcd.clear();
  lcd.print("SAN SANG QUET");
}

void showScanning() {
  lcd.clear();
  lcd.print("Dang quet...");
}

void showPlate(const char* bienSo, const char* status) {
  lcd.clear();
  lcd.print(bienSo);
  lcd.setCursor(0, 1);
  lcd.print(status);
}

void showUnknown(const char* uid) {
  lcd.clear();
  lcd.print("XE LA");
  lcd.setCursor(0, 1);
  lcd.print(uid);
}