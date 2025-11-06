import os
import ffmpeg
import whisper
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import datetime

# Initialize model
model = whisper.load_model("base")

# Ensure directories exist
os.makedirs("thumbnails", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

def extract_audio(video_path, audio_path, progress_callback=None):
    stream = ffmpeg.input(video_path)
    stream = ffmpeg.output(stream, audio_path, format='mp3', acodec='mp3')
    ffmpeg.run(stream, overwrite_output=True)
    if progress_callback:
        progress_callback(50)  # Audio extraction completed (50%)

def generate_thumbnail(video_path, thumbnail_path):
    ffmpeg.input(video_path, ss=1).output(thumbnail_path, vframes=1).run(overwrite_output=True)

def transcribe_audio(audio_path, progress_callback=None):
    result = model.transcribe(audio_path)
    if progress_callback:
        progress_callback(100)  # Transcription completed (100%)
    return result["segments"]

def format_transcription(segments):
    formatted_text = ""
    for seg in segments:
        start = str(datetime.timedelta(seconds=int(seg['start'])))
        end = str(datetime.timedelta(seconds=int(seg['end'])))
        text = seg['text'].strip()
        formatted_text += f"[{start} - {end}] {text}\n"
    return formatted_text

def update_progress(val):
    progress_bar['value'] = val
    root.update_idletasks()

def handle_drop(event):
    files = root.splitlist(event.data)
    for file in files:
        file = file.strip('{}')
        if os.path.isfile(file):
            video_title.config(text=os.path.basename(file))
            progress_bar['value'] = 0
            thumbnail_path = f"thumbnails/{os.path.basename(file)}.png"
            
            try:
                # Generate thumbnail
                generate_thumbnail(file, thumbnail_path)
                thumb_img = Image.open(thumbnail_path)
                thumb_img = thumb_img.resize((200, 120))
                thumb_img_tk = ImageTk.PhotoImage(thumb_img)
                thumbnail_label.config(image=thumb_img_tk)
                thumbnail_label.image = thumb_img_tk

                # Extract and transcribe audio
                audio_path = f"uploads/temp_audio.mp3"
                extract_audio(file, audio_path, update_progress)
                segments = transcribe_audio(audio_path, update_progress)
                transcription = format_transcription(segments)
                os.remove(audio_path)

                text_box.insert(tk.END, f"\n{os.path.basename(file)}:\n{'='*60}\n{transcription}\n")
                text_box.see(tk.END)
            except Exception as e:
                text_box.insert(tk.END, f"\nError: {e}\n{'-'*60}\n")
                text_box.see(tk.END)

# GUI setup
root = TkinterDnD.Tk()
root.title("Enhanced Video Transcriber")
root.geometry("900x700")
root.config(bg="#2E3440")

# Video Title
video_title = tk.Label(root, text="Drop Video Here", font=("Arial", 16), bg="#88C0D0", fg="#2E3440")
video_title.pack(pady=5, fill=tk.X)

# Thumbnail display
thumbnail_label = tk.Label(root, bg="#3B4252")
thumbnail_label.pack(pady=10)

# Drop area
drop_area = tk.Label(root, text="📂 Drag & Drop Video 📂", font=("Arial", 30), bg="#3B4252", fg="#ECEFF4")
drop_area.pack(pady=20, padx=20, expand=True, fill=tk.BOTH)
drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind("<<Drop>>", handle_drop)

# Progress Bar
progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate', length=500)
progress_bar.pack(pady=10, padx=10)

# Transcription Textbox
text_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 11), bg="#D8DEE9", fg="#2E3440")
text_box.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

root.mainloop()
