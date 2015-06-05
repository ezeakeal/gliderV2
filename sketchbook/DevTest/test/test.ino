
#include <SoftwareSerial.h>
#define GPSENABLE 2
SoftwareSerial mySerial(12, 13);
int val = 0;
int led = 9;           // the pin that the LED is attached to
int brightness = 0;    // how bright the LED is
int fadeAmount = 5;    // how many points to fade the LED by

// the setup routine runs once when you press reset:
void setup() {
  Serial.begin(57600);
  pinMode(led, OUTPUT);
  pinMode(GPSENABLE, OUTPUT);
  digitalWrite(GPSENABLE, HIGH);
  //  gpsSetup();
}

// the loop routine runs over and over again forever:
void loop() {
  val = Serial.read(); 
  if (val > '0' && val <= '9' ) {
    val = val - '0';          // convert from character to number
    for(int i=0; i<val; i++) {
      digitalWrite(led,HIGH);
      delay(150);
      digitalWrite(led, LOW);
      delay(150);
    }
    delay(1000);
  }
}

