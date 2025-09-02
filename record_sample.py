import pyaudio
import wave
import logging
import time
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def record_audio(seconds: int, filename: str, stop_event: threading.Event) -> str:
    """
    ノンブロッキング（コールバック）方式で指定秒数録音し、WAVファイルとして保存する。
    stop_eventがセットされたら録音を中断する。

    :param seconds: 録音秒数
    :param filename: 保存ファイル名
    :param stop_event: 録音を中断するためのthreading.Eventオブジェクト
    :return: 録音の状態 ('completed', 'interrupted', 'error')
    """
    try:
        p = pyaudio.PyAudio()
        frames = []

        # コールバック関数: PyAudioが別スレッドで呼び出す
        def callback(in_data, frame_count, time_info, status):
            frames.append(in_data)
            return (None, pyaudio.paContinue) # 録音のみなのでout_dataはNone

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=callback)

        logging.info(f"ノンブロッキング録音を開始します... (最長{seconds}秒)")
        stream.start_stream()

        start_time = time.time()
        interrupted = False

        # 録音がアクティブな間、待機する
        # 待機中に stop_event またはタイムアウトをチェック
        while stream.is_active():
            if stop_event.is_set():
                logging.info("外部からの停止信号により録音を中断します。")
                interrupted = True
                break
            if time.time() - start_time > seconds:
                logging.info("指定時間が経過したため録音を終了します。")
                break
            time.sleep(0.1)

        logging.info("録音ストリームを停止します。")
        stream.stop_stream()
        stream.close()
        p.terminate()

        logging.info("WAVファイルに保存中...")
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        logging.info(f"{filename} への保存が完了しました。")

        return 'interrupted' if interrupted else 'completed'

    except Exception as e:
        logging.error(f"録音中に予期せぬエラーが発生しました: {e}", exc_info=True)
        return 'error'

if __name__ == '__main__':
    # --- テストコード ---
    print("ノンブロッキング録音のテストを開始します。")
    
    # 1. 10秒間録音し、5秒で中断させるテスト
    stop_event_test = threading.Event()
    def interrupt_after_5s():
        time.sleep(5)
        print("\n[テスト1] 5秒経過、録音を中断します。")
        stop_event_test.set()

    print("\n--- テスト1: 10秒間の録音を5秒で中断 --- ")
    threading.Thread(target=interrupt_after_5s).start()
    status = record_audio(10, "output_interrupted.wav", stop_event_test)
    print(f"[テスト1] 最終的な録音ステータス: {status}")

    print("\n----------------------------------------")

    # 2. 3秒間、最後まで正常に録音するテスト
    stop_event_test_2 = threading.Event()
    print("\n--- テスト2: 3秒間の録音を正常に完了 --- ")
    status_2 = record_audio(3, "output_completed.wav", stop_event_test_2)
    print(f"[テスト2] 最終的な録音ステータス: {status_2}")

    print("\nテストが完了しました。")
