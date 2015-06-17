#include <SPI.h>
#include <PWMServo.h>
#include <SoftwareSerial.h>
#include <util/crc16.h>

// Pins
// #define GPSENABLE 2
#define SPI_SS 10
#define PIN_TELEM 7


// Create Servo instances
// Use PWMServo which uses PWM rather than.. the other type.
//    the ATMEGA328 has 4 PWM pins.
//    we could include other servos like the gimbal ones now
//    but there is jitter on the other pins when they are 
//    being used as servos. This is because SoftwareSerial
//    grabs the timer they use, and can interfer with it
//    So maybe use Parachute/Release Servos on dodgy servo pins
PWMServo leftServo;
PWMServo rightServo;
PWMServo parachuteServo;
PWMServo detachServo;

// Other constants
unsigned int telemIndex = 0;

void setup() {
//  pinMode(GPSENABLE, OUTPUT);
  pinMode(SPI_SS, OUTPUT);

  Serial.begin(19200);
  
  // Lock Servo positions
  ledblink();
  initServoPos();

  // Setup GPS
  // setup_GPS();
  
  // Setup Servos
  ledblink();
  hook_servos();
  demo_servo_loop();
  
  // Setup SPI
  setup_SPI();
}

void loop() {
//  demo_servo_loop();
  // SPI_clear();
}

char* constructTelemetry(){
  int p = 100; // readPressure();
  int r = 100; // readThermister();
  int t = 100; // readTemperature_LM35();
  char* gpsBuffer = 0;
  if (readGPS()){
    gpsBuffer = getGPS();
    gpsBuffer[ strlen(gpsBuffer) - 1 ] = '\0';
  }  
  char buf[150];
  snprintf(buf, sizeof buf, "T|%05d|%ld|%s|%010d|%010d|%010d|", telemIndex, millis(), gpsBuffer, p, r, t);
  int size = strlen(buf);
  sprintf(buf, "%s%d", buf, size);
  return buf;
}

void sendStr(char* msg){
  telemIndex++;
  setSPIResponse(msg);
}



