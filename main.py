from pydub import AudioSegment
import bme280_sample
import tsl2572_sample
from record_sample import record_audio
from api import post_data

WAVE_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"

def wav_to_mp3():
    print("* converting wav to mp3...")
    audio = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    audio.export(MP3_OUTPUT_FILENAME, format="mp3")
    print("* mp3 saved")

def get_bme280_data() -> dict[str, float]:
    return bme280_sample.readData()

def get_tsl2572_data() -> dict[str, float]:
    return tsl2572_sample.readData()

def main():
    bme280_sample.init()
    tsl2572_sample.init()

    record_audio(300, WAVE_OUTPUT_FILENAME)
    wav_to_mp3()
    bme280_data = get_bme280_data()
    tsl2572_data = get_tsl2572_data()
    post_data(MP3_OUTPUT_FILENAME, bme280_data, tsl2572_data)

if __name__ == "__main__":
    main()
