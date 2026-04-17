#include <Arduino.h>
#include <Servo.h>
#include "pins.h"
#include "config.h"

Servo servoIn;
Servo servoOut;

bool inOpen = false;
bool outOpen = false;

unsigned long inTime = 0;
unsigned long outTime = 0;

void servoInit() {
  servoIn.attach(SERVO_IN_PIN);
  servoOut.attach(SERVO_OUT_PIN);

  servoIn.write(SERVO_CLOSE);
  servoOut.write(SERVO_CLOSE);
}

void openIn() {
  servoIn.write(SERVO_OPEN);
  inOpen = true;
  inTime = millis();
}

void openOut() {
  servoOut.write(SERVO_OPEN);
  outOpen = true;
  outTime = millis();
}

void updateServo() {
  if (inOpen && millis() - inTime > SERVO_TIME) {
    servoIn.write(SERVO_CLOSE);
    inOpen = false;
  }

  if (outOpen && millis() - outTime > SERVO_TIME) {
    servoOut.write(SERVO_CLOSE);
    outOpen = false;
  }
}