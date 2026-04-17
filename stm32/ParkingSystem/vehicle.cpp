#include <Arduino.h>
#include "vehicle.h"
#include <string.h>

Xe danhSachXe[] = {
  {"6272125C", "29A-12345"},
  {"D5B94F06", "30B-67890"}
};

const int SO_XE = 2;
bool trangThaiXe[2] = {false, false};

int timXe(const char* uid) {
  for (int i = 0; i < SO_XE; i++) {
    if (strcmp(danhSachXe[i].uid, uid) == 0) return i;
  }
  return -1;
}