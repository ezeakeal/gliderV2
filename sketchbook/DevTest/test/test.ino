#include <Servo.h>
#include <SoftwareSerial.h>

#define SWSER_TX 7
#define SWSER_RX 8
SoftwareSerial gpsSerial(SWSER_TX, SWSER_RX);

Servo leftServo;
Servo rightServo;
Servo parachuteServo;
Servo detachServo;

int i;
// the setup routine runs once when you press reset:
void setup() {
  gpsSerial.begin(9600); 
  rightServo.attach(6);  // attaches the servo on pin 9 to the servo object
  leftServo.attach(9);  // attaches the servo on pin 9 to the servo object
  detachServo.attach(5);
  parachuteServo.attach(3);
  i = 0;
}

// the loop routine runs over and over again forever:
void loop() {
  i++;
  i = i % 90;
    leftServo.write(i);
    rightServo.write(i);
    parachuteServo.write(i);
    detachServo.write(i);
    delay(20);
}

