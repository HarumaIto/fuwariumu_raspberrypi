import wave
import pyaudio
import logging
import threading

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def record_audio(seconds: int, filename: str, stop_event: threading.Event) -> str:
    """
    指定秒数録音し、WAVファイルとして保存する。
    stop_eventがセットされたら録音を中断する。

    :param seconds: 録音秒数
    :param filename: 保存ファイル名
    :param stop_event: 録音を中断するためのthreading.Eventオブジェクト
    :return: 録音の状態 ('completed', 'interrupted', 'error')
    """
    p = None
    stream = None
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        logging.info(f"* recording {seconds} sec...")
        frames = []
        for _ in range(0, int(RATE / CHUNK * seconds)):
            if stop_event.is_set():
                logging.info("録音が中断されました。")
                return 'interrupted'
            data = stream.read(CHUNK)
            frames.append(data)
        
        logging.info("* done recording")

        # ファイルに書き込む
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        sample_width = pyaudio.get_sample_size(FORMAT)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return 'completed'

    except IOError as e:
        logging.error(f"録音デバイスのエラー: {e}。マイクが接続されているか確認してください。")
        return 'error'
    except Exception as e:
        logging.error(f"録音中に予期せぬエラーが発生しました: {e}")
        return 'error'
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if p:
            p.terminate()

def main():
    """サンプル実行: 10秒録音し、5秒で中断させるテスト"""
    import time
    stop_event = threading.Event()

    # 5秒後にstop_eventをセットするスレッド
    def interrupt_after_5s():
        time.sleep(5)
        print("\n5秒経過、録音を中断します。")
        stop_event.set()

    print("10秒間の録音を開始します。5秒後に中断されます。")
    threading.Thread(target=interrupt_after_5s).start()
    
    status = record_audio(10, "output_interrupted.wav", stop_event)
    print(f"最終的な録音ステータス: {status}")
    # statusがinterruptedの場合、ファイルは作成されない（または不完全）

if __name__ == "__main__":
    main()
