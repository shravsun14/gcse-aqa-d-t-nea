import time
import RPi.GPIO as GPIO
import spidev
import config
import subprocess

GPIO.setmode(GPIO.BCM)

GPIO.setup(config.MOSFET_GPIO, GPIO.OUT)
GPIO.output(config.MOSFET_GPIO, GPIO.LOW)

spi = spidev.SpiDev() 
spi.open(0, 0) 
spi.max_speed_hz = 1000000

def turn_lights_on():
    subprocess.run(['sudo', 'uhubctl', '-l', '1', '-a', '1'], capture_output=True)
    subprocess.run(['sudo', 'uhubctl', '-l', '3', '-a', '1'], capture_output=True)

def turn_lights_off():
    subprocess.run(['sudo', 'uhubctl', '-l', '1', '-a', '0'], capture_output=True)
    subprocess.run(['sudo', 'uhubctl', '-l', '3', '-a', '0'], capture_output=True)

def read_moisture():
    adc = spi.xfer2([1, (8 + config.SENSOR_CHANNEL) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def pump_on():
    GPIO.output(config.MOSFET_GPIO, GPIO.HIGH)
    time.sleep(config.PUMP_DURATION)
    GPIO.output(config.MOSFET_GPIO, GPIO.LOW)

def cleanup():
    GPIO.output(config.MOSFET_GPIO, GPIO.LOW)
    GPIO.cleanup() # Got this from the test script, found it useful for debugging

