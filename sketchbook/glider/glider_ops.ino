// Servos
#define PARACHUTE_SERVO 6
#define RIGHT_SERVO 9
#define DETACH_SERVO 5
#define LEFT_SERVO 3

void hook_servos()
{
  // Attach Servos
  rightServo.attach(RIGHT_SERVO);
  leftServo.attach(LEFT_SERVO);
  detachServo.attach(DETACH_SERVO);
  parachuteServo.attach(PARACHUTE_SERVO);
  Serial.println("Servos hooked");
}

void processData() {
  commandReady = false;
  // Go figure out what to do
  if(strstr(command_buff, "W:")) {
    char *str;
    char *p = command_buff;
    int count = 0;
    
    while ((str = strtok_r(p, ":", &p)) != NULL) {
      if (!strstr(str, "W")) {
        if (count == 0) {
          // Left
          angWingL = atoi(str);
        } else {
          angWingR = atoi(str);
        }
        count = count + 1;
      }
    }
  }
  
  if(strstr(command_buff, "D:")) {
    angDetach = 0;
  }

  if(strstr(command_buff, "P:")) {
    angParachute = 45;
  }
}

void setServo(){
  leftServo.write(angWingL);
  rightServo.write(angWingR);
  detachServo.write(angDetach);
  parachuteServo.write(angParachute);
}
