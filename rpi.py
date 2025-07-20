"""
Đọc dữ liệu từ cảm biến DHT11
"""

import time
import adafruit_dht
import board
import gpiozero
from gpiozero import LED

class MyRelay(gpiozero.OutputDevice):
    name: str
    def __init__(self, pin, name="Light"):
        self.name = name
        super().__init__(pin, active_high=True, initial_value=False)
        self.off()

    def on(self):
        super().on()

    def off(self):
        super().off()

class MyLED(LED):
    color: str
    def __init__(self, pin, color="Red"):
        super().__init__(pin)
        self.color = color

    def on(self):
        super().on()

    def off(self):
        super().off()

dht = adafruit_dht.DHT11(board.D10)
leds: list[MyLED] = [MyLED(12), MyLED(23, "Yellow"), MyLED(24, "Yellow")]
relays: list[MyRelay] = [MyRelay(21)]

ledPayload = "|".join([led.color + "0" for led in leds]) if len(leds) > 0 else None
relayPayload = "|".join([relay.name + "0" for relay in relays]) if len(relays) > 0 else None

for led in leds:
    led.off()

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
        # try:
        #     temperature, humidity = read_sensor()
        #     print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
        # except Exception as e:
        #     print(f"Error reading sensor data: {e}")
        try:
            time.sleep(2)
            relays[0].on()
            time.sleep(2)
            relays[0].off()
            print("LED 0 turned ON for 2 seconds")
        except Exception as e:
            print(f"Error controlling LED: {e}")
