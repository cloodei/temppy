"""
Đọc dữ liệu từ cảm biến DHT11
"""

import board
import gpiozero
import adafruit_dht
from gpiozero import LED

class MyRelay(gpiozero.OutputDevice):
    name: str
    def __init__(self, pin, name="Light"):
        self.name = name
        super().__init__(pin, active_high=True, initial_value=False)
        self.off()

class MyLED(pin=LED):
    color: str
    def __init__(self, pin, color="Red"):
        self.color = color
        super().__init__(pin)
        self.off()

readsend = False

dht = adafruit_dht.DHT11(pin=board.D10)
leds: list[MyLED] = [MyLED(pin=5, color="Yellow"), MyLED(pin=6, color="Red"), MyLED(pin=13, color="Yellow"), MyLED(pin=19, color="Green")]
relays: list[MyRelay] = [MyRelay(pin=21, name="Đèn LED Xanh")]

def read_sensor():
    global dht
    try:
        dht.measure()
        return dht._temperature, dht._humidity
    except RuntimeError as e:
        print(f"RuntimeError: {e.args[0]}")
        return None, None
    except Exception as e:
        dht.exit()
        raise e


def ledPayload():
    return "|".join([(led.color + ("1" if led.is_active else "0")) for led in leds]) if len(leds) > 0 else None

def relayPayload(room: str):
    return "|".join([f"{relay.name}-{room}-{('1' if relay.is_active else '0')}" for relay in relays]) if len(relays) > 0 else None
    
def dhtPayload(room: str):
    try:
        dht.measure()
        global readsend
        return f"{room}{'1' if readsend else '0'}"
    except RuntimeError as e:
        print(f"RuntimeError: {e.args[0]}")
        return None
    except Exception as e:
        dht.exit()
        return None
