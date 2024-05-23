import time
import board
import adafruit_dht

# Initialisiere den DHT11-Sensor
dhtDevice = adafruit_dht.DHT11(board.D4)

while True:
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        if temperature_c is not None and humidity is not None:
            temperature_f = temperature_c * (9 / 5) + 32
            print(
                "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    temperature_f, temperature_c, humidity
                )
            )
        else:
            print("Fehler beim Auslesen der Sensorwerte.")

    except RuntimeError as error:
        print(f"RuntimeError: {error.args[0]}")
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)
