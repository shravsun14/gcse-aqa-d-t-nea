import spidev # Library to control hardware SPI for the MCP3008
import RPi.GPIO as GPIO # Library to control the GPIO pins to control the MOSFET
import time # Library to add waiting breaks

PUMP_PIN = 17   # Changed from 2 to 17 because 2 had a hardware 'Pull-Up Resistor', 
#                 which meant the Pi turned on the pump during boot. 
SENSOR_CHANNEL = 0 # Channel of sensor connected to ADC

GPIO.setmode(GPIO.BCM) # Sets pins to be recognised by GPIO No., not Pin No.
GPIO.setup(PUMP_PIN, GPIO.OUT) # To configure specific pins (pump pin) to be output

spi = spidev.SpiDev() # Initialises the SPI software object
spi.open(0, 0)     # Connects software object to specific port, 
#                    First 0 sets pins to be recognised by hardware SPI's GPIO 9/10 pins
#                    Second 0 sets Chip Select pin to CE0 (since RPi has 2 chip select pins)
spi.max_speed_hz = 1000000 # Sets communication speed to 1MHz, since being too fast causes interference 
#                            and being too slow leads to code being inefficient

def read_channel(channel): # Function created to prevent writing of same code multiple times.
    adc = spi.xfer2([1, (8 + channel) << 4, 0]) # Sends 3 bytes to the chip and chip sends back 3 bytes which is stored
                                                # Byte 1: To 'wake up' the chip
                                                # Byte 2: Configuration byte: '8' sets chip to compare input to Ground 0V
                                                #         '<< 4' shifts bits to start of byte to chip reads them first
                                                # Byte 3: Dummy Byte to keep connection open
    data = ((adc[1] & 3) << 8) + adc[2] # Chip returns an integer 0-1023 but as 2 8-bit packages, which have to be combined
    return data

print('----------------------------------------')
print('Hardware Test Started')
time.sleep(1)

pump_on = input('Turn Pump ON? [y/n]') # Asks whether pump should also be on, 
#                                        as having pump on without water damages it.

try:
    if pump_on == 'y':
        print('Turning Pump ON... | Reading Sensor Values...')
        GPIO.output(PUMP_PIN, GPIO.HIGH) # Sets value to High, activating pump
        while True:
            moisture_level = read_channel(SENSOR_CHANNEL)
            print('Pump: ON | Sensor Reading:', moisture_level)     # Reads value every 2 seconds
            time.sleep(2)
    else:
        print('Reading Sensor Values Only...')
        while True:
            moisture_level = read_channel(SENSOR_CHANNEL)
            print('Pump: OFF | Sensor Reading:', moisture_level)    # Reads value every 2 seconds
            time.sleep(2)

except KeyboardInterrupt: # When program stopped, safety stops the pump.
    print('\nProgram interrupted. Stopping...') 
    GPIO.output(PUMP_PIN, GPIO.LOW)
    GPIO.cleanup()
    print('GPIO Cleaned Up. Exiting program...')


