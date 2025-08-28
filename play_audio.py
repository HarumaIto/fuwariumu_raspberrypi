from pydub import AudioSegment
import simpleaudio as sa

AUDIO_FILE = "/home/intern/Music/school_hallway_sound.mp3"

def get_audio_data():
    audio = AudioSegment.from_mp3(AUDIO_FILE)
    mono_audio = audio.set_channels(1)
    return mono_audio

def play_audio(mono_audio):
    playback_data = mono_audio.raw_data
    play_obj = sa.play_buffer(playback_data, 1, 2, mono_audio.frame_rate)
    return play_obj
