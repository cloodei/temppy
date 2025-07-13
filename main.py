import paho.mqtt.client as paho
import rpi
import requests
from dotenv import load_dotenv
from os import getenv
from paho import mqtt

load_dotenv()
api_url = getenv("API_ENDPOINT")
username = getenv("MQTT_USERNAME")
password = getenv("MQTT_PASSWORD")
cluster_url = getenv("MQTT_CLUSTER_URL")

mqttClient = paho.Client(client_id="", protocol=paho.MQTTv5)
mqttClient.on_connect = lambda client, userdata, flags, rc: print(f"Connected with result code {rc}")

mqttClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
mqttClient.username_pw_set(username, password)
mqttClient.connect(cluster_url, 8883)
mqttClient.loop_start()

user_id: int
while True:
    try:
        username = input("Tên đăng nhập: ").strip()
        password = input("Mật khẩu: ").strip()
        response = requests.post(f"{api_url}/pi/login", json={"username": username, "password": password})
        response.raise_for_status()
        user_id = response.json().get("id")
        if user_id is not None:
            print(f"Đăng nhập thành công với ID người dùng: {user_id}")
            break
        else:
            print("Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin đăng nhập.")
    except Exception as e:
        print(f"Error during login: {e}. Please check your network connection or API endpoint.")
        raise e

while True:
    room = input("Nhập tên phòng ('q' để thoát): ").strip().lower()
    match room:
        case "exit" | "stop" | "quit" | "close" | "esc" | "q" | "x" | "0":
            mqttClient.loop_stop()
            mqttClient.disconnect()
            break
        case _:
            print("Đọc dữ liệu từ cảm biến...")
            break

    try:
        temperature, humidity = rpi.read_sensor()
        if temperature is None or humidity is None:
            print("Không đọc được dữ liệu từ cảm biến. Vui lòng kiểm tra kết nối.")
            continue
        
        mqttClient.publish(topic="pi/readings", payload=f"{temperature}|{humidity}|{room}", qos=1)
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu từ cảm biến: {e}. Vui lòng kiểm tra kết nối cảm biến.")
