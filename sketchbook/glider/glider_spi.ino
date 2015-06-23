// http://www.gammon.com.au/forum/?id=10892
// http://mitchtech.net/raspberry-pi-arduino-spi/
unsigned int output_pos = 0;
const unsigned int MAX_OUTPUT = 200;
static char output_line[MAX_OUTPUT];

unsigned int input_pos = 0;
const unsigned int MAX_INPUT = 20;
static char input_line[MAX_INPUT];


void setup_SPI()
{
  ledblink();
  
  // have to send on master in, *slave out*
  pinMode(MISO, OUTPUT);  
  // turn on SPI in slave mode
  SPCR |= _BV(SPE);
  // turn on interrupts
  SPCR |= _BV(SPIE);
  
  attachInterrupt (0, ss_falling, FALLING);
  
}

// start of transaction, no command yet
void ss_falling ()
{
  clearSPIBuffer();
}  // end of interrupt service routine (ISR) ss_falling


// SPI interrupt routine
ISR (SPI_STC_vect)
{
  char c = SPDR;

  switch (c) {
    case '$':   // start of text
      clearSPIBuffer();
      SPDR = c;
      break;
      
    case ';':   // end of text
      input_line [input_pos] = '\0';  // terminating null byte
      processSPIBuffer(input_pos);
      SPDR = c;
      break;
    
    case '-': // This is the "Send response" char
      SPDR = output_line[output_pos];
      output_pos++;
      break;
      
    default:
      // keep adding if not full ... allow for terminating null byte
      if (input_pos < (MAX_INPUT - 1)){
        input_line [input_pos++] = c;
      } else {
        clearSPIBuffer();        
      }
      SPDR = c;
      break;
  }

}  // end of interrupt service routine (ISR) SPI_STC_vect

  
void clearSPIBuffer(){
  // http://stackoverflow.com/questions/1559487/how-to-empty-a-char-array
  input_line[0] = '\0';
  input_pos = 0;
}

void processSPIBuffer(int index){
  Serial.print("Handling: ");
  Serial.println(input_line);
  processData(input_line, index);
}

void setSPIResponse(char* response){
  int size = strlen(response);
  Serial.print("Setting telemetry ");
  Serial.print(size);
  Serial.println(" chars");
  strncpy(output_line, response, size);
  output_line[size+1] = '\0';
  Serial.print("Output: ");
  Serial.println(output_line);
  output_pos = 0;
}
