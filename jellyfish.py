from pydub import AudioSegment
import numpy as np
import simpleaudio as sa
import matplotlib.pyplot as plt
from gpiozero import RGBLED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep, perf_counter
from led import hsv_to_rgb

PIN_RED=5
PIN_GREEN=6
PIN_BLUE=13

AUDIO_FILE = "/home/intern/Music/school_hallway_sound.mp3"

GAIN = 5

def init_led():
    factory=PiGPIOFactory()
    led = RGBLED(PIN_RED, PIN_GREEN, PIN_BLUE, pin_factory=factory)
    return led

def get_audio_data():
    audio = AudioSegment.from_mp3(AUDIO_FILE)
    mono_audio = audio.set_channels(1)
    return mono_audio

def play_audio(mono_audio):
    playback_data = mono_audio.raw_data
    play_obj = sa.play_buffer(playback_data, 1, 2, mono_audio.frame_rate)
    return play_obj

def led_blink_reflect_music(led, mono_audio, play_obj):
    samples = np.array(mono_audio.get_array_of_samples())
    samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max

    actual_max_amplitude = np.max(np.abs(samples))

    sample_rate = mono_audio.frame_rate
    chunk_size = int(sample_rate * 0.01)

    current_time = 0

    while play_obj.is_playing():
        start_time = perf_counter()
        current_sample = int(current_time * sample_rate)

        chunk_start = current_sample
        chunk_end = min(current_sample + chunk_size, len(samples))
        if chunk_start >= chunk_end:
            break

        print(current_time)
        chunk = samples[chunk_start:chunk_end]

        amplitude = np.mean(np.abs(chunk))

        normalized_amplitude = amplitude / actual_max_amplitude
        normalized_amplitude = np.sqrt(normalized_amplitude)
        normalized_amplitude = max(0.0, min(1.0, normalized_amplitude))

        led.color = hsv_to_rgb(normalized_amplitude, normalized_amplitude, normalized_amplitude)

        end_time = perf_counter()
        elapsed_time = (end_time - start_time) / 60
        sleep_time = 0.005
        current_time = current_time + (sleep_time + elapsed_time)
        sleep(sleep_time)

    led.off()

def main():
    try:
        led = init_led()

        audio_data = get_audio_data()

        play_obj = play_audio(audio_data)    
    
        print("Playing audio")

        led_blink_reflect_music(led, audio_data, play_obj)

        play_obj.wait_done()
        print("Program finished.")
    except Exception as e:
        print(f"An error occurred: {e}")
        led.off()
        
if __name__=="__main__":
        main()
