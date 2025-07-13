"""
Đọc dữ liệu từ cảm biến DHT11
"""

import time
import adafruit_dht
import board
from gpiozero import LED

dht = adafruit_dht.DHT11(board.D10)
led = LED(5)

def read_sensor():
    try:
        dht.measure()
        return dht._temperature, dht._humidity
    except RuntimeError as e:
        print(f"RuntimeError: {e.args[0]}")
        return None, None
    except Exception as e:
        dht.exit()
        raise e

if __name__ == "__main__":
    while True:
        try:
            temperature, humidity = read_sensor()
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
        except Exception as e:
            print(f"Error reading sensor data: {e}")
        time.sleep(0.25)
        led.on()
        time.sleep(2.75)
        led.off()
