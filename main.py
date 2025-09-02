import logging
import time
import threading
import queue
from pydub import AudioSegment

# プロジェクト内のモジュール
import bme280_sample
import tsl2572_sample
from record_sample import record_audio
from api import post_data, get_task
from led import init_led
from play_audio import get_audio_data, play_audio
from jellyfish import led_blink_reflect_music
from switch import setup_switch

# --- 設定項目 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
WAVE_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"
RECORDING_SECONDS = 180

# --- グローバル変数 ---
led_strip = None
task_ids = []
recording_thread = None
stop_recording_event = threading.Event()
event_queue = queue.Queue()

def wav_to_mp3(wav_path: str, mp3_path: str) -> bool:
    logging.info(f"{wav_path} を {mp3_path} に変換します...")
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3")
        logging.info("変換が完了しました。")
        return True
    except Exception as e:
        logging.error(f"MP3への変換中にエラーが発生しました: {e}")
        return False

def play_completed_task(led_strip, task_response: dict):
    logging.info(f"タスク再生開始: {task_response.get('task_id')}")
    try:
        base64_audio_data = task_response.get('result')
        if not base64_audio_data: return
        audio_data = get_audio_data(base64_audio_data)
        if not audio_data: return
        play_obj = play_audio(audio_data)
        if not play_obj: return
        led_blink_reflect_music(led_strip, audio_data, play_obj)
        logging.info("再生が完了しました。")
    except Exception as e:
        logging.error(f"音声・LEDの再生中にエラーが発生しました: {e}")

def record_and_post_data():
    """【別スレッドで実行】録音、センサーデータ取得、API投稿を行う"""
    stop_recording_event.clear()

    logging.info("録音スレッド: 処理を開始します。")
    record_status = record_audio(RECORDING_SECONDS, WAVE_OUTPUT_FILENAME, stop_recording_event)

    if record_status == 'interrupted':
        logging.info("録音スレッド: 録音が中断されたため終了します。")
        return
    if record_status == 'error':
        logging.error("録音スレッド: 録音に失敗しました。")
        return

    if not wav_to_mp3(WAVE_OUTPUT_FILENAME, MP3_OUTPUT_FILENAME):
        logging.error("録音スレッド: MP3への変換に失敗しました。")
        return

    bme_data = bme280_sample.readData()
    tsl_data = tsl2572_sample.readData()

    response = post_data(MP3_OUTPUT_FILENAME, bme_data, tsl_data)
    if response and "task_id" in response:
        new_task_id = response["task_id"]
        logging.info(f"録音スレッド: データの投稿に成功。Task ID: {new_task_id}")
        task_ids.append(new_task_id)
    else:
        logging.error("録音スレッド: データの投稿に失敗。")
    logging.info("録音スレッド: 正常に終了します。")

def handle_switch_press():
    """【軽量な割り込みハンドラ】キューにイベントを追加するだけ"""
    event_queue.put('SWITCH_PRESSED')

def process_switch_event():
    """スイッチイベントを処理する"""
    global led_strip, recording_thread
    logging.info("スイッチ・イベントを処理します。")

    # 再生可能なタスクを検索
    available_task = None
    for task_id in task_ids:
        task_info = get_task(task_id)
        if task_info and task_info.get("status") == "completed":
            available_task = task_info
            break

    if available_task:
        logging.info(f"再生タスク {available_task['task_id']} が見つかりました。")
        if recording_thread and recording_thread.is_alive():
            logging.info("実行中の録音スreadに停止信号を送信します。")
            stop_recording_event.set()
            recording_thread.join() # スレッドが終了するのを待つ
            logging.info("録音スレッドが停止しました。")
        
        play_completed_task(led_strip, available_task)
        if available_task['task_id'] in task_ids:
            task_ids.remove(available_task['task_id'])
    else:
        logging.info("再生できる完了済みタスクがありませんでした。")

def main():
    global led_strip, recording_thread
    try:
        # 初期化処理
        led_strip = init_led()
        bme280_sample.init()
        tsl2572_sample.init()
        setup_switch(handle_switch_press)
        logging.info("アプリケーションを開始します。")

        while True:
            # --- スイッチイベントの処理 ---
            try:
                event = event_queue.get_nowait()
                if event == 'SWITCH_PRESSED':
                    process_switch_event()
            except queue.Empty:
                pass

            # --- 録音スレッドの管理 ---
            if recording_thread is None or not recording_thread.is_alive():
                logging.info("メインループ: 新しい録音スレッドを開始します。")
                recording_thread = threading.Thread(target=record_and_post_data)
                recording_thread.start()
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        logging.info("シャットダウンシグナルを受信しました。")
    except Exception as e:
        logging.critical(f"メインループで予期せぬエラー: {e}", exc_info=True)
    finally:
        if recording_thread and recording_thread.is_alive():
            logging.info("シャットダウン前に録音スレッドを停止します...")
            stop_recording_event.set()
            recording_thread.join()
        if led_strip:
            led_strip.off()
        logging.info("アプリケーションをシャットダウンしました。")

if __name__ == "__main__":
    main()
