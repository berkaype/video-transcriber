from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import threading
import os
from moviepy import AudioFileClip
from transformers import pipeline
import whisper


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Transcription App")
        self.transcript_text = ""
        # BART modelini yükle
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        #whisper modelini yükle
        self.whisper_model = whisper.load_model("turbo")
        
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
        
        self.transcript_text_box = Text(self.transcript_frame, height=10)
        self.transcript_text_box.pack(padx=5, pady=5, fill=BOTH, expand=True)
        
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
                audio_path = "temp_audio.mp3"
                try:
                    audio_clip.write_audiofile(audio_path)
                except Exception as e:
                    print(f"Ses dosyası oluşturulamadı: {str(e)}")
                    return  # Hata durumunda işlemi durdur
                
                try:
                    # Whisper ile transkripsiyon
                    result = self.whisper_model.transcribe(audio_path)
                except Exception as e:
                    print(f"Whisper ses dosyasını okuyamadı: {str(e)}")
                    return
                
                segments = result['segments']
                
                # Transkript ve zaman kodlarını ekle
                self.transcript_text_box.delete(1.0, END)
                timecode_transcript_content = ""
                self.transcript_text = ""
                for segment in segments:
                    start_time = self.format_time(segment['start'])
                    end_time = self.format_time(segment['end'])
                    text = segment['text']
                    timecode_transcript_content += text + " "
                    self.transcript_text_box.insert(END, f"[{start_time} - {end_time}] {text}\n")
                    self.transcript_text += text  
                
                # Generate summary using BART
                summary = self.generate_summary(self.transcript_text)
                self.summary_text.insert(END, summary)
                
                # Clean up
                os.remove(audio_path)
                
            except Exception as e:
                print(f"Hata: {str(e)}")
            finally:
                self.progress.stop()
        
        thread = threading.Thread(target=process)
        thread.start()



    def format_time(self, seconds):
        """Zamanı saat:dakika:saniye,milliseconds formatına dönüştürür."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"
        
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
