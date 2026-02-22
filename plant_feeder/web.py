from flask import Flask, render_template, request
import controller
import config
import threading
import main

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    force_water = False
    
    if request.method == 'POST':
        if 'force_water' in request.form:
            force_water = True
            print("WEB: Manual watering command received.")
        elif 'toggle_lights' in request.form:
            controller.toggle_lights()
            print("WEB: Light toggle command received.")
        elif 'toggle_auto' in request.form:
            if controller.auto_watering_enabled:
                controller.auto_watering_enabled = False
            else:
                controller.auto_watering_enabled = True
                threading.Thread(target=main.start_auto_loop, daemon=True).start()

    moisture, raw_moisture, status = controller.check_plant(force_water_command=force_water, auto_water=False)

    return render_template('index.html',
                           moisture=moisture,
                           raw_moisture=raw_moisture,
                           status=status,
                           last_checked=controller.last_checked,
                           last_watered=controller.last_watered,
                           light_status=controller.light_status,
                           auto_enabled=controller.auto_watering_enabled)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
