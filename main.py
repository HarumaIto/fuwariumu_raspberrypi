import logging
import time
import multiprocessing
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

# --- グローバル変数 (メインプロセスのみ) ---
led_strip = None
task_ids = []

# --- プロセス間通信用のオブジェクト ---
# 注意: これらのオブジェクトはfork前に一度だけ生成される
stop_recording_event = multiprocessing.Event()
switch_event_queue = multiprocessing.Queue()
task_id_queue = multiprocessing.Queue()

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

# ===================================================================
# === 録音プロセスで実行される関数群 (ここから) ===
# ===================================================================

def record_and_post_data_process(stop_event, task_queue):
    """【別プロセスで実行】録音、センサーデータ取得、API投稿を行う"""
    # このプロセス内で必要な初期化を行う
    bme280_sample.init()
    tsl2572_sample.init()
    stop_event.clear()

    logging.info("録音プロセス: 処理を開始します。")
    record_status = record_audio(RECORDING_SECONDS, WAVE_OUTPUT_FILENAME, stop_event)

    if record_status == 'interrupted':
        logging.info("録音プロセス: 録音が中断されたため終了します。")
        return
    if record_status == 'error':
        logging.error("録音プロセス: 録音に失敗しました。")
        return

    if not wav_to_mp3(WAVE_OUTPUT_FILENAME, MP3_OUTPUT_FILENAME):
        logging.error("録音プロセス: MP3への変換に失敗しました。")
        return

    bme_data = bme280_sample.readData()
    tsl_data = tsl2572_sample.readData()

    response = post_data(MP3_OUTPUT_FILENAME, bme_data, tsl_data)
    if response and "task_id" in response:
        new_task_id = response["task_id"]
        logging.info(f"録音プロセス: データの投稿に成功。Task ID: {new_task_id}")
        task_queue.put(new_task_id) # キュー経由でメインプロセスに通知
    else:
        logging.error("録音プロセス: データの投稿に失敗。")
    logging.info("録音プロセス: 正常に終了します。")

# ===================================================================
# === メインプロセスで実行される関数群 (ここから) ===
# ===================================================================

def handle_switch_press():
    """【軽量な割り込みハンドラ】キューにイベントを追加するだけ"""
    # 割り込みハンドラ内でのloggingは競合の可能性があるためコメントアウト推奨
    # logging.info("スイッチ・イベントをキューに追加しました。")
    switch_event_queue.put('SWITCH_PRESSED')

def process_switch_event(current_process):
    """スイッチイベントを処理する（メインプロセスで実行）"""
    global led_strip
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
        if current_process and current_process.is_alive():
            logging.info("実行中の録音プロセスに停止信号を送信します。")
            stop_recording_event.set()
            current_process.join(timeout=5) # タイムアウト付きで待つ
            if current_process.is_alive():
                logging.warning("録音プロセスが時間内に終了しませんでした。強制終了します。")
                current_process.terminate()
            logging.info("録音プロセスが停止しました。")
        
        play_completed_task(led_strip, available_task)
        if available_task['task_id'] in task_ids:
            task_ids.remove(available_task['task_id'])
    else:
        logging.info("再生できる完了済みタスクがありませんでした。")
    return None # 新しいプロセスを返さない

def main():
    global led_strip
    recording_process = None
    try:
        led_strip = init_led()
        setup_switch(handle_switch_press)
        logging.info("メインプロセス: アプリケーションを開始します。")

        while True:
            # --- 完了したタスクIDを録音プロセスから受信 ---
            try:
                new_task_id = task_id_queue.get_nowait()
                task_ids.append(new_task_id)
                logging.info(f"メインプロセス: 新しいタスクID {new_task_id} を受信しました。")
            except multiprocessing.queues.Empty:
                pass

            # --- スイッチイベントの処理 ---
            try:
                event = switch_event_queue.get_nowait()
                if event == 'SWITCH_PRESSED':
                    recording_process = process_switch_event(recording_process)
            except multiprocessing.queues.Empty:
                pass

            # --- 録音プロセスの管理 ---
            if recording_process is None or not recording_process.is_alive():
                logging.info("メインプロセス: 新しい録音プロセスを開始します。")
                recording_process = multiprocessing.Process(
                    target=record_and_post_data_process, 
                    args=(stop_recording_event, task_id_queue)
                )
                recording_process.start()
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        logging.info("シャットダウンシグナルを受信しました。")
    except Exception as e:
        logging.critical(f"メインループで予期せぬエラー: {e}", exc_info=True)
    finally:
        if recording_process and recording_process.is_alive():
            logging.info("シャットダウン前に録音プロセスを停止します...")
            stop_recording_event.set()
            recording_process.join(timeout=5)
            if recording_process.is_alive():
                recording_process.terminate()
        if led_strip:
            led_strip.off()
        logging.info("アプリケーションをシャットダウンしました。")

if __name__ == "__main__":
    # マルチプロセス利用時は、エントリーポイントを保護することが必須
    main()