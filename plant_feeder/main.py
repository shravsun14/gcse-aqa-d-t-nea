import time
import config
import controller
import hardware

def start_auto_loop():
    print("Main: Auto-watering loop started!")
    while controller.auto_watering_enabled:
        moisture, raw_moisture, status = controller.check_plant(force_water_command=False, auto_water=True)
        for _ in range(config.CHECK_INTERVAL):
            if not controller.auto_watering_enabled:
                print("Main: Auto-watering loop stopped!")
                return
            time.sleep(1)

if __name__ == '__main__':
    controller.auto_watering_enabled = True
    try:
        start_auto_loop()
    except KeyboardInterrupt:
        print("Stopping...")
        hardware.cleanup()