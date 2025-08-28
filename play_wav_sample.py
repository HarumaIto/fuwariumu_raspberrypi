import pyaudio
import wave

CHUNK = 1024
WAVE_FILENAME = "output.wav"

def main():
  wf = wave.open(WAVE_FILENAME, 'rb')

  p = pyaudio.PyAudio()

  stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                  channels=wf.getnchannels(),
                  rate=wf.getframerate(),
                  output=True)

  data = wf.readframes(CHUNK)

  while data != b'':
    stream.write(data)
    data = wf.readframes(CHUNK)

  stream.stop_stream()
  stream.close()
  p.terminate()

if __name__ == "__main__":
  main()