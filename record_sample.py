import wave
import pyaudio
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def record_audio(seconds=5, filename="output.wav"):
    """
    指定秒数録音し、WAVファイルとして保存する。
    :param seconds: 録音秒数
    :param filename: 保存ファイル名
    :return: 成功した場合はTrue、失敗した場合はFalse
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
        
        print(f"* recording {seconds} sec...")
        frames = []
        for _ in range(0, int(RATE / CHUNK * seconds)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("* done recording")

        # ストリームを先に閉じる
        stream.stop_stream()
        stream.close()
        p.terminate()
        stream = None
        p = None

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        # PyAudioオブジェクトがterminateされているため、p.get_sample_sizeを直接使えない
        # FORMATからサンプルサイズを計算する
        sample_width = pyaudio.get_sample_size(FORMAT)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return True

    except IOError as e:
        logging.error(f"録音デバイスのエラー: {e}。マイクが接続されているか確認してください。")
        return False
    except Exception as e:
        logging.error(f"録音中に予期せぬエラーが発生しました: {e}")
        return False
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if p:
            p.terminate()

def main():
    """サンプル実行: 5秒録音"""
    if record_audio(5, "output.wav"):
        print("録音が完了し、output.wavとして保存されました。")
    else:
        print("録音に失敗しました。")

if __name__ == "__main__":
    main()