#include <Servo.h>
#include <SoftwareSerial.h>
#include <util/crc16.h>

// Pins
#define GPSENABLE 2
#define LED 8
#define LED_O 7
#define PIN_TELEM 7
// Pins-Servos
#define LEFT_SERVO 3
#define RIGHT_SERVO 5
#define PARACHUTE_SERVO 6
#define DETACH_SERVO 11
#define GIMBAL_H_SERVO 10
#define GIMBAL_V_SERVO 9
// SWSerial 


// Create Servo instances
Servo leftServo;  // create servo object to control a servo
Servo rightServo;  // create servo object to control a servo
Servo parachuteServo;
Servo detachServo;
Servo gimbalHServo;
Servo gimbalVServo;

// Other constants
const unsigned int MAX_INPUT = 165;
unsigned int input_pos = 0;
unsigned int telemIndex = 0;

void setup() {
  Serial.begin(19200);
  // Setup the GPS
  ledblink();
  ledblink();
  pinMode(GPSENABLE, OUTPUT);
//  digitalWrite(GPSENABLE, HIGH);
  // Setup our LEDs
  ledblink();
  pinMode(LED, OUTPUT);
  pinMode(LED_O, OUTPUT);
  // Setup Servos
  ledblink();
  pinMode(RIGHT_SERVO, OUTPUT);
  pinMode(LEFT_SERVO, OUTPUT);
  pinMode(DETACH_SERVO, OUTPUT);
  pinMode(PARACHUTE_SERVO, OUTPUT);
  // Attach Servos
  ledblink();
  rightServo.attach(RIGHT_SERVO);  // attaches the servo on pin 9 to the servo object
  leftServo.attach(LEFT_SERVO);  // attaches the servo on pin 9 to the servo object
  detachServo.attach(DETACH_SERVO);
  parachuteServo.attach(PARACHUTE_SERVO);
  gimbalHServo.attach(GIMBAL_H_SERVO);
  gimbalVServo.attach(GIMBAL_V_SERVO);
  
  // Lock Servo positions
  ledblink();
  parachuteServo.write(45);

  // Setup GPS
  ledblink();
  gpsSetup();
  Serial.flush();
}

void loop() {
  readSerial();
}

void readSerial() {
  static char input_line[MAX_INPUT];

  if (Serial.available()) {
    while (Serial.available() > 0) {
      char inByte = Serial.read();
      digitalWrite(LED, HIGH);
      delay(10);
      digitalWrite(LED, LOW);

      switch (inByte) {

      case ';':   // end of text
        input_line [input_pos] = 0;  // terminating null byte

        // terminator reached! process input_line here ...
        processData(input_line);

        // reset buffer for next time
        input_pos = 0;
        break;

      case '\r':   // treat as newline
        break;

      default:
        // keep adding if not full ... allow for terminating null byte
        if (input_pos < (MAX_INPUT - 1))
          input_line [input_pos++] = inByte;
        break;
      }
    }
  }
}


void processData(char * data) {
  // display the data
  if(strstr(data, "W:")) {
    char *str;
    char *p = data;
    int count = 0;
    int left = 0;
    int right = 0;
    while ((str = strtok_r(p, ":", &p)) != NULL) {
      if (!strstr(str, "W")) {
        if (count == 0) {
          // Left
          left = atoi(str);
        } else {
          right = atoi(str);
        }
        count = count + 1;
      }
    }
    
    rotateLeft(left);
    rotateRight(right);
  }

  if(strstr(data, "T:")) {
    char *str;
    char *p = data;
    int count = 0;
    int left = 0;
    int right = 0;
    while ((str = strtok_r(p, ":", &p)) != NULL) {
      if (!strstr(str, "T")) {
        if (count == 0) {
          // Left
          left = atoi(str);
        } else {
          right = atoi(str);
        }
        count = count + 1;
      }
    }
    
    pointH(left);
    pointV(right);
  }

  if(strstr(data, "R:")) {   
    char *str;
    char *p = data;
    while ((str = strtok_r(p, ":", &p)) != NULL) {
      if (!strstr(str, "R")) {

      }
    }
  }
  
  if(strstr(data, "D:")) {
    detachServo.write(180);
  }

  if(strstr(data, "P:")) {
    parachuteServo.write(90);
  }

  if(strstr(data, "G:")) {
    digitalWrite(LED, HIGH);
    // Construct and send telemetry
    char* telStr = constructTelemetry();
    sendStr(telStr);
    digitalWrite(LED, LOW);
  }
}

void rotateLeft(int degree) {
  leftServo.write(degree);
}

void rotateRight(int degree) {
  rightServo.write(degree);
}

void pointH(int degree) {
  gimbalHServo.write(degree);
}

void pointV(int degree) {
  gimbalVServo.write(degree);
}

void ledblink(){
  digitalWrite(LED, HIGH);
  digitalWrite(LED_O, HIGH);
  delay(200);
  digitalWrite(LED, LOW);
  digitalWrite(LED_O, LOW);
  delay(200);
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
  char buf[350];
  snprintf(buf, sizeof buf, "T|%05d|%ld|%s|%010d|%010d|%010d|", telemIndex, millis(), gpsBuffer, p, r, t);
  int size = strlen(buf);
  sprintf(buf, "%s%d", buf, size);
  return buf;
}

void sendStr(String msg){
  digitalWrite(PIN_TELEM, LOW);
  Serial.println(msg);
  Serial.flush();
  digitalWrite(PIN_TELEM, HIGH);
  telemIndex++;
}
