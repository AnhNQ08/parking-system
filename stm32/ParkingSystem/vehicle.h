#ifndef VEHICLE_H
#define VEHICLE_H

struct Xe {
  const char* uid;
  const char* bienSo;
};

extern Xe danhSachXe[];
extern const int SO_XE;
extern bool trangThaiXe[];

int timXe(const char* uid);

#endif