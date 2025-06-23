import speech_recognition as sr
from gen import chat_with_gemini
import winsound

# Find the correct microphone index
mic_index = 1  # Change this to your actual mic index
LANGUAGE_CODE = "en-US"

recognizer = sr.Recognizer()

with sr.Microphone(device_index=mic_index) as source:
    print("🎤 Listening... (Press Ctrl+C to stop)")
    recognizer.adjust_for_ambient_noise(source)
    is_called = False
    try:
        while True:
            print("🎙️ Speak something...")
            audio = recognizer.listen(source)
            
            try:
                text = recognizer.recognize_google(audio, language=LANGUAGE_CODE)
                text = text.replace("retina","Hey tina")
                text = text.replace("retino", "Hey tina")
                print(f"📝 You said: {text}")
                if "tina" in text.lower() or is_called:
                    is_called = True
                    temp_audio_path = chat_with_gemini(text)
                    try:
                        winsound.PlaySound(temp_audio_path, winsound.SND_FILENAME)
                    except:
                        pass

            except sr.UnknownValueError:
                print("❌ Could not understand the audio.")
            except sr.RequestError:
                print("⚠️ Could not request results. Check your internet connection.")

    except KeyboardInterrupt:
        print("\n🔴 Stopped listening.")
