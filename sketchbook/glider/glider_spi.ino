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
  SPI.usingInterrupt(2);
  // have to send on master in, *slave out*
  pinMode(MISO, OUTPUT);  
  // turn on SPI in slave mode
  SPCR |= _BV(SPE);
  // turn on interrupts
  SPCR |= _BV(SPIE);
}

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
  // Copy the command for later processing..
  strncpy(command_buff, input_line, index);
  command_buff[15] = '\0';
  Serial.print("Command: ");
  Serial.println(command_buff);
  commandReady = true;
}

