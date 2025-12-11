import subprocess
import threading
import sys
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window


# Arka plan koyu ton — loglar beyaz
Window.clearcolor = (0.1, 0.1, 0.1, 1)
Window.softinput_mode = "pan"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCAN_PATH = os.path.join(CURRENT_DIR, "scan.py")

scan_process = None


class LogView(ScrollView):
    """Log alanı - scan.py çıktısını gösterir"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(
            size_hint_y=None,
            text='',
            halign='left',
            valign='top',
            font_size='16sp',
            color=(1, 1, 1, 1)  # beyaz yazı
        )
        self.label.bind(texture_size=self._update_height)
        self.add_widget(self.label)

    def _update_height(self, instance, size):
        self.label.height = size[1]
        self.label.text_size = (self.width * 0.95, None)

    def log(self, message):
        self.label.text += message + "\n"
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0))


class FaceBoxUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

        # Log ekranı
        self.log_box = LogView(size_hint=(1, 0.85))
        self.add_widget(self.log_box)

        # Butonlar
        button_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)

        start_btn = Button(
            text="Başlat",
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),  # beyaz yazı
            font_size='18sp'
        )
        start_btn.bind(on_press=lambda x: self.start_scan())

        stop_btn = Button(
            text="Durdur",
            background_color=(0.9, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),  # beyaz yazı
            font_size='18sp'
        )
        stop_btn.bind(on_press=lambda x: self.stop_scan())

        exit_btn = Button(
            text="Çıkış",
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),  # beyaz yazı
            font_size='18sp'
        )
        exit_btn.bind(on_press=lambda x: self.stop_and_exit())

        button_layout.add_widget(start_btn)
        button_layout.add_widget(stop_btn)
        button_layout.add_widget(exit_btn)

        self.add_widget(button_layout)

    def log(self, message):
        Clock.schedule_once(lambda dt: self.log_box.log(message))

    def read_output(self):
        global scan_process
        for line in scan_process.stdout:
            self.log(line.rstrip())

    def start_scan(self):
        global scan_process
        if scan_process is None:
            self.log("🔹 scan.py başlatılıyor...")
            try:
                scan_process = subprocess.Popen(
                    [sys.executable, SCAN_PATH],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                threading.Thread(target=self.read_output, daemon=True).start()
                self.log("✅ scan.py çalışıyor.")
            except Exception as e:
                self.log(f"❌ Başlatılamadı: {e}")
                scan_process = None
        else:
            self.log("⚠️ scan.py zaten çalışıyor.")

    def stop_scan(self):
        global scan_process
        if scan_process is not None:
            scan_process.terminate()
            scan_process = None
            self.log("🛑 scan.py durduruldu.")
        else:
            self.log("⚠️ scan.py çalışmıyor.")

    def stop_and_exit(self):
        self.stop_scan()
        App.get_running_app().stop()


class FaceBoxApp(App):
    def build(self):
        self.title = "FaceBox Starter"
        return FaceBoxUI()


if __name__ == "__main__":
    FaceBoxApp().run()
