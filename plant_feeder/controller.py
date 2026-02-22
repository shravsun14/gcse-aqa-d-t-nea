import datetime
import hardware
import config

last_watered = 'Never'
last_checked = 'Never'
light_status = 'On'
auto_watering_enabled = False

def toggle_lights():
    global light_status
    
    if light_status == 'On':
        hardware.turn_lights_off()
        light_status = 'Off'
    elif light_status == 'Off':
        hardware.turn_lights_on()
        light_status = 'On'

def get_current_time():
    now = datetime.datetime.now()
    return now.strftime('%d-%m-%Y %H:%M')

def get_percentage(raw_value):
    percent = (config.FULL_DRY - raw_value) / (config.FULL_DRY - config.FULL_WET) * 100
    if percent < 0: percent = 0
    if percent > 100: percent = 100
    return int(percent)

def check_plant(force_water_command = False, auto_water = False):
    global last_checked, last_watered
    last_checked = get_current_time()
    raw_moisture = hardware.read_moisture()
    current_moisture = get_percentage(raw_moisture)

    if force_water_command == True:
        hardware.pump_on()
        last_watered = get_current_time()
        status_msg = 'Status: Manual Watering Complete'
    
    elif auto_water == True and raw_moisture > config.DRY_THRESHOLD:
        hardware.pump_on()
        last_watered = get_current_time()
        status_msg = 'Status: Dry - Watering Initiated'

    elif raw_moisture > config.DRY_THRESHOLD:
        status_msg = 'Status: Soil is Dry (Waiting for 6-hour cycle)'

    elif raw_moisture < config.WET_THRESHOLD:
        status_msg = 'Status: Soil is very wet'

    else:
        status_msg = 'Status: Moisture level is OK'
    
    return current_moisture, raw_moisture, status_msg
