from pydub import AudioSegment
import bme280_sample
import tsl2572_sample
from record_sample import record_audio
from api import post_data, get_task

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

def check_response_play_audio():
    for task_id in task_ids:
        response = get_task(task_id)
        if response["status"] == "completed":
            # ここに再生処理を実装
            print(f"Task {task_id} completed. Result: {response['result']}")
            task_ids.remove(task_id)

def main():
    bme280_sample.init()
    tsl2572_sample.init()

    for _ in range(3):
        if len(task_ids) != 0:
            check_response_play_audio()

        record_audio(5, WAVE_OUTPUT_FILENAME)
        wav_to_mp3()
        bme280_data = get_bme280_data()
        tsl2572_data = get_tsl2572_data()

        response = post_data(MP3_OUTPUT_FILENAME, bme280_data, tsl2572_data)
        task_ids.append(response["task_id"])

    check_response_play_audio()

if __name__ == "__main__":
    main()
