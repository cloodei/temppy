import paho.mqtt.client as paho
import temp
from dotenv import load_dotenv
from os import getenv
from paho import mqtt

load_dotenv()
username = getenv("MQTT_USERNAME")
password = getenv("MQTT_PASSWORD")
cluster_url = getenv("MQTT_CLUSTER_URL")

mqttClient = paho.Client(client_id="", protocol=paho.MQTTv5)
mqttClient.on_connect = lambda client, userdata, flags, rc: print(f"Connected with result code {rc}")

mqttClient.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
mqttClient.username_pw_set(username, password)
mqttClient.connect(cluster_url, 8883)

mqttClient.loop_start()
while True:
    input("Press Enter to read sensor data...")
    try:
        temperature, humidity = temp.read_sensor()
        mqttClient.publish("pi/readings", f"{temperature} {humidity}%", qos=1)
    except Exception as e:
        print(f"Error reading pi data: {e}")
