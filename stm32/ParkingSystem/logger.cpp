#include <Arduino.h>
#include <HardwareSerial.h>

HardwareSerial MySerial1(PA10, PA9);
bool isSerialInit = false;

void logEvent(const char* bienSo, const char* status) {
  if (!isSerialInit) {
    MySerial1.begin(115200);
    isSerialInit = true;
  }
  MySerial1.print("[LOG] ");
  MySerial1.print(bienSo);
  MySerial1.print(" - ");
  MySerial1.println(status);
}