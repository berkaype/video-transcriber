from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import threading
import os
from moviepy import AudioFileClip
from transformers import pipeline
import speech_recognition as sr


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Transcription App")
        
        # BART modelini yükle
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Dil seçimi için dropdown menü
        self.language_frame = ttk.LabelFrame(root, text="Dil Seçimi")
        self.language_frame.pack(padx=10, pady=10, fill=BOTH, expand=False)
        
        self.language_label = ttk.Label(self.language_frame, text="Dil Seçin:")
        self.language_label.pack(side=LEFT, padx=5, pady=5)
        
        self.language_var = StringVar()
        self.language_var.set("tr-TR")  # Varsayılan olarak Türkçe
        self.language_dropdown = ttk.Combobox(
            self.language_frame, 
            textvariable=self.language_var,
            values=[
                "tr-TR (Türkçe)", 
                "en-US (İngilizce)", 
                "fr-FR (Fransızca)", 
                "de-DE (Almanca)", 
                "es-ES (İspanyolca)"
            ]
        )
        self.language_dropdown.pack(side=LEFT, padx=5, pady=5)
        self.language_dropdown.config(state="readonly")
        
        # Drop zone
        self.drop_frame = ttk.LabelFrame(root, text="Video Yükleme Alanı")
        self.drop_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        self.drop_label = ttk.Label(self.drop_frame, text="Video dosyasını buraya sürükleyin veya seçin")
        self.drop_label.pack(pady=50)
        
        self.select_button = ttk.Button(self.drop_frame, text="Video Seç", command=self.select_file)
        self.select_button.pack()
        
        # Transcription area
        self.transcript_frame = ttk.LabelFrame(root, text="Konuşma Metni")
        self.transcript_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        self.transcript_text = Text(self.transcript_frame, height=10)
        self.transcript_text.pack(padx=5, pady=5, fill=BOTH, expand=True)
        
        # Summary area
        self.summary_frame = ttk.LabelFrame(root, text="Video Özeti")
        self.summary_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        self.summary_text = Text(self.summary_frame, height=5)
        self.summary_text.pack(padx=5, pady=5, fill=BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(padx=10, pady=10, fill=X)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.process_video(file_path)

    def process_video(self, video_path):
        def process():
            try:
                self.progress.start()
                
                # Extract audio from video
                audio_clip = AudioFileClip(video_path)
                audio_path = "temp_audio.wav"
                audio_clip.write_audiofile(audio_path)
                
                # Initialize recognizer
                recognizer = sr.Recognizer()
                
                # Read the audio file
                with sr.AudioFile(audio_path) as source:
                    audio = recognizer.record(source)
                
                # Get selected language
                selected_language = self.language_var.get().split(" ")[0]
                
                # Perform speech recognition
                text = recognizer.recognize_google(audio, language=selected_language)
                
                # Update transcript text
                self.transcript_text.delete(1.0, END)
                self.transcript_text.insert(END, text)
                
                # Generate summary using BART
                transcript_content = self.transcript_text.get("1.0", END)
                summary = self.generate_summary(transcript_content)
                self.summary_text.insert(END, summary)
                
                # Clean up
                os.remove(audio_path)
                
            except Exception as e:
                print(f"Hata: {str(e)}")
            finally:
                self.progress.stop()
        
        thread = threading.Thread(target=process)
        thread.start()
        
    def generate_summary(self, text):
        # BART has a max input length, so we chunk the text if needed
        max_chunk = 1024
        chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
        
        summaries = []
        for chunk in chunks:
            summary = self.summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        
        return " ".join(summaries)

if __name__ == "__main__":
    root = Tk()
    app = TranscriptionApp(root)
    root.mainloop()
