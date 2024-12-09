import network
import time
from machine import Pin, unique_id
import ubinascii
from umqtt.simple import MQTTClient

# Wi-Fi credentials
SSID = "SSID"
PASSWORD = "WIFI_PASS"

# MQTT Broker details
MQTT_BROKER = "BROKER"
MQTT_PORT = 1883
MQTT_TOPIC = "home/door_kitcab"
MQTT_CLIENT_ID = "esp32_kitcab"  # Fixed client ID for persistent sessions

# GPIO Pin for reed switch
REED_SWITCH_PIN = 5

# Initialize reed switch with internal pull-up resistor
reed_switch = Pin(REED_SWITCH_PIN, Pin.IN, Pin.PULL_UP)

# Connect to Wi-Fi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Already connected to Wi-Fi")
        return wlan

    print(f"Connecting to Wi-Fi: {SSID}...")
    wlan.connect(SSID, PASSWORD)

    # Wait for connection
    for _ in range(20):  # 20 seconds timeout
        if wlan.isconnected():
            print("Wi-Fi connected")
            print("Network config:", wlan.ifconfig())
            return wlan
        time.sleep(1)

    # Fail if unable to connect
    raise RuntimeError("Failed to connect to Wi-Fi")

# Check MQTT connection status
def is_connected(client):
    try:
        client.ping()  # Send a ping to check connection
        return True
    except OSError:
        return False

# Publish MQTT message
def send_mqtt_message(client, message):
    try:
        # Ensure message is UTF-8 encoded
        client.publish(MQTT_TOPIC, message.encode('utf-8'))
        print(f"MQTT message sent: {message}")
    except OSError as e:
        print(f"Failed to send MQTT message: {e}")
        try:
            print("Attempting to reconnect to MQTT broker with delay...")
            time.sleep(5)  # Add a 5-second backoff before reconnecting
            client.connect()  # Reconnect to the broker
            client.publish(MQTT_TOPIC, message.encode('utf-8'))  # Retry sending the message
            print(f"MQTT message sent after reconnect: {message}")
        except Exception as reconnection_error:
            print(f"Reconnection failed: {reconnection_error}")

# Monitor door and send status
def monitor_door(client):
    prev_status = None
    last_change = 0
    debounce_delay = 200  # 200ms debounce delay

    while True:
        # Check reed switch state
        current_time = time.ticks_ms()
        status = reed_switch.value() == 1  # 1 = Open, 0 = Closed

        if status != prev_status and time.ticks_diff(current_time, last_change) > debounce_delay:
            prev_status = status
            last_change = current_time
            door_kitcab = "ανοιχτό" if status else "κλειστό"
            print(f"Το ντουλάπι είναι {door_kitcab}")
            send_mqtt_message(client, door_kitcab)

        time.sleep(0.1)

# Main execution
try:
    # Connect to Wi-Fi
    wlan = connect_to_wifi()

    # Connect to MQTT broker
    mqtt_client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=300)  # Keepalive set to 300 seconds
    mqtt_client.connect()
    print(f"Connected to MQTT broker at {MQTT_BROKER}")

    # Monitor door and send status
    monitor_door(mqtt_client)
except Exception as e:
    print(f"Error: {e}")
