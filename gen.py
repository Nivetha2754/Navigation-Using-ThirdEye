import google.generativeai as genai
from PIL import Image
import cv2
import os
import requests
import base64
import winsound
import threading
from pydub import AudioSegment
from io import BytesIO
from datetime import datetime
from mongo import notesdb
from pymongo import TEXT
from ytdl import download_song
from datetime import datetime
import pytz
from face import *


import pygame

notesdb.create_index([("note", TEXT)])

TEMP_IMAGE_DIR = "temp_images"
IMAGE_PATH = "captured_image.jpg"

os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

genai.configure(api_key="AIzaSyD4vxY-2AXCn3TD-RwxBNAx9_31BzwTDZM")

SYSTEM_PROMPT = """Your name is Tina and you are a helpful assistant for visually disabled persons. 
You are present in Envision Glass and you help them with navigation, general questions, shopping, 
daily information, etc. Every time with the user's prompt, you will get an image. 
You need to provide the response based on the image or even without using that image for certain questions.
And don't say that based on the image or from the image. 
and also don't have the visuals so you need to guide them, for example guide me to the door, you need to guide them like go two steps ahead, turn left or i couldn't find any doors infront of you please turn and say again.
Be careful with them. Now you are an assistant to a person named Sathish.
Act like a friend not like a AI, use humans words like hmm, yeah, hum mm, awww,... etc. you can use these words as much as you can to siumulate human like response.

Function calls metadata
use save_image to save the current image and return the image path.
use save_note to save any notes to the database, you can directly add the notes without asking my permission. you can save anything that you need in future, it is act like a persistent memory to you. you can save anything like my preference, personal information,...etc.
use get_similar_notes to retrive the notes from the query even if you don't know about it already you can use it to find any information. like user's preference, personal information,... everything about me, you can directly check notes without asking me.
use play_song, resume_song, pause_song, stop_song functions to play/resume/pause/stop the song.
use get_current_datetime('Asia/Kolkata') to get the current date and time.
use detect_face face to know who is infront of the camera, you can call this function when the user ask who is infront of me?.
use add_face to add any user to the database, you can call this function when the user ask to remeber or store this user is currently infront of me.
"""

def save_image():
    ret, frame = cap.read()
    if ret:
    
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(TEMP_IMAGE_DIR, f"temp_{timestamp}.jpg")

        cv2.imwrite(image_path, frame)
        print(f"📸 Image captured and saved as {image_path}")
        return image_path
    else:
        print("❌ Failed to capture image")
        return None
    
def save_note(note: str):
    """Save a note in the database."""
    note_data = {
        "note": note,
        "timestamp": datetime.utcnow()
    }
    notesdb.insert_one(note_data)
    return "Note saved successfully."

def get_similar_notes(query: str):
    """Retrieve notes similar to the given query."""
    limit: int = 5
    results = notesdb.find({"$text": {"$search": query}}).limit(limit)
    return [note["note"] for note in results]

def detect_face():
    print("face detect called.")
    data = recognition.recognize(image_path=IMAGE_PATH)
    return data

def add_face(name: str):
    data = face_collection.add(image_path=IMAGE_PATH, subject=name)
    return True

def play_song(song_name: str):
    pygame.mixer.init()
    song_path = download_song(song_name)
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    return f"Music is Started Playing... song_path:{song_path}"

def pause_song(is_pause: bool):
    pygame.mixer.music.pause()
    return "Music Paused..."

def resume_song(is_pause: bool):
    pygame.mixer.music.unpause()
    return "Music Resumed..."

def stop_song(song_path:str):
    pygame.mixer.music.unload()
    os.remove(song_path)
    return "Music Stopped"

def get_current_datetime(timezone: str) -> str:
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    except pytz.UnknownTimeZoneError:
        return "Invalid timezone. Please provide a valid timezone string."



model = genai.GenerativeModel(model_name="gemini-2.0-flash",
                              system_instruction=SYSTEM_PROMPT,tools=[save_image,save_note,get_similar_notes,play_song,pause_song,resume_song,stop_song,get_current_datetime,detect_face,add_face])

chat_session = model.start_chat(enable_automatic_function_calling=True)

TOKEN_LIMIT = 104500
total_tokens_used = 0

cap = cv2.VideoCapture(f"http://192.168.1.126:4747/video", cv2.CAP_FFMPEG) 
TTS_API_URL = "https://voice.ridemap365.in/tts?paragraphChunks="
ret = None
frame = None

def show_webcam():
    global ret, frame
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read from webcam")
            break
        cv2.imshow("Live Feed - Press 'q' to Exit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def capture_webcam():
    if not ret:
        print("Failed to read from webcam")
        capture_webcam()
    else:
        cv2.imwrite(IMAGE_PATH, frame)
        return IMAGE_PATH

thread = threading.Thread(target=show_webcam, daemon=True)
thread.start()

def text_to_speech(text):
    try:
        response = requests.get(TTS_API_URL + text)
        response_data = response.json()
        audio_base64 = response_data.get("audioStream", "")
        if not audio_base64:
            print("❌ No audio data received.")
            return
        audio_bytes = base64.b64decode(audio_base64)
        temp_audio_path = "temp_audio.wav"
        audio_segment = AudioSegment.from_file(BytesIO(audio_bytes), format="ogg")
        audio_segment.export(temp_audio_path, format="wav")
        return temp_audio_path
    except Exception as e:
        print("❌ TTS Error:", e)

def chat_with_gemini(user_input):
    global total_tokens_used, chat_session
    try:
        image_path = capture_webcam()
        if image_path:
            image = Image.open(image_path)
            response = chat_session.send_message([user_input, image])
            tina_response = response.text
            file_path = text_to_speech(tina_response)
            print("\nTina:", tina_response)
        else:
            print("❌ Image not captured, skipping image context.")
    except Exception as e:
        print("Error:", e)
        chat_with_gemini(user_input)
    return file_path

def chat_with():
    while True:
        que = input("You: ")
        temp_audio_path = chat_with_gemini(que)
        try:
            winsound.PlaySound(temp_audio_path, winsound.SND_FILENAME)
        except:
            pass

chat_with()