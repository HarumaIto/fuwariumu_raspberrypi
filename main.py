import logging
import time
import threading
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

def wav_to_mp3(wav_path: str, mp3_path: str) -> bool:
    """WAVファイルをMP3形式に変換する"""
    logging.info(f"{wav_path} を {mp3_path} に変換します...")
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3")
        logging.info("変換が完了しました。")
        return True
    except FileNotFoundError:
        logging.error(f"WAVファイルが見つかりません: {wav_path}")
        return False
    except Exception as e:
        logging.error(f"MP3への変換中にエラーが発生しました: {e}")
        return False

def play_completed_task(led_strip, task_response: dict):
    """完了したタスクの音声とLEDパターンを再生する"""
    logging.info(f"タスク再生開始: {task_response.get('task_id')}")
    try:
        base64_audio_data = task_response.get('result')
        if not base64_audio_data:
            logging.error("タスクレスポンスに音声データが含まれていません。")
            return

        audio_data = get_audio_data(base64_audio_data)
        if not audio_data:
            logging.error("再生用の音声データを取得できませんでした。")
            return

        play_obj = play_audio(audio_data)
        if not play_obj:
            logging.error("音声再生を開始できませんでした。")
            return
        
        logging.info("音声とLEDパターンの再生を開始します。")
        led_blink_reflect_music(led_strip, audio_data, play_obj)
        logging.info("再生が完了しました。")
        
    except Exception as e:
        logging.error(f"音声・LEDの再生中にエラーが発生しました: {e}")

def find_available_task() -> dict | None:
    """再生可能な完了済みタスクを検索する"""
    if not task_ids:
        return None
    
    logging.info(f"{len(task_ids)}個のタスクから再生可能なものを探します。")
    for task_id in task_ids:
        task_info = get_task(task_id)
        if task_info and task_info.get("status") == "completed":
            logging.info(f"再生可能なタスクが見つかりました: {task_id}")
            return task_info
    logging.info("再生可能なタスクはありませんでした。")
    return None

def record_and_post_data():
    """録音、センサーデータ取得、APIへのデータ投稿を行う（中断可能）"""
    global stop_recording_event
    stop_recording_event.clear()
    
    logging.info("録音スレッドを開始します。")
    record_status = record_audio(RECORDING_SECONDS, WAVE_OUTPUT_FILENAME, stop_recording_event)

    if record_status == 'interrupted':
        logging.info("録音が中断されたため、後続処理をスキップします。")
        return
    if record_status == 'error':
        logging.error("録音に失敗しました。このサイクルをスキップします。")
        return

    if not wav_to_mp3(WAVE_OUTPUT_FILENAME, MP3_OUTPUT_FILENAME):
        logging.error("MP3への変換に失敗しました。このサイクルをスキップします。")
        return

    bme_data = bme280_sample.readData()
    tsl_data = tsl2572_sample.readData()

    response = post_data(MP3_OUTPUT_FILENAME, bme_data, tsl_data)
    if response and "task_id" in response:
        logging.info(f"データの投稿に成功しました。Task ID: {response['task_id']}")
        task_ids.append(response["task_id"])
    else:
        logging.error("データの投稿に失敗したか、レスポンスにtask_idが含まれていません。")
    logging.info("録音スレッドを終了します。")

def handle_switch_press():
    """
    スイッチが押された時に呼び出されるコールバック関数。
    完了済みのタスクを探し、あれば録音を中断して再生する。
    """
    global led_strip, recording_thread
    logging.info("スイッチが押されました。完了したタスクを確認します。")

    available_task = find_available_task()

    if available_task:
        logging.info(f"再生タスク {available_task['task_id']} のために、現在の処理を中断します。")
        
        if recording_thread and recording_thread.is_alive():
            logging.info("実行中の録音スレッドに停止信号を送ります。")
            stop_recording_event.set()
            # スレッドが終了し、オーディオデバイスが解放されるのを待つ
            recording_thread.join()
            logging.info("録音スレッドが停止しました。")
        
        play_completed_task(led_strip, available_task)
        # 再生済みのタスクをリストから削除
        if available_task['task_id'] in task_ids:
            task_ids.remove(available_task['task_id'])
    else:
        logging.info("再生できる完了済みタスクがありませんでした。")

def main():
    """アプリケーションのメイン関数"""
    global led_strip, recording_thread
    try:
        led_strip = init_led()
        bme280_sample.init()
        tsl2572_sample.init()
        setup_switch(handle_switch_press)

        logging.info("アプリケーションを開始します。")
        while True:
            if recording_thread is None or not recording_thread.is_alive():
                # 録音スレッドが実行中でなければ、新しいスレッドを開始
                recording_thread = threading.Thread(target=record_and_post_data)
                recording_thread.start()
            
            time.sleep(10) # メインループのポーリング間隔

    except KeyboardInterrupt:
        logging.info("シャットダウンシグナルを受信しました。")
    except Exception as e:
        logging.critical(f"メインループで予期せぬエラーが発生しました: {e}", exc_info=True)
    finally:
        if recording_thread and recording_thread.is_alive():
            logging.info("シャットダウン前に、実行中の録音スレッドに停止信号を送ります...")
            stop_recording_event.set()
            recording_thread.join() # スレッドが終了するのを待つ

        if led_strip:
            led_strip.off()
        logging.info("アプリケーションをシャットダウンしました。")

if __name__ == "__main__":
    main()