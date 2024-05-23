from flask import Flask, jsonify, render_template
import time
import board
import adafruit_dht
import spidev
from threading import Thread, Event, Lock

app = Flask(__name__)

# Variable zum Speichern der Sensorwerte
sensor_data = {
    "temperature_c": None,
    "temperature_f": None,
    "humidity": None,
    "soil_moisture": {
        "channel_0": None,
        "channel_1": None,
        "channel_2": None,
        "channel_3": None
    }
}

# Ereignis zum Beenden des Sensor-Threads
stop_event = Event()
lock = Lock()

# Initialisiere den DHT11-Sensor und den SPI-Bus nur einmal
dhtDevice = None
spi = None

def initialize_sensors():
    global dhtDevice, spi
    # Initialisiere den DHT11-Sensor und den SPI-Bus
    try:
        if dhtDevice is None:
            dhtDevice = adafruit_dht.DHT11(board.D4)
            print("DHT11 Sensor initialisiert.")
        if spi is None:
            spi = spidev.SpiDev()
            spi.open(0, 0)
            spi.max_speed_hz = 1350000
            print("SPI Bus initialisiert.")
    except Exception as e:
        print(f"Fehler beim Initialisieren der Sensoren: {e}")

def read_adc(channel):
    if channel < 0 or channel > 7:
        print(f"Ungültiger ADC-Kanal: {channel}")
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    print(f"ADC Channel {channel} gelesen: {data}")
    return data

def convert_to_percentage(value):
    # Konvertiere den ADC-Wert (0-1000) in eine Prozentzahl (100%-0%)
    percentage = max(0, min(100, (1000 - value) * 100 // 1000))
    print(f"ADC Wert {value} zu Prozent {percentage}% konvertiert.")
    return percentage

def create_ascii_bar(percentage):
    # Erzeuge einen Ladebalken in ASCII basierend auf dem Prozentsatz
    bar_length = 20
    filled_length = bar_length * percentage // 100
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f'[{bar}] {percentage}%'

def update_sensor_data():
    initialize_sensors()
    while not stop_event.is_set():
        try:
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity
            if temperature_c is not None and humidity is not None:
                temperature_f = temperature_c * (9 / 5) + 32
                with lock:
                    sensor_data["temperature_c"] = temperature_c
                    sensor_data["temperature_f"] = temperature_f
                    sensor_data["humidity"] = humidity
                print(f"Temperatur: {temperature_c:.1f} C, Luftfeuchtigkeit: {humidity}%")
            else:
                print("Fehler beim Auslesen der DHT11-Sensorwerte.")
        except RuntimeError as error:
            print(f"RuntimeError: {error.args[0]}")
        except Exception as error:
            print(f"Exception: {error}")
            dhtDevice.exit()
            raise error
        
        soil_data = {}
        for i in range(4):
            try:
                adc_value = read_adc(i)
                if adc_value >= 0:
                    percentage = convert_to_percentage(adc_value)
                    soil_data[f"channel_{i}"] = {
                        "value": adc_value,
                        "percentage": percentage,
                        "ascii_bar": create_ascii_bar(percentage)
                    }
                else:
                    print(f"Fehler beim Auslesen von ADC-Kanal {i}")
                    soil_data[f"channel_{i}"] = None
            except Exception as e:
                print(f"Fehler beim Auslesen des ADC-Kanals {i}: {e}")
                soil_data[f"channel_{i}"] = None

        with lock:
            sensor_data["soil_moisture"] = soil_data

        print(f"Sensor Daten aktualisiert: {sensor_data}")
        
        time.sleep(2.0)

@app.route('/data')
def get_sensor_data():
    with lock:
        data_copy = sensor_data.copy()  # Machen Sie eine Kopie der Daten, um das Lock freizugeben
    print(f"Senden der Daten: {data_copy}")  # Debug-Ausgabe
    return jsonify(data_copy)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    sensor_thread = Thread(target=update_sensor_data)
    sensor_thread.start()
    try:
        app.run(debug=False, host='0.0.0.0', port=6996)  # Debug-Modus deaktivieren
    finally:
        stop_event.set()
        sensor_thread.join()
        dhtDevice.exit()
