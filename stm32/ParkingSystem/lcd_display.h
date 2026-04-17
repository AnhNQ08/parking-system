#ifndef LCD_DISPLAY_H
#define LCD_DISPLAY_H

void lcdInit();
void showWelcome();
void showPlate(const char* bienSo, const char* status);
void showUnknown(const char* uid);
void showScanning();

#endif