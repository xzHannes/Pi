import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

try:
    while True:
        for channel in [0, 1, 2]:  # Nur Channel 0, 1 und 2 auslesen
            value = read_adc(channel)
            print(f"Channel {channel}: {value}")
        time.sleep(1)
except KeyboardInterrupt:
    spi.close()