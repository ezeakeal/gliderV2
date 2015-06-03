#include <Servo.h>
#include <SoftwareSerial.h>
#include <util/crc16.h>

Servo leftServo;  // create servo object to control a servo
Servo rightServo;  // create servo object to control a servo
Servo parachuteServo;
Servo detachServo;

// Pins
#define RADIOPIN 9   // NTX2 TX
#define DETACHSERVO 10
#define RIGHTSERVO 11
#define LEFTSERVO 12
#define PARACHUTESERVO 13
#define LED 14

#define SER_TX 12
#define SER_RX 13


// Other constants
#define BAUD 50

const unsigned int MAX_INPUT = 165;
static unsigned int input_pos = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  pinMode(RIGHTSERVO, OUTPUT);
  pinMode(LEFTSERVO, OUTPUT);
  pinMode(DETACHSERVO, OUTPUT);
  pinMode(PARACHUTESERVO, OUTPUT);
  
  rightServo.attach(RIGHTSERVO);  // attaches the servo on pin 9 to the servo object
  leftServo.attach(LEFTSERVO);  // attaches the servo on pin 9 to the servo object
  detachServo.attach(DETACHSERVO);
  parachuteServo.attach(PARACHUTESERVO);
  
  parachuteServo.write(45);
}

void loop() {
  readSerial();
}

void readSerial() {
  static char input_line[MAX_INPUT];

  if (Serial.available()) {
    while (Serial.available() > 0) {
      char inByte = Serial.read();
      Serial.print("data: ");
      Serial.println(inByte);

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
  Serial.print("*** Data: ");
  Serial.println(data);

  if(strstr(data, "W:")) {
    Serial.println("In W:");
    
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

  if(strstr(data, "R:")) {
    digitalWrite(LED, HIGH);
    delay(1000);
    digitalWrite(LED, LOW);
    delay(100);
    
    char *str;
    char *p = data;
    while ((str = strtok_r(p, ":", &p)) != NULL) {
      if (!strstr(str, "R")) {
        rtty_txstring(BAUD, str);
      }
    }
  }
  
  if(strstr(data, "D:")) {
    Serial.println("Detaching!");
    detachServo.write(180);
  }

  if(strstr(data, "P:")) {
    Serial.println("Parachuting!");
    parachuteServo.write(180);
  }
}

void rotateLeft(int degree) {
  leftServo.write(degree);
}

void rotateRight(int degree) {
  rightServo.write(degree);
}


// RTTY Stuff
void rtty_txstring(int baud, char *string) {
  Serial.print("Transmitting: ");
  Serial.println(string);
  Serial.print("Baud: ");
  Serial.println(baud);

  /* Simple function to sent a char at a time to
    ** rtty_txbyte function.
    ** NB Each char is one byte (8 Bits)
    */

  char c;

  c = *string++;

  while ( c != '\0') {
    rtty_txbyte(baud, c);
    c = *string++;
  }
}


void rtty_txbyte (int baud, char c) {
  /* Simple function to sent each bit of a char to
    ** rtty_txbit function.
    ** NB The bits are sent Least Significant Bit first
    **
    ** All chars should be preceded with a 0 and
    ** proceded with a 1. 0 = Start bit; 1 = Stop bit
    **
    */

  int i;

  rtty_txbit(baud, 0); // Start bit

  // Send bits for for char LSB first

  for (i = 0; i < 7; i++) { // Change this here 7 or 8 for ASCII-7 / ASCII-8
    if (c & 1) rtty_txbit(baud, 1);

    else rtty_txbit(baud, 0);

    c = c >> 1;

  }

  rtty_txbit(baud, 1); // Stop bit
  rtty_txbit(baud, 1); // Stop bit
}

void rtty_txbit (int baud, int bit) {
  if (bit) {
    // high
    analogWrite(RADIOPIN, 138);
  } else {
    // low
    analogWrite(RADIOPIN, 127);
  }

  if (baud == 300) {
    delayMicroseconds(3370); // 300 baud
  } else if (baud == 50) {
    delayMicroseconds(10000); // For 50 Baud uncomment this and the line below.
    delayMicroseconds(10150); // You can't do 20150 it just doesn't work as the
  } else {
    delayMicroseconds(10000); // For 50 Baud uncomment this and the line below.
    delayMicroseconds(10150); // You can't do 20150 it just doesn't work as the
    Serial.println("Unknown Baud - defaulting to 50.");
  }
}

uint16_t gps_CRC16_checksum (char *string) {
  size_t i;
  uint16_t crc;
  uint8_t c;

  crc = 0xFFFF;

  // Calculate checksum ignoring the first two $s
  for (i = 2; i < strlen(string); i++) {
    c = string[i];
    crc = _crc_xmodem_update (crc, c);
  }

  return crc;
}




