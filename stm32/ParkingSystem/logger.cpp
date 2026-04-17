#include <Arduino.h>

void logEvent(const char* bienSo, const char* status) {
  Serial.print("[LOG] ");
  Serial.print(bienSo);
  Serial.print(" - ");
  Serial.println(status);
}