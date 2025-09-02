import requests
import base64
import json
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_PATH = "http://192.168.111.236:8000"

def post_data(mp3_path, bme280_data, tsl2572_data) -> dict[str, str] | None:
    print("* posting data...")
    url = f"{BASE_PATH}/api/v1/data"

    try:
        with open(mp3_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        logging.error(f"音声ファイルが見つかりません: {mp3_path}")
        return None

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

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # ステータスコードが200番台でない場合に例外を発生させる

        print("POST status:", response.status_code)
        print("bme280:", bme280_data)
        print("tsl2572:", tsl2572_data)
        print("* post done")

        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"APIへのデータ送信に失敗しました: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"レスポンスJSONのデコードに失敗しました: {e}")
        return None


def get_task(task_id: str) -> dict[str, any] | None:
    url = f"{BASE_PATH}/api/v1/status/{task_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"タスクステータスの取得に失敗しました: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"レスポンスJSONのデコードに失敗しました: {e}")
        return None

def get_mock_task() -> dict[str, any] | None:
    url = f"{BASE_PATH}/api/v1/get_mock_data"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"モックの取得に失敗しました: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"レスポンスのでコードに失敗しました: {e}")
        return None

def get_status(task_ids: list[str]) -> bool | None:
    url = f"{BASE_PATH}/api/v1/task_list"
    try:
        payload = {"task_ids": task_ids}
        response = requests.get(url, params=payload, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"ステータスの取得に失敗しました: {e}")
        return None

