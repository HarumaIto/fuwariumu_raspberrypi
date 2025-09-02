import numpy as np
import random
import matplotlib.pyplot as plt
from time import sleep, perf_counter
from led import hsv_to_rgb, init_led
from play_audio import get_audio_data, play_audio
from servo import Servo
from colorsys import rgb_to_hsv 
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ROTATE_SERVO = 12
VERTICAL_SERVO = 13

GAIN = 5

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def lerp(a, b, t):
    return a + (b - a) * t

def simulation_motion(bpm, period):
    """
    bpm: 曲のテンポ
    period: 拍の回数
    """
    dt = 60 / bpm
    duration = dt * period
    times = []
    angles = []

    angle_bottom = 90
    angle_top = -75
    amplitude = angle_bottom - angle_top

    elapsed = 0
    while elapsed < duration:
        phase = (elapsed % duration) / duration

        if phase < 0.3:
            angle = angle_bottom - amplitude * (1 - (1 - phase / 0.3)**2)
        else:
            angle = angle_bottom - amplitude * (1 - (phase - 0.3) / 0.7**0.5)

        times.append(elapsed)
        angles.append(angle)

        elapsed += dt

    return times, angles

def led_blink_reflect_music(led, mono_audio, bpm, play_obj, min_color, max_color):
    rotate = Servo(ROTATE_SERVO)
    vertical = Servo(VERTICAL_SERVO)

    # ledがNoneの場合、何もしない
    if led is None and rotate is None and vertical is None:
        logging.warning("LEDが初期化されていないため、LEDの点滅処理をスキップします。")
        # 音声だけ再生して終了
        play_obj.wait_done()
        return

    min_rgb = hex_to_rgb(min_color)
    max_rgb = hex_to_rgb(max_color)
    min_hsv = rgb_to_hsv(*min_rgb)
    max_hsv = rgb_to_hsv(*max_rgb)

    samples = np.array(mono_audio.get_array_of_samples())
    samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max

    actual_max_amplitude = np.max(np.abs(samples))
    if actual_max_amplitude == 0:
        actual_max_amplitude = 1.0 # 無音ファイルの場合のゼロ除算を防ぐ

    sample_rate = mono_audio.frame_rate
    chunk_size = int(sample_rate * 0.01)

    current_time = 0

    current_hue = random.random()

    tempo_count = 0
    while play_obj.is_playing():
        if tempo_count == 0 or tempo_count % 16 == 0:
            times, angles = simulation_motion(bpm, 16)
            vertical.move_with_profile(times, angles)

        tempo_count += 1
        start_time = perf_counter()
        current_sample = int(current_time * sample_rate)

        chunk_start = current_sample
        chunk_end = min(current_sample + chunk_size, len(samples))
        if chunk_start >= chunk_end:
            break

        chunk = samples[chunk_start:chunk_end]

        amplitude = np.mean(np.abs(chunk))

        normalized_amplitude = amplitude / actual_max_amplitude
        normalized_amplitude = np.sqrt(normalized_amplitude)
        normalized_amplitude = max(0.0, min(1.0, normalized_amplitude))

        hue = lerp(min_hsv[0], max_hsv[0], normalized_amplitude, )
        saturation = lerp(min_hsv[1], max_hsv[1], normalized_amplitude)
        value = lerp(min_hsv[2], max_hsv[2], normalized_amplitude)

        current_hue = current_hue + (random.random() - 0.5) * 0.01
        if current_hue < 0:
            current_hue += 1.0
        elif current_hue > 1.0:
            current_hue -= 1.0

        led.color = hsv_to_rgb(hue, saturation, value)

        end_time = perf_counter()
        elapsed_time = (end_time - start_time) / 60
        sleep_time = 60 / bpm - elapsed_time
        current_time = current_time + (sleep_time + elapsed_time)
        sleep(sleep_time)

    led.off()

def main():
    led = None
    try:
        led = init_led()
        
        audio_data = get_audio_data()
        if audio_data is None:
            logging.error("音声データの取得に失敗しました。")
            return

        play_obj = play_audio(audio_data)
        if play_obj is None:
            logging.error("音声の再生に失敗しました。")
            return
    
        print("Playing audio")
        bpm = 120
        min_color = "#0000FF"  # 青
        max_color = "#FF0000"  # 赤
        led_blink_reflect_music(led, audio_data, bpm, play_obj, min_color, max_color)

        # play_obj.wait_done() は led_blink_reflect_music の中で呼ばれるか、
        # もしくはLED処理と並行して待つべきか設計によりますが、
        # 現状のコードでは led_blink_reflect_music がブロッキングするので、ここでは不要かもしれません。
        # ただし、LED処理をスキップした場合は待つ必要があります。
        if led is None and play_obj:
            play_obj.wait_done()

        print("Program finished.")
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
    finally:
        if led:
            led.off()
        
if __name__=="__main__":
        main()
