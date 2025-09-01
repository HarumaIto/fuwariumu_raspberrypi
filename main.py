import logging
import time
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
RECORDING_SECONDS = 5
LOOP_SLEEP_SECONDS = 10

# --- グローバル変数 ---
led_strip = None
task_ids = []

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
    logging.info(f"タスク完了。結果: {task_response.get('result')}")
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

def check_and_execute_tasks(led_strip):
    """APIでタスクの状態を確認し、完了していれば再生処理を実行する"""
    if not task_ids:
        logging.info("チェック対象のタスクがありません。")
        return
        
    logging.info(f"{len(task_ids)}個のタスクの状態を確認します。")
    # リストのコピーに対してループを回し、安全な要素の削除を可能にする
    for task_id in task_ids[:]:
        task_info = get_task(task_id)
        if not task_info:
            logging.error(f"タスク {task_id} の状態取得に失敗しました。")
            continue

        if task_info.get("status") == "completed":
            play_completed_task(led_strip, task_info)
            task_ids.remove(task_id)
            # 完了したタスクが見つかったら再生して終了
            break
        elif task_info.get("status") == "failed":
            logging.error(f"タスク {task_id} は失敗しました。理由: {task_info.get('result')}")
            task_ids.remove(task_id)

def record_and_post_data():
    """録音、センサーデータ取得、APIへのデータ投稿を行う"""
    if not record_audio(RECORDING_SECONDS, WAVE_OUTPUT_FILENAME):
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

def handle_switch_press():
    """
    スイッチが押された時に呼び出されるコールバック関数。
    完了済みのタスクを確認して再生する。
    """
    global led_strip
    logging.info("スイッチが押されました。完了したタスクを確認します。")
    check_and_execute_tasks(led_strip)

def main():
    """アプリケーションのメイン関数"""
    global led_strip
    try:
        led_strip = init_led()
        bme280_sample.init()
        tsl2572_sample.init()
        setup_switch(handle_switch_press)

        logging.info("アプリケーションを開始します。")
        while True:
            record_and_post_data()
            logging.info(f"録音サイクル完了。{LOOP_SLEEP_SECONDS}秒待機します。")
            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        logging.info("シャットダウンシグナルを受信しました。")
    except Exception as e:
        logging.critical(f"メインループで予期せぬエラーが発生しました: {e}", exc_info=True)
    finally:
        if led_strip:
            led_strip.off()
        logging.info("アプリケーションをシャットダウンしました。")

if __name__ == "__main__":
    main()
