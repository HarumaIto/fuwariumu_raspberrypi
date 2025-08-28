from pydub import AudioSegment
import bme280_sample
import tsl2572_sample
from record_sample import record_audio
import io
import sys

WAVE_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"

def wav_to_mp3():
    print("* converting wav to mp3...")
    audio = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    audio.export(MP3_OUTPUT_FILENAME, format="mp3")
    print("* mp3 saved")

def get_bme280_data():
    buf = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buf
    bme280_sample.readData()
    sys.stdout = sys_stdout
    return buf.getvalue()

def get_tsl2572_data():
    tsl2572_sample.initTSL2572()
    adc = tsl2572_sample.getTSL2572adc()
    atime = tsl2572_sample.ATIME
    gain = tsl2572_sample.GAIN
    cpl = (2.73 * (256 - atime) * gain)/(60.0)
    lux1 = ((adc[0] * 1.00) - (adc[1] * 1.87)) / cpl
    lux2 = ((adc[0] * 0.63) - (adc[1] * 1.00)) / cpl
    lux = max(lux1, lux2, 0)
    return {"adc0": adc[0], "adc1": adc[1], "lux": lux}

def post_data(mp3_path, bme280_str, tsl2572_dict):
    print("* posting data (mock)...")
    # url = "http://example.com/api/upload"  # モックURL
    # files = {"file": open(mp3_path, "rb")}
    # data = {
    #     "bme280": bme280_str,
    #     "tsl2572": str(tsl2572_dict)
    # }
    # 実際のPOSTはコメントアウト
    # response = requests.post(url, files=files, data=data)
    # print("POST status:", response.status_code)
    print("bme280:", bme280_str)
    print("tsl2572:", tsl2572_dict)
    print("* post done (mock)")

def main():
    record_audio(300, WAVE_OUTPUT_FILENAME)
    wav_to_mp3()
    bme280_str = get_bme280_data()
    tsl2572_dict = get_tsl2572_data()
    post_data(MP3_OUTPUT_FILENAME, bme280_str, tsl2572_dict)

if __name__ == "__main__":
    main()
