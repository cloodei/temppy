import paho.mqtt.client as paho
import rpi
import requests
import time
import signal
from dotenv import load_dotenv
from os import getenv
from paho import mqtt

load_dotenv()
api_url = getenv("API_ENDPOINT")
username = getenv("MQTT_USERNAME")
password = getenv("MQTT_PASSWORD")
cluster_url = getenv("MQTT_CLUSTER_URL")

def pub_components(client: paho.Client):
    ledpayload = rpi.ledPayload()
    relaypayload = rpi.relayPayload()
    dhtpayload = rpi.dhtPayload()

    client.publish(topic="pi/online", payload="1", qos=1)
    if ledpayload:
        client.publish(topic="pi/led", payload=ledpayload, qos=1)

    if relaypayload:
        client.publish(topic="pi/relay", payload=relaypayload, qos=1)

    if dhtpayload:
        client.publish(topic="pi/dht", payload=dhtpayload, qos=1)

def on_connect(client, userdata, flags, rc, properties=None):
    pub_components(client)
    client.subscribe("client/led", qos=1)
    client.subscribe("client/dht", qos=1)
    client.subscribe("client/relay", qos=1)
    client.subscribe("client/online", qos=1)
    print("Đã kết nối tới MQTT broker.")

def on_message(client, _, message):
    payload = message.payload.decode().strip()
    if message.topic == "client/online":
        pub_components(client)

    elif message.topic == "client/dht":
        rpi.readsend = payload == "1"
        if rpi.readsend:
            print("Bắt đầu đọc dữ liệu")
        else:
            print("Dừng đọc dữ liệu")

    elif message.topic == "client/led":
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
            print(f"Rơ le {relay.name} {'bật' if relay.is_active else 'tắt'}")


mqttClient = paho.Client(client_id="", protocol=paho.MQTTv5)

def disconnect():
    global mqttClient
    mqttClient.publish(topic="pi/online", payload="0", qos=1)
    mqttClient.loop_stop()
    mqttClient.disconnect()
    print("Đã ngắt kết nối khỏi MQTT broker.")

def kill():
    disconnect()
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

time.sleep(1.5)
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

        user_id = res.get("user_id", 0)
        if user_id <= 0:
            print("Không tìm thấy người dùng. Vui lòng kiểm tra lại thông tin đăng nhập.")
            continue

        if user_id is not None:
            print(f"Đăng nhập thành công với ID người dùng: {user_id}")
            break
        else:
            print("Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin đăng nhập.")
    except Exception as e:
        print(f"Error during login: {e}. Please check your network connection or API endpoint.")
        raise e

room = None
with open("room.txt", "r") as file:
    room = file.read().strip()

while True:
    if not rpi.readsend:
        time.sleep(1.5)
        continue

    try:
        temperature, humidity = rpi.read_sensor()
        if temperature is None or humidity is None:
            print("Không đọc được dữ liệu từ cảm biến. Vui lòng kiểm tra kết nối.")
            continue

        print(f"Nhiệt độ: {temperature}°C  |  Độ ẩm: {humidity}%")
        mqttClient.publish(topic="pi/readings", payload=f"{user_id}|{temperature}|{humidity}|{room}", qos=1)
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu từ cảm biến: {e}. Vui lòng kiểm tra kết nối cảm biến.")
    finally:
        time.sleep(8)
