#include <SPI.h>
#include <Servo.h>
#include <util/crc16.h>

// Pins
#define SPI_SS 10

Servo leftServo;
Servo rightServo;
Servo parachuteServo;
Servo detachServo;

int angWingL = 90;
int angWingR = 90;
int angParachute = 90;
int angDetach = 90;

char command_buff [16];
bool commandReady = false;


void setup() {
//  pinMode(GPSENABLE, OUTPUT);
  pinMode(SPI_SS, OUTPUT);

  Serial.begin(19200);
  
  // Setup Servos
  hook_servos();

  // Setup SPI
  setup_SPI();
}

void loop() {
  if (commandReady){
    processData();
    Serial.print("Angles: ");
    Serial.print(angWingL);
    Serial.print(" ");
    Serial.print(angWingR);
    Serial.print(" ");
    Serial.print(angDetach);
    Serial.print(" ");
    Serial.print(angParachute);
    Serial.println(" ");
    setServo();
  }
}


