import os
import warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=UserWarning)

from tkinter import *
from tkinter import ttk, filedialog, messagebox
import threading
from moviepy import AudioFileClip
import whisper 

try:
    import cv2
    from PIL import Image, ImageTk
    THUMBNAIL_ENABLED = True
except ImportError:
    THUMBNAIL_ENABLED = False


class ModernTranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SpeechRecog")
        self.root.geometry("1280x720")
        self.root.configure(bg='#2b2b2b')
        
        # Modern renkler
        self.colors = {
            'bg': '#2b2b2b',
            'card_bg': '#3c3c3c',
            'accent': '#0078d4',
            'accent_hover': '#106ebe',
            'text': '#ffffff',
            'text_secondary': '#cccccc',
            'success': '#107c10',
            'error': '#d13438'
        }
        
        # Modern font
        self.fonts = {
            'heading': ('Segoe UI', 16, 'bold'),
            'subheading': ('Segoe UI', 12, 'bold'),
            'body': ('Segoe UI', 10),
            'small': ('Segoe UI', 9)
        }
        
        self.transcript_text = ""
        self.whisper_model = None
        self.is_processing = False
        
        self.setup_ui()
        self.load_model()
    
    def setup_ui(self):
        # Ana container
        main_frame = Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # ==========================================================
        # ÇÖZÜM: PAKETLEME SIRASINI DEĞİŞTİR
        # Önce alta gelecekler, sonra üste gelecekler, en son da
        # kalan boşluğu dolduracak olanlar paketlenir.
        # ==========================================================
        
        # 1. EN ALTA GELECEKLERİ EN BAŞTA PAKETLE (side=BOTTOM ile)
        self.create_status_bar(main_frame)
        self.create_progress_bar(main_frame)
        
        # 2. EN ÜSTE GELECEKLERİ SONRA PAKETLE
        # Başlık
        title_frame = Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(fill=X, pady=(0, 20), side=TOP)
        
        title_label = Label(
            title_frame,
            text="🎤 SpeechRecog",
            font=self.fonts['heading'],
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack()
        
        subtitle_label = Label(
            title_frame,
            text="AI destekli ses tanıma ve transkripsiyon aracı",
            font=self.fonts['body'],
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack()
        
        # Dosya yükleme kartı
        self.create_upload_card(main_frame)
        
        # 3. ORTADA KALAN ALANI DOLDURACAK OLANI EN SON PAKETLE
        # Bu, expand=True sayesinde kalan tüm boşluğu kaplayacaktır.
        self.create_transcription_cards(main_frame)

    
    def update_progress(self, message, percentage):
        """Progress durumunu güncelle"""
        self.progress['value'] = percentage
        self.progress_label.configure(text=f"{message} ({percentage}%)")
        self.update_status(message)
        self.root.update_idletasks()
    
    def reset_progress(self):
        """Progress bar'ı sıfırla"""
        self.progress['value'] = 0
        self.progress_label.configure(text="Hazır - Video seçin")
    
    def show_thumbnail(self, video_path):
        """Video thumbnail'ını göster"""
        if not THUMBNAIL_ENABLED:
            print("Thumbnail için cv2 ve Pillow kütüphaneleri gerekli.")
            file_name = os.path.basename(video_path)
            file_size = os.path.getsize(video_path) / (1024*1024)
            self.drop_label.configure(text=f"✅ Video seçildi: {file_name}")
            self.file_info_label.configure(text=f"Boyut: {file_size:.1f} MB")
            self.file_info_label.pack(pady=(5, 0))
            return

        try:
            # Video'dan ilk frame'i al
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Boyutları ayarla (max 200x150)
                height, width = frame_rgb.shape[:2]
                max_width, max_height = 200, 150
                
                if width > max_width or height > max_height:
                    ratio = min(max_width/width, max_height/height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                
                pil_image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Başlangıç widget'larını gizle
                self.icon_label.pack_forget()
                self.drop_label.pack_forget()
                self.formats_label.pack_forget()
                
                # Thumbnail'ı göster
                self.thumbnail_label.configure(image=photo)
                self.thumbnail_label.image = photo  # Referansı tut
                self.thumbnail_label.pack(pady=(0, 10))
                
                # Dosya bilgisini göster
                file_name = os.path.basename(video_path)
                file_size = os.path.getsize(video_path) / (1024*1024)  # MB
                self.file_info_label.configure(text=f"✅ {file_name}\nBoyut: {file_size:.1f} MB")
                self.file_info_label.pack(pady=(0, 10))
                
                # Yeni video seçimi için buton
                # Buton zaten varsa tekrar oluşturma
                if not hasattr(self, 'new_video_btn'):
                    self.new_video_btn = Button(
                        self.drop_inner,
                        text="🔄 Başka Video Seç",
                        font=self.fonts['small'],
                        bg=self.colors['accent'],
                        fg='white',
                        relief='flat',
                        bd=0,
                        padx=15,
                        pady=5,
                        cursor='hand2',
                        command=self.reset_upload_area
                    )
                self.new_video_btn.pack()
                
        except Exception as e:
            print(f"Thumbnail oluşturulamadı: {e}")
            # Hata durumunda sadece dosya bilgisini göster
            file_name = os.path.basename(video_path)
            file_size = os.path.getsize(video_path) / (1024*1024)
            
            self.drop_label.configure(text=f"✅ Video seçildi: {file_name}")
            self.file_info_label.configure(text=f"Boyut: {file_size:.1f} MB")
            self.file_info_label.pack(pady=(5, 0))
    
    def reset_upload_area(self):
        """Upload alanını sıfırla"""
        # Thumbnail, dosya bilgisi ve butonu gizle
        self.thumbnail_label.pack_forget()
        self.file_info_label.pack_forget()
        if hasattr(self, 'new_video_btn'):
            self.new_video_btn.pack_forget()
        
        # Orijinal widget'ları geri getir
        self.icon_label.pack()
        self.drop_label.configure(text="Video dosyasını seçmek için tıklayın")
        self.drop_label.pack(pady=(10, 0))
        self.formats_label.pack(pady=(5, 0))
        
        # Progress'i sıfırla
        self.reset_progress()
    
    def create_upload_card(self, parent):
        card = Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=0)
        card.pack(fill=X, pady=(0, 15), side=TOP) # DEĞİŞİKLİK: side=TOP eklendi
        
        inner_frame = Frame(card, bg=self.colors['card_bg'])
        inner_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        self.drop_frame = Frame(inner_frame, bg='#404040', relief='flat', bd=2)
        self.drop_frame.pack(fill=X, pady=(0, 15))
        
        self.drop_inner = Frame(self.drop_frame, bg='#404040')
        self.drop_inner.pack(fill=X, padx=30, pady=40)
        
        self.icon_label = Label(self.drop_inner, text="📁", font=('Segoe UI', 24), bg='#404040', fg=self.colors['text'])
        self.icon_label.pack()
        
        self.drop_label = Label(self.drop_inner, text="Video dosyasını seçmek için tıklayın", font=self.fonts['body'], bg='#404040', fg=self.colors['text_secondary'])
        self.drop_label.pack(pady=(10, 0))
        
        self.file_info_label = Label(self.drop_inner, text="", font=self.fonts['small'], bg='#404040', fg=self.colors['success'], wraplength=400)
        
        self.thumbnail_label = Label(self.drop_inner, bg='#404040')
        
        self.formats_label = Label(self.drop_inner, text="Desteklenen formatlar: MP4, AVI, MOV, MKV, WMV", font=self.fonts['small'], bg='#404040', fg=self.colors['text_secondary'])
        self.formats_label.pack(pady=(5, 0))
        
        for widget in [self.drop_frame, self.drop_inner, self.icon_label, self.drop_label, self.formats_label]:
            widget.bind("<Button-1>", lambda e: self.select_file())
    
    def create_transcription_cards(self, parent):
        trans_container = Frame(parent, bg=self.colors['bg'])
        trans_container.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        self.create_transcript_card(trans_container, "⏰ TimeCode Transcript", "timecode")
        self.create_transcript_card(trans_container, "📝 Transkript", "clean")
    
    def create_transcript_card(self, parent, title, card_type):
        card = Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=0)
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10) if card_type == "timecode" else (10, 0))
        
        inner_frame = Frame(card, bg=self.colors['card_bg'])
        inner_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        header_frame = Frame(inner_frame, bg=self.colors['card_bg'])
        header_frame.pack(fill=X, pady=(0, 10))
        
        title_label = Label(header_frame, text=title, font=self.fonts['subheading'], bg=self.colors['card_bg'], fg=self.colors['text'])
        title_label.pack(side=LEFT)
        
        delete_btn = self.create_mini_button(header_frame, "🗑️", lambda: self.delete_transcript(card_type))
        delete_btn.pack(side=RIGHT, padx=(5, 0))

        copy_btn = self.create_mini_button(header_frame, "📋", lambda: self.copy_transcript(card_type))
        copy_btn.pack(side=RIGHT, padx=(5, 0))
        
        save_btn = self.create_mini_button(header_frame, "💾", lambda: self.save_transcript(card_type))
        save_btn.pack(side=RIGHT)
        
        text_frame = Frame(inner_frame, bg=self.colors['card_bg'])
        text_frame.pack(fill=BOTH, expand=True)
        
        text_widget = Text(text_frame, font=self.fonts['body'], bg='#404040', fg=self.colors['text'], insertbackground=self.colors['text'], selectbackground=self.colors['accent'], relief='flat', bd=0, padx=10, pady=10, wrap=WORD)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        if card_type == "timecode":
            self.timecode_text = text_widget
        else:
            self.clean_text = text_widget
    
    def create_progress_bar(self, parent):
        self.progress_container = Frame(parent, bg=self.colors['bg'])
        # DEĞİŞİKLİK: side=BOTTOM eklendi.
        self.progress_container.pack(fill=X, pady=(0, 15), side=BOTTOM)
        
        self.progress_title = Label(self.progress_container, text="İşlem Durumu", font=self.fonts['subheading'], bg=self.colors['bg'], fg=self.colors['text'])
        self.progress_title.pack(anchor=W, pady=(0, 10))
        
        style = ttk.Style()
        style.configure("Modern.Horizontal.TProgressbar", background=self.colors['accent'], troughcolor='#404040', borderwidth=1, lightcolor=self.colors['accent'], darkcolor=self.colors['accent'], thickness=25)
        
        self.progress = ttk.Progressbar(self.progress_container, mode='determinate', style="Modern.Horizontal.TProgressbar", length=500, value=0)
        self.progress.pack(fill=X, pady=(0, 10))
        
        self.progress_label = Label(self.progress_container, text="Hazır - Video seçin", font=self.fonts['body'], bg=self.colors['bg'], fg=self.colors['text_secondary'], anchor=W)
        self.progress_label.pack(fill=X)
    
    def create_status_bar(self, parent):
        status_frame = Frame(parent, bg=self.colors['bg'])
        # DEĞİŞİKLİK: side=BOTTOM eklendi.
        status_frame.pack(fill=X, side=BOTTOM)
        
        self.status_label = Label(status_frame, text="Hazır", font=self.fonts['small'], bg=self.colors['bg'], fg=self.colors['text_secondary'], anchor=W)
        self.status_label.pack(side=LEFT)
        
        self.model_status = Label(status_frame, text="Model yükleniyor...", font=self.fonts['small'], bg=self.colors['bg'], fg=self.colors['text_secondary'], anchor=E)
        self.model_status.pack(side=RIGHT)
    
    def create_mini_button(self, parent, text, command):
        button = Button(parent, text=text, command=command, font=self.fonts['small'], bg='#505050', fg='white', relief='flat', bd=0, padx=8, pady=4, cursor='hand2')
        button.bind("<Enter>", lambda e: button.configure(bg='#606060'))
        button.bind("<Leave>", lambda e: button.configure(bg='#505050'))
        return button
    
    def load_model(self):
        def load():
            try:
                self.whisper_model = whisper.load_model("turbo") 
                self.model_status.configure(text="✅ Model hazır", fg=self.colors['success'])
                self.update_status("Model başarıyla yüklendi")
            except Exception as e:
                self.model_status.configure(text="❌ Model hatası", fg=self.colors['error'])
                self.update_status(f"Model yükleme hatası: {str(e)}")
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def update_status(self, message):
        self.status_label.configure(text=message)
        self.root.update_idletasks()
    
    def select_file(self):
        if self.is_processing:
            messagebox.showwarning("Uyarı", "İşlem devam ediyor, lütfen bekleyin.")
            return
            
        file_path = filedialog.askopenfilename(
            title="Video Dosyası Seç",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All files", "*.*")]
        )
        if file_path:
            self.show_thumbnail(file_path)
            self.process_video(file_path)
    
    def process_video(self, video_path):
        if not self.whisper_model:
            messagebox.showerror("Hata", "Whisper modeli henüz yüklenmedi. Lütfen bekleyin.")
            return
        
        def process():
            audio_path = None
            try:
                self.is_processing = True
                
                # Adım 1: Ses çıkarma
                self.update_progress("🎵 Ses dosyası çıkarılıyor...", 20)
                
                import tempfile
                temp_dir = tempfile.gettempdir()
                # Dosya adını daha benzersiz hale getirelim
                base_name = os.path.basename(video_path)
                audio_filename = f"temp_audio_{os.path.splitext(base_name)[0]}.wav"
                audio_path = os.path.join(temp_dir, audio_filename)
                
                with AudioFileClip(video_path) as audio_clip:
                    audio_clip.write_audiofile(audio_path, logger=None, codec='pcm_s16le')
                
                if not os.path.exists(audio_path):
                    raise Exception("Ses dosyası oluşturulamadı")
                
                # Adım 2: Transkripsiyon başlangıcı
                self.update_progress("🤖 AI ile transkripsiyon yapılıyor...", 50)
                
                # fp16=False, çoğu CPU için daha kararlı çalışır.
                result = self.whisper_model.transcribe(audio_path, fp16=False)
                
                # Adım 3: Metin işleme
                self.update_progress("📝 Metinler işleniyor...", 80)
                
                segments = result.get('segments', [{'start': 0, 'end': 0, 'text': result.get('text', '')}])
                
                self.root.after(0, lambda: self.timecode_text.delete(1.0, END))
                self.root.after(0, lambda: self.clean_text.delete(1.0, END))
                
                # Adım 4: Sonuçları yazma
                self.update_progress("✍️ Sonuçlar hazırlanıyor...", 90)
                
                clean_transcript = ""
                
                for segment in segments:
                    start_time = self.format_time(segment.get('start', 0))
                    end_time = self.format_time(segment.get('end', 0))
                    text = segment.get('text', '').strip()
                    
                    if text:
                        timecoded_line = f"[{start_time} --> {end_time}] {text}\n"
                        self.root.after(0, self.timecode_text.insert, END, timecoded_line)
                        clean_transcript += text + " "
                
                if clean_transcript.strip():
                    self.root.after(0, self.clean_text.insert, END, clean_transcript.strip())
                
                # Tamamlandı
                self.update_progress("✅ Transkripsiyon tamamlandı!", 100)
                
            except Exception as e:
                error_msg = str(e)
                print(f"Detaylı hata: {error_msg}")
                self.update_progress(f"❌ Hata oluştu", 0) # Mesajı kısa tut
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Transkripsiyon sırasında hata oluştu:\n{error_msg}"))
            finally:
                self.is_processing = False
                # Geçici dosyayı güvenli şekilde sil
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except Exception as e_del:
                        print(f"Geçici ses dosyası silinemedi: {e_del}")
    
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def format_time(self, seconds):
        """Zamanı saat:dakika:saniye,milisaniye formatına dönüştürür."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"
    
    def delete_transcript(self, card_type):
        try:
            if card_type == "timecode":
                self.timecode_text.delete(1.0, END)
            else:
                self.clean_text.delete(1.0, END)
            self.update_status("🗑️ Transkript temizlendi")
        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {str(e)}")

    def copy_transcript(self, card_type):
        try:
            text = self.timecode_text.get(1.0, END).strip() if card_type == "timecode" else self.clean_text.get(1.0, END).strip()
            
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.update_status("📋 Transkript panoya kopyalandı")
            else:
                messagebox.showinfo("Bilgi", "Kopyalanacak transkript bulunamadı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Kopyalama hatası: {str(e)}")
    
    def save_transcript(self, card_type):
        try:
            if card_type == "timecode":
                text = self.timecode_text.get(1.0, END).strip()
                default_name = "zaman_kodlu_transkript.txt"
            else:
                text = self.clean_text.get(1.0, END).strip()
                default_name = "temiz_transkript.txt"
            
            if not text:
                messagebox.showinfo("Bilgi", "Kaydedilecek transkript bulunamadı.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=default_name
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.update_status(f"💾 Transkript kaydedildi: {os.path.basename(file_path)}")
        
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")


if __name__ == "__main__":
    root = Tk()
    app = ModernTranscriptionApp(root)
    root.mainloop()