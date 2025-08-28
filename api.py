import requests
import base64
import json

BASE_PATH = "http://192.168.111.254:8000"

def post_data(mp3_path, bme280_data, tsl2572_data):
    print("* posting data...")
    url = f"{BASE_PATH}/api/v1/data"

    with open(mp3_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    environmental_data = {
        "temperature": bme280_data["temperature"],
        "pressure": bme280_data["pressure"],
        "humidity": bme280_data["humidity"],
        "lux": tsl2572_data["lux"]
    }

    payload = {
        "audio_data": audio_data,
        "environmental_data": environmental_data
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    print("POST status:", response.status_code)
    print("bme280:", bme280_data)
    print("tsl2572:", tsl2572_data)
    print("* post done")
