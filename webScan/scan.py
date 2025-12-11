# scan.py (sabitlenmiş yaş aralığı ve yumuşatılmış cinsiyet)
import os
import cv2
import numpy as np
import base64
from flask import Flask, request, jsonify, send_from_directory
from deepface import DeepFace
from datetime import datetime
import qrcode
import subprocess
import time
import requests
import webbrowser
import json

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

NGROK_PATH = r"C:\ngrok\ngrok.exe"
NGROK_PORT = 5000

# --- Yüz cache: her yüz için ilk yaş aralığı ve cinsiyet geçmişi ---
face_cache = {}  # key: yüz indeksi, value: {"first_age_range": str, "genders": [..]}

# --- Yaş aralıkları ---
def map_age_to_range(age):
    try:
        age = float(age)
    except:
        return "Bilinmiyor"
    if age <= 3: return "0-3"
    elif age <= 9: return "3-9"
    elif age <= 15: return "9-15"
    elif age <= 25: return "15-25"
    elif age <= 35: return "25-35"
    elif age <= 45: return "35-45"
    elif age <= 55: return "45-55"
    elif age <= 65: return "55-65"
    else: return "65+"

# --- NumPy tipleri için güvenli json.dumps ---
def np_serializer(obj):
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    try:
        return str(obj)
    except:
        return None

# --- Ngrok başlat ---
def start_ngrok():
    try:
        ngrok_process = subprocess.Popen([NGROK_PATH, "http", str(NGROK_PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None, None
    time.sleep(3)
    try:
        tunnels = requests.get("http://127.0.0.1:4040/api/tunnels").json().get('tunnels', [])
        for t in tunnels:
            if t.get('proto') == 'http':
                return t.get('public_url'), ngrok_process
    except Exception:
        return None, ngrok_process
    return None, ngrok_process

# --- QR kod oluştur ---
def generate_qr(url):
    qr_img = qrcode.make(url)
    qr_path = os.path.join(DOWNLOAD_DIR, "qr_code.png")
    qr_img.save(qr_path)
    print(f"QR kod oluşturuldu: {qr_path}")
    return qr_path

# --- Flask Routes ---
@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "index.html")

@app.route("/scan", methods=["POST"])
def scan():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"error": "No image data"}), 400

        img_data = data['image'].split(",")[1]
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({"error": "Image not valid"}), 400

        analysis = DeepFace.analyze(img, actions=['age','gender'], enforce_detection=False)

        # Normalize DeepFace çıktısı
        if isinstance(analysis, dict):
            if "instance_1" in analysis and isinstance(analysis["instance_1"], dict):
                analysis_list = [analysis["instance_1"]]
            elif "age" in analysis:
                analysis_list = [analysis]
            elif isinstance(list(analysis.values())[0], dict):
                analysis_list = list(analysis.values())
            else:
                analysis_list = [analysis]
        elif isinstance(analysis, list):
            analysis_list = analysis
        else:
            return jsonify({"error": "DeepFace output format unknown"}), 500

        results = []
        faces_count = len(analysis_list)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for idx, face in enumerate(analysis_list):
            age = None
            gender = None

            if isinstance(face, dict):
                age = face.get("age") or face.get("dominant_age") or 0.0
                gender = face.get("gender")

                # Eğer dict içinde dict varsa orada ara
                for k, v in face.items():
                    if isinstance(v, dict):
                        if age is None and "age" in v: age = v.get("age")
                        if gender is None and "gender" in v: gender = v.get("gender")

            try:
                age = float(age)
            except:
                age = 0.0

            if isinstance(gender, dict):
                try:
                    gender = max(gender, key=gender.get)
                except:
                    gender = "unknown"
            gender = str(gender).lower() if gender else "unknown"
            if "man" in gender or "male" in gender:
                gender_text = "Erkek"
            elif "woman" in gender or "female" in gender:
                gender_text = "Kadın"
            else:
                gender_text = "Bilinmiyor"

            # --- Face cache ---
            if idx not in face_cache:
                face_cache[idx] = {"first_age_range": None, "genders": []}

            # İlk yaş aralığını sabitle
            if face_cache[idx]["first_age_range"] is None:
                face_cache[idx]["first_age_range"] = map_age_to_range(age)
            age_range = face_cache[idx]["first_age_range"]

            # Cinsiyeti yumuşatma (son 5 değeri kullan)
            face_cache[idx]["genders"].append(gender_text)
            if len(face_cache[idx]["genders"]) > 5:
                face_cache[idx]["genders"].pop(0)
            smooth_gender = max(set(face_cache[idx]["genders"]), key=face_cache[idx]["genders"].count)

            # TXT kaydet
            txt_filename = f"face_{idx+1}_{timestamp}.txt"
            txt_path = os.path.join(DOWNLOAD_DIR, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Face {idx+1}\n")
                f.write(f"Age Range: {age_range}\n")
                f.write(f"Gender: {smooth_gender}\n")

            # Görsel üzerine yaz
            region = face.get("region", {}) if isinstance(face, dict) else {}
            x, y, w, h = int(region.get("x", 0)), int(region.get("y", 0)), int(region.get("w", 0)), int(region.get("h", 0))
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, f"{age_range} - {smooth_gender}", (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            results.append({
                "face": idx + 1,
                "age_range": age_range,
                "gender": smooth_gender,
                "txt_file": txt_filename
            })

        img_filename = f"faces_{timestamp}.png"
        cv2.imwrite(os.path.join(DOWNLOAD_DIR, img_filename), img)

        return jsonify({
            "faces_count": faces_count,
            "results": results,
            "image_file": img_filename
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)


# --- Main ---
if __name__ == "__main__":
    ngrok_url, ngrok_process = start_ngrok()
    if ngrok_url:
        generate_qr(ngrok_url)
        print(f"✅ Ngrok URL: {ngrok_url}")
        try: webbrowser.open(ngrok_url)
        except: pass
    else:
        local_url = f"http://127.0.0.1:{NGROK_PORT}"
        print(f"🌐 Lokal olarak {local_url} üzerinden erişim sağlanabilir.")
        try: webbrowser.open(local_url)
        except: pass

    app.run(host="0.0.0.0", port=NGROK_PORT)
    if ngrok_process:
        try: ngrok_process.terminate()
        except: pass
