from pydub import AudioSegment
import numpy as np
import matplotlib.pyplot as plt

def get_audio_waveform(file_path):
	try:
		audio = AudioSegment.from_mp3(file_path)
		
		sample_rate = audio.frame_rate
		mono_audio = audio.set_channels(1)
		
		data = np.array(mono_audio.get_array_of_samples())

		data = data.astype(np.float32) / np.iinfo(data.dtype).max

		time = np.linspace(0, len(data) / sample_rate, len(data))

		plt.figure(figsize=(15, 5))
		plt.plot(time, data, color='blue', linewidth=0.5)
		plt.title('Audio Waveform')
		plt.ylabel('Amplitude')
		plt.grid(True)
		plt.show()
	except FileNotFoundError:
		print(f"Error: The file at {file_path} was not found.")
	except Exception as e:
		print(f"An error occurred: {e}")

def main():
	filePath = "/home/intern/Music/school_hallway_sound.mp3"
	get_audio_waveform(filePath)

if __name__ == "__main__":
	main() 
