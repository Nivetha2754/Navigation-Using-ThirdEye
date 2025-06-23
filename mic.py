import pyaudio
import time
import json
import winsound
from rev_ai.models import MediaConfig
from rev_ai.streamingclient import RevAiStreamingClient
from rev_ai import custom_vocabularies_client
from rev_ai.models import CustomVocabulary
from six.moves import queue  # type: ignore
from gen import cv2, cap, chat_with_gemini

def get_bluetooth_mic_index():
    """Finds and returns the index of the Bluetooth microphone."""
    p = pyaudio.PyAudio()
    bt_mic_index = None
    print("Available Audio Devices:")

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"Index {i}: {dev['name']} (Input Channels: {dev['maxInputChannels']})")

        # Check if the device is an input mic and matches a Bluetooth headset pattern
        if dev['maxInputChannels'] > 0 and "Hands-Free AG Audio" in dev['name']:
            bt_mic_index = i
            print(f"✅ Selected Bluetooth Mic: {dev['name']} (Index: {bt_mic_index})")
            break  # Use the first detected Bluetooth mic
    
    p.terminate()
    return bt_mic_index



class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk, device_index=None):
        self._rate = rate
        self._chunk = chunk
        self.device_index = device_index
        self._buff = queue.Queue()
        self.closed = True
        self._audio_stream = None
        self._audio_interface = None
        self.paused = False  # Track whether mic is paused

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            input_device_index=self.device_index,  # Use Bluetooth Mic
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        if not self.paused:  # Only add data if mic is not paused
            self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

    def pause(self):
        """Pause the microphone stream (stop capturing input)."""
        if self._audio_stream and not self.paused:
            self.paused = True
            self._audio_stream.stop_stream()

    def resume(self):
        """Resume the microphone stream (start capturing input again)."""
        if self._audio_stream and self.paused:
            self.paused = False
            self._audio_stream.start_stream()

    def stop(self):
        """Properly close the stream."""
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        if self._audio_interface:
            self._audio_interface.terminate()
        self.closed = True
        self._buff.put(None)

# Get Bluetooth microphone index
bluetooth_mic_index = get_bluetooth_mic_index()

if bluetooth_mic_index is None:
    print("Bluetooth microphone not found. Please ensure it is connected.")
    exit(1)

rate = 16000  
chunk = int(rate / 10)
access_token = "02b656nIB7zDP6GsjpUADKRig07Vdzdziy9PrYhm-lINpl20sydL_n6csXNDFkzdTuWl4yAW3Vwii3AUA0H6-775YvWFg"
example_mc = MediaConfig('audio/x-raw', 'interleaved', 16000, 'S16LE', 1)

client = custom_vocabularies_client.RevAiCustomVocabulariesClient(access_token)
custom_vocabulary = CustomVocabulary(["hey tina", "tina", "hi dina"])

# submit the CustomVocabulary
custom_vocabularies_job = client.submit_custom_vocabularies([custom_vocabulary])


streamclient = RevAiStreamingClient(access_token, example_mc)

def play_audio_and_pause_mic(temp_audio_path):
    winsound.PlaySound(temp_audio_path, winsound.SND_FILENAME)
    time.sleep(0.5)

# --- Main Recording Process ---
with MicrophoneStream(rate, chunk, bluetooth_mic_index) as stream:
    try:
        response_gen = streamclient.start(stream.generator(), filter_profanity=True)
        
        for response in response_gen:
            response_data = json.loads(response)  # Convert JSON string to dictionary
            print(response_data)

            if response_data.get("type") == "final":
                final_text = "".join(
                    elem["value"] for elem in response_data.get("elements", []) if elem["value"] != "<unk>"
                )
                if "tina" in final_text.lower() or "dina" in final_text.lower():
                    print("You:", final_text)
                    stream.pause()
                    temp_audio_path = chat_with_gemini(final_text)
                    play_audio_and_pause_mic(temp_audio_path)
                    stream.resume()

    except KeyboardInterrupt:
        streamclient.client.send("EOS")

cap.release()
cv2.destroyAllWindows()
