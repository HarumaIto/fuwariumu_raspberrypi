from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import numpy as np
import matplotlib.pyplot as plt
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_audio_waveform(file_path):
	try:
		# ファイル形式を自動判別して読み込み
		audio = AudioSegment.from_file(file_path)
		
		sample_rate = audio.frame_rate
		mono_audio = audio.set_channels(1)
		
		data = np.array(mono_audio.get_array_of_samples())

		# データを[-1, 1]の範囲に正規化
		if data.dtype == np.int16:
			data = data.astype(np.float32) / 32768.0
		elif data.dtype == np.int32:
			data = data.astype(np.float32) / 2147483648.0
		else:
			# 他のデータ型の場合は、最大値で割る
			max_val = np.iinfo(data.dtype).max
			if max_val > 0:
				data = data.astype(np.float32) / max_val

		time = np.linspace(0, len(data) / sample_rate, num=len(data), endpoint=False)

		plt.figure(figsize=(15, 5))
		plt.plot(time, data, color='blue', linewidth=0.5)
		plt.title('Audio Waveform')
		plt.xlabel('Time (s)')
		plt.ylabel('Amplitude')
		plt.grid(True)
		plt.show()
	except FileNotFoundError:
		logging.error(f"ファイルが見つかりません: {file_path}")
	except CouldntDecodeError as e:
		logging.error(f"ファイルのデコードに失敗しました: {file_path}, Error: {e}")
	except Exception as e:
		logging.error(f"波形生成中に予期せぬエラーが発生しました: {e}")

def main():
	# このパスはご自身の環境に合わせて変更してください
	filePath = "output.mp3" # 例としてカレントディレクトリのファイルを指定
	get_audio_waveform(filePath)

if __name__ == "__main__":
	main()