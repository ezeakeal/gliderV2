char command_buff [10];

// Servos
#define LEFT_SERVO 9
#define RIGHT_SERVO 6
#define PARACHUTE_SERVO 3
#define DETACH_SERVO 5

void hook_servos()
{
  // Attach Servos
  ledblink();
  rightServo.attach(RIGHT_SERVO);  // attaches the servo on pin 9 to the servo object
  leftServo.attach(LEFT_SERVO);  // attaches the servo on pin 9 to the servo object
  detachServo.attach(DETACH_SERVO);
  parachuteServo.attach(PARACHUTE_SERVO);
  Serial.println("Servos hooked");
}

void readSerial() {

}

void processData(char * data, int len) {
  // Copy the command for later processing..
  strncpy(command_buff, data, 18);
  command_buff[9] = '\0';
  
  // Go figure out what to do
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
    leftServo.write(left);
    rightServo.write(right);
    parachuteServo.write(right);
    detachServo.write(right);
  }
  
  if(strstr(data, "D:")) {
    detachServo.write(180);
  }

  if(strstr(data, "P:")) {
    parachuteServo.write(90);
  }

  if(strstr(data, "G:")) {
    // Construct and send telemetry
    char* telStr = constructTelemetry();
    sendStr(telStr);
  }
}

void ledblink(){
  /*digitalWrite(LED, HIGH);
  digitalWrite(LED_O, HIGH);
  delay(200);
  digitalWrite(LED, LOW);
  digitalWrite(LED_O, LOW);
  delay(200);
  */
}

void initServoPos(){
  leftServo.write(0);
  rightServo.write(0);
  detachServo.write(0);
  parachuteServo.write(0);
}


