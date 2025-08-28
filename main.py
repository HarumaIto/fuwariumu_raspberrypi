from pydub import AudioSegment
import bme280_sample
import tsl2572_sample
from record_sample import record_audio
from api import post_data, get_task
from led import init_led
from play_audio import get_audio_data, play_audio
from jellyfish import led_blink_reflect_music

WAVE_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"

task_ids = []

def wav_to_mp3():
    print("* converting wav to mp3...")
    audio = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    audio.export(MP3_OUTPUT_FILENAME, format="mp3")
    print("* mp3 saved")

def get_bme280_data() -> dict[str, float]:
    return bme280_sample.readData()

def get_tsl2572_data() -> dict[str, float]:
    return tsl2572_sample.readData()

def check_response_play_audio(led):
    for task_id in task_ids:
        response = get_task(task_id)
        if response["status"] == "completed":
            print(f"Task {task_id} completed. Result: {response['result']}")
            
            led = init_led()
            audio_data = get_audio_data()
            play_obj = play_audio(audio_data)
            
            print("Playing audio")
            led_blink_reflect_music(led, audio_data, play_obj)
            
            play_obj.wait_done()
            print("Program finished.")
            
            task_ids.remove(task_id)

def main():
    led = init_led()
    bme280_sample.init()
    tsl2572_sample.init()

    for _ in range(3):
        if len(task_ids) != 0:
            check_response_play_audio(led)

        record_audio(5, WAVE_OUTPUT_FILENAME)
        wav_to_mp3()
        bme280_data = get_bme280_data()
        tsl2572_data = get_tsl2572_data()

        response = post_data(MP3_OUTPUT_FILENAME, bme280_data, tsl2572_data)
        task_ids.append(response["task_id"])

    check_response_play_audio(led)

if __name__ == "__main__":
    main()
