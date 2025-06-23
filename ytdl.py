import yt_dlp
import os

def download_song(query, save_path="downloads"):
    os.makedirs(save_path, exist_ok=True)

    file_path = None

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "cookiefile": "cookies.txt",
        "default_search": "ytsearch1",
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if not info:
            print("Error: Could not extract information.")
            return None
        
        if 'requested_downloads' in info:
            for entry in info['requested_downloads']:
                if 'filepath' in entry:
                    original_file = entry['filepath'] 
                    converted_file = os.path.splitext(original_file)[0] + ".mp3"
                    if os.path.exists(converted_file):
                        file_path = converted_file

        if not file_path:
            for filename in os.listdir(save_path):
                if filename.endswith(".mp3"):
                    file_path = os.path.join(save_path, filename)
                    break

        if file_path and os.path.exists(file_path):
            return file_path
        else:
            print("❌ Error: MP3 file not found after conversion.")
            return None