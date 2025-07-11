import adafruit_dht
import board
from time import sleep
from gpiozero import LED

dht = adafruit_dht.DHT11(board.D10)
led = LED(5)

def read_sensor():
    try:
        temp = dht.temperature
        hum = dht.humidity
        print(f"Temperature: {temp}°C, Humidity: {hum}%")
        
        if temp > 30:
            led.on()
            print("LED is ON")
        else:
            led.off()
            print("LED is OFF")
    except RuntimeError as e:
        print(f"RuntimeError: {e.args[0]}")
    except Exception as e:
        dht.exit()
        raise e
    finally:
        sleep(3)

while True:
    read_sensor()
