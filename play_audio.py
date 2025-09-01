from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import simpleaudio as sa
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AUDIO_FILE = "/home/intern/Music/school_hallway_sound.mp3"

def get_audio_data():
    try:
        audio = AudioSegment.from_mp3(AUDIO_FILE)
        mono_audio = audio.set_channels(1)
        return mono_audio
    except FileNotFoundError:
        logging.error(f"音声ファイルが見つかりません: {AUDIO_FILE}")
        return None
    except CouldntDecodeError as e:
        logging.error(f"音声ファイルのデコードに失敗しました: {e}")
        return None
    except Exception as e:
        logging.error(f"音声データの取得中に予期せぬエラーが発生しました: {e}")
        return None


def play_audio(mono_audio):
    if mono_audio is None:
        logging.error("音声データがNoneのため、再生できません。")
        return None
    try:
        playback_data = mono_audio.raw_data
        play_obj = sa.play_buffer(playback_data, 1, 2, mono_audio.frame_rate)
        return play_obj
    except Exception as e:
        logging.error(f"音声の再生準備中にエラーが発生しました: {e}")
        return None