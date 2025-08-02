import rpi
import time
import signal
import requests
import paho.mqtt.client as paho
from paho import mqtt
from os import getenv
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, filepath: str, callback):
        self.filepath = filepath
        self.callback = callback
    
    def on_modified(self, event):
        if (not event.is_directory) and (event.src_path == self.filepath):
            self.callback()

def read_file_content():
    global room
    with open("room/room.txt", "r") as f:
        read = f.read().strip()
        if read != room:
            room = read
            pubDHT()
            pubRelay()

load_dotenv()
api_url = getenv("API_ENDPOINT")
username = getenv("MQTT_USERNAME")
password = getenv("MQTT_PASSWORD")
cluster_url = getenv("MQTT_CLUSTER_URL")

observer = Observer()
handler = FileChangeHandler("./room/room.txt", read_file_content)
observer.schedule(handler, path="./room", recursive=False)
observer.start()

def pubLED():
    ledpayload = rpi.ledPayload()
    if ledpayload:
        mqttClient.publish(topic="pi/led", payload=ledpayload, qos=1, retain=True)

def pubRelay():
    global room
    relaypayload = rpi.relayPayload(room)
    if relaypayload:
        mqttClient.publish(topic="pi/relay", payload=relaypayload, qos=1, retain=True)

def pubDHT():
    global room
    dhtpayload = rpi.dhtPayload(room)
    if dhtpayload:
        mqttClient.publish(topic="pi/dht", payload=dhtpayload, qos=1, retain=True)

def pub(client: paho.Client):
    global room
    client.publish(topic="pi/online", payload="1", qos=1, retain=True)
    pubLED()
    pubDHT()
    pubRelay()

def on_connect(client, userdata, flags, rc, properties=None):
    global room
    with open("room/room.txt", "r") as file:
        room = file.read().strip()
    pub(client)
    client.subscribe("client/led", qos=1)
    client.subscribe("client/dht", qos=1)
    client.subscribe("client/relay", qos=1)
    print("Đã kết nối tới MQTT broker.")

def on_message(client, _, message):
    payload = message.payload.decode().strip()
    if message.topic == "client/led":
        led_idx = int(payload.split("|")[0])
        if 0 <= led_idx < len(rpi.leds):
            led = rpi.leds[led_idx]
            if payload.endswith("1"):
                led.on()
            else:
                led.off()

    elif message.topic == "client/relay":
        relay_idx = int(payload.split("|")[0])
        if 0 <= relay_idx < len(rpi.relays):
            relay = rpi.relays[relay_idx]
            if payload.endswith("1"):
                relay.on()
            else:
                relay.off()

    elif message.topic == "client/dht":
        rpi.readsend = payload == "1"
    # print(f"Đã nhận tin nhắn từ {message.topic}: {payload}")


mqttClient = paho.Client(client_id="", protocol=paho.MQTTv5)

def kill():
    global mqttClient

    mqttClient.publish(topic="pi/online", payload="0", qos=1, retain=True)
    mqttClient.loop_stop()
    mqttClient.disconnect()

    observer.stop()
    observer.join()
    exit(0)

signal.signal(signalnum=signal.SIGINT, handler=lambda signum, frame: kill())
signal.signal(signalnum=signal.SIGTERM, handler=lambda signum, frame: kill())

mqttClient.will_set(topic="pi/online", payload="0", qos=1, retain=True)

mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
mqttClient.username_pw_set(username, password)
mqttClient.connect(cluster_url, 8883)
mqttClient.loop_start()

user_id = int(getenv("USER_ID")) if getenv("USER_ID") else 0

time.sleep(0.75)
while user_id <= 0:
    try:
        username = input("Tên đăng nhập: ").strip()
        password = input("Mật khẩu: ").strip()

        response = requests.post(f"{api_url}/pi/login", json={"username": username, "password": password})
        response.raise_for_status()
        res = response.json()

        if res == True:
            print("Mật khẩu không đúng. Vui lòng thử lại.")
            continue
        elif res == False:
            print("Tên đăng nhập không đúng. Vui lòng thử lại.")
            continue

        user_id: int = res.get("id", 0)
        if user_id <= 0:
            print("Không tìm thấy người dùng. Vui lòng kiểm tra lại thông tin đăng nhập.")
            continue

        if user_id is not None:
            print(f"Đăng nhập thành công với ID người dùng: {user_id}")
            with open(".env", "a") as env_file:
                env_file.write(f"\nUSER_ID={user_id}\n")

            break
        else:
            print("Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin đăng nhập.")
    except Exception as e:
        print(f"Error during login: {e}. Please check your network connection or API endpoint.")
        raise e

while True:
    if not rpi.readsend:
        time.sleep(0.75)
        if not rpi.readsend:
            time.sleep(0.75)
            continue

    try:
        temperature, humidity = rpi.read_sensor()
        if temperature is None or humidity is None:
            print("Không đọc được dữ liệu từ cảm biến. Vui lòng kiểm tra kết nối.")
            continue

        print(f"{temperature}  {humidity}")
        mqttClient.publish(topic="pi/readings", payload=f"{user_id}|{temperature}|{humidity}|{room}", qos=1)
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu từ cảm biến: {e}. Vui lòng kiểm tra kết nối cảm biến.")
    finally:
        time.sleep(8)
