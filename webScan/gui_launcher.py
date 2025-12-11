
import subprocess
import threading
import sys
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCAN_PATH = os.path.join(CURRENT_DIR, "scan.py")

scan_process = None


root = tk.Tk()
root.title("FaceBox Starter")
root.geometry("700x500")
root.configure(bg="#f0f4f8")
root.resizable(False, False)


log_box = scrolledtext.ScrolledText(root, width=85, height=20, bg="#ffffff", fg="#333333",
                                    font=("Segoe UI", 10), state=tk.DISABLED, wrap=tk.WORD)
log_box.pack(pady=15, padx=15)

def log(message):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    log_box.config(state=tk.DISABLED)


def read_output():
    global scan_process
    for line in scan_process.stdout:
        log(line.rstrip())


def start_scan():
    global scan_process
    if scan_process is None:
        log("🔹 scan.py başlatılıyor...")
        try:
            scan_process = subprocess.Popen(
                [sys.executable, SCAN_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            threading.Thread(target=read_output, daemon=True).start()
            log("✅ scan.py çalışıyor.")
        except Exception as e:
            log(f"❌ Başlatılamadı: {e}")
            scan_process = None
    else:
        log("⚠️ scan.py zaten çalışıyor.")

def stop_scan():
    global scan_process
    if scan_process is not None:
        scan_process.terminate()
        scan_process = None
        log("🛑 scan.py durduruldu.")
    else:
        log("⚠️ scan.py çalışmıyor.")


button_frame = tk.Frame(root, bg="#f0f4f8")
button_frame.pack(pady=10)

start_btn = tk.Button(button_frame, text="Başlat", command=start_scan,
                      bg="#4CAF50", fg="white", font=("Segoe UI", 12), width=12)
start_btn.pack(side=tk.LEFT, padx=10)

stop_btn = tk.Button(button_frame, text="Durdur", command=stop_scan,
                     bg="#F44336", fg="white", font=("Segoe UI", 12), width=12)
stop_btn.pack(side=tk.LEFT, padx=10)

exit_btn = tk.Button(button_frame, text="Çıkış", command=lambda: root.destroy(),
                     bg="#607D8B", fg="white", font=("Segoe UI", 12), width=12)
exit_btn.pack(side=tk.LEFT, padx=10)


root.mainloop()
