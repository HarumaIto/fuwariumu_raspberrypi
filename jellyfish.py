import numpy as np
import matplotlib.pyplot as plt
from time import sleep, perf_counter
from led import hsv_to_rgb, init_led
from play_audio import get_audio_data, play_audio
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GAIN = 5

def led_blink_reflect_music(led, mono_audio, play_obj):
    # ledがNoneの場合、何もしない
    if led is None:
        logging.warning("LEDが初期化されていないため、LEDの点滅処理をスキップします。")
        # 音声だけ再生して終了
        play_obj.wait_done()
        return

    samples = np.array(mono_audio.get_array_of_samples())
    samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max

    actual_max_amplitude = np.max(np.abs(samples))
    if actual_max_amplitude == 0:
        actual_max_amplitude = 1.0 # 無音ファイルの場合のゼロ除算を防ぐ

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

        led_blink_reflect_music(led, audio_data, play_obj)

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