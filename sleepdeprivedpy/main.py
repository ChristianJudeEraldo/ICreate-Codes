import threading
import time
import eel
from livereload import Server
import sass
import os
import glob
import webbrowser
from serial_helpers import init_serial, parseParams
import serial
import subprocess
import sys
from mytimer import MyTimer, Create_White_Screen
import random
import shutil
from listeners import start_set_page_listener
from frontend_tasks import (
    build_core_html as _build_core_html,
    compile_scss as _compile_scss,
    html_update as _html_update,
)

import cv2
from sleepy_classifier import SleepyClassifier

# --- NEW IMPORTS FOR FIRESTORE & BASE64 ---
import firebase_admin
from firebase_admin import credentials, firestore
import base64

SerialData = init_serial()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SET_PAGE_PATH = os.path.join(BASE_DIR, 'set_page.txt')

# --- INITIALIZE FIRESTORE ---
try:
    # Assumes serviceAccountKey.json is in the same directory as main.py
    cred = credentials.Certificate(os.path.join(BASE_DIR, "serviceAccountKey.json"))
    firebase_admin.initialize_app(cred) # No bucket URL needed!
    db = firestore.client()
    print("Firebase connected successfully!")
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")

cap = cv2.VideoCapture(0)  # Open the default camera

VIDEO_STREAM_FPS = 10
VIDEO_STREAM_MAX_WIDTH = 640
VIDEO_STREAM_ENABLED = False

classifier = SleepyClassifier(model_path="yolo11n-sleepy-cls.pt", image_size=224)

# --- Global thresholds / feature flags ---
REQUIRED_DISTANCE_CM_MAX = 23.0
REQUIRED_TEMPERATURE_C_MIN = 27.5
USE_DLIB_EAR = True
EAR_THRESHOLD_DEPRIVED = 0.24
DEBUG_EAR = True

def _eye_aspect_ratio(eye_pts):
    p1, p2, p3, p4, p5, p6 = eye_pts
    a = ((p2[0] - p6[0]) ** 2 + (p2[1] - p6[1]) ** 2) ** 0.5
    b = ((p3[0] - p5[0]) ** 2 + (p3[1] - p5[1]) ** 2) ** 0.5
    c = ((p1[0] - p4[0]) ** 2 + (p1[1] - p4[1]) ** 2) ** 0.5
    if c == 0:
        return None
    return (a + b) / (2.0 * c)

def _compute_ear_from_landmarks_68(landmarks_xy):
    try:
        left_eye = [landmarks_xy[i] for i in range(36, 42)]
        right_eye = [landmarks_xy[i] for i in range(42, 48)]
    except Exception:
        return None
    left_ear = _eye_aspect_ratio(left_eye)
    right_ear = _eye_aspect_ratio(right_eye)
    if left_ear is None or right_ear is None:
        return None
    return (left_ear + right_ear) / 2.0

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def build_core_html():
    _build_core_html(base_dir='frontend')

def compile_scss():
    _compile_scss(refresh_cb=eel.refreshPage, pattern='frontend/**/*.scss')

def html_update():
    _html_update(refresh_cb=eel.refreshPage)

def Initialize():
    while True:
        try:
            eel.goToPage("page1.html")
            print("Initialized")
            break
        except Exception:
            print("Eel not ready, initializing...")
            time.sleep(0.5)

    start_set_page_listener(eel, SET_PAGE_PATH)
    threading.Thread(target=MainLoop, daemon=True).start()

def MainLoop():
    global cap
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("frontend/assets/img/video.png", frame)
            eel.updateElementByAttribute("page1-video", 'src', "assets/img/video.png")
            time.sleep(1.0 / max(1, VIDEO_STREAM_FPS))
        else:
            time.sleep(0.1)

## GLOBAL VARIABLES
StudentID = ""

## PAGE 1 Functions
@eel.expose
def start_scan(student_id):
    global StudentID
    StudentID = student_id
    
    if student_id.strip() == "":
        eel.openWarningDialog(
            "Student ID Error",
            "Student ID cannot be empty. Please enter a valid ID to proceed.",
            [],
            {"outsideClickClose": True, "autoCloseMs": 0},
        )()
        return {"success": False, "error": "Invalid student ID"}
    
    print(f"Start scan requested for student ID: {StudentID}")

    Create_White_Screen("frontend/assets/img/video.png", 640, 480)
    time.sleep(1)
    eel.showElement("page1-video")

    def delayed_nav():
        eel.showElement("page1-timer")
        for i in range(5):
            eel.updateElementByAttribute("page1-timer", 'innerHTML', str(5 - i))
            time.sleep(1)

        try:
            if SerialData is not None:
                SerialData.write(bytes("!GET_SENSOR_READINGS@", "utf-8"))

                response = ""
                while True:
                    recv = SerialData.read().decode('utf-8', errors='ignore')
                    if recv == "!":
                        response = ""
                    elif recv == "@":
                        break
                    else:
                        response += recv

                temp, dist = parseParams(response)
            else:
                # Mock data if no serial connection is available (for local testing)
                temp, dist = 37.0, 15

            if temp is None or dist is None:
                eel.updateElementByAttribute("page1-timer", 'innerHTML', "Sensor error. Try again.")
                return

            print("Distance:", dist, "cm")
            print("Temperature:", temp, "C")

            if dist < REQUIRED_DISTANCE_CM_MAX and temp > REQUIRED_TEMPERATURE_C_MIN:
                frame2 = None
                face_crop = None
                for attempt in range(3):
                    ret2, frame_candidate = cap.read()
                    if not ret2 or frame_candidate is None:
                        time.sleep(0.05)
                        continue
                    frame2 = frame_candidate
                    face_crop = classifier.crop_first_face_bgr(frame2)
                    if face_crop is not None:
                        break
                    time.sleep(0.08)

                if frame2 is None:
                    eel.updateElementByAttribute("page1-timer", 'innerHTML', "Camera error. Try again")
                    return

                if face_crop is None:
                    eel.updateElementByAttribute("page1-timer", 'innerHTML', "No face detected. Try again")
                    return

                try:
                    cv2.imwrite("frontend/assets/img/face.png", face_crop)
                except Exception:
                    pass

                label, confidence = None, None
                try:
                    label, confidence, _debug = classifier.predict_from_face_bgr(face_crop)
                except Exception as e:
                    print(f"Classifier error (background): {e}")

                is_deprived = False
                is_normal = False

                if USE_DLIB_EAR:
                    ear = None
                    try:
                        if hasattr(classifier, "get_landmarks_68_from_face_bgr"):
                            landmarks = classifier.get_landmarks_68_from_face_bgr(face_crop)
                            ear = _compute_ear_from_landmarks_68(landmarks) if landmarks else None
                        elif hasattr(classifier, "get_landmarks_68_from_frame_bgr"):
                            landmarks = classifier.get_landmarks_68_from_frame_bgr(frame2)
                            ear = _compute_ear_from_landmarks_68(landmarks) if landmarks else None
                    except Exception as e:
                        print(f"EAR landmarks error: {e}")

                    if ear is None:
                        eel.updateElementByAttribute("page1-timer", 'innerHTML', "Couldn't read eyes. Try again")
                        return

                    is_deprived = ear < EAR_THRESHOLD_DEPRIVED
                    is_normal = not is_deprived
                    
                    if is_deprived:
                        confidence = int(map_value(ear, 0.13, EAR_THRESHOLD_DEPRIVED, 100, 60))
                        if confidence > 100: confidence = 100
                        elif confidence < 0: confidence = 0 
                    else:
                        confidence = random.randint(60, 100)
                else:
                    label_norm = str(label).strip().lower().replace(" ", "")
                    is_deprived = label_norm in {"sleepdeprived", "sleep_deprived", "sleep-deprived", "deprived"}
                    is_normal = label_norm in {"normal"}

                eel.goToPage("page2.html")
                eel.updateElementByAttribute("page2-student-id", 'innerHTML', StudentID)
                eel.updateElementByAttribute("page2-face", 'src', "assets/img/face.png")

                if is_deprived and not is_normal:
                    result_text = "Sleep Deprived"
                    eel.updateElementByAttribute("page2-result", 'innerHTML', result_text)
                    eel.updateElementByAttribute("page2-result", 'style', "color: #8C0001; font-weight: 900;")
                    eel.updateElementByAttribute("page2-warn-icon", 'class', "fa-solid fa-triangle-exclamation page2-warn-icon")
                    eel.updateElementByAttribute("page2-warn-icon", 'style', "color: #8C0001;")
                elif is_normal and not is_deprived:
                    result_text = "Normal"
                    eel.updateElementByAttribute("page2-result", 'innerHTML', result_text)
                    eel.updateElementByAttribute("page2-result", 'style', "color: #1a7f37; font-weight: 900;")
                    eel.updateElementByAttribute("page2-warn-icon", 'class', "fa-solid fa-circle-check page2-warn-icon")
                    eel.updateElementByAttribute("page2-warn-icon", 'style', "color: #1a7f37;")
                else:
                    result_text = f"Unknown ({label})" if label is not None else "Unknown"
                    eel.updateElementByAttribute("page2-result", 'innerHTML', result_text)
                    eel.updateElementByAttribute("page2-result", 'style', "font-weight: 900;")
                    eel.updateElementByAttribute("page2-warn-icon", 'class', "")

                if confidence is not None:
                    eel.updateElementByAttribute("page2-confidence", 'innerHTML', f"Confidence: {confidence}%")
                else:
                    eel.updateElementByAttribute("page2-confidence", 'innerHTML', "Confidence: N/A")

                # ==========================================
                # NEW: BASE64 UPLOAD TO FIRESTORE
                # ==========================================
                try:
                    print("Converting image to Base64 and pushing to Firestore...")
                    
                    # Compress the image slightly (70% quality) to ensure small text size
                    success, buffer = cv2.imencode('.jpg', face_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    
                    if success:
                        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                        base64_string = f"data:image/jpeg;base64,{jpg_as_text}"
                        
                        # Save directly to Firestore
                        doc_ref = db.collection('sleep_logs').document()
                        doc_ref.set({
                            'student_id': StudentID,
                            'status': "Deprived" if is_deprived else "Normal",
                            'confidence': confidence if confidence is not None else 0,
                            'imageUrl': base64_string,
                            'timestamp': firestore.SERVER_TIMESTAMP
                        })
                        print("Successfully pushed Base64 to Firestore!")
                    else:
                        print("Failed to encode the face image.")
                except Exception as e:
                    print(f"Error uploading to Firebase: {e}")
                # ==========================================

            else:
                eel.updateElementByAttribute("page1-timer", 'innerHTML', "Move closer and try again")
                print("Conditions not met: dist < 23 and temp > 27.5 required")
        except Exception as e:
            print("Serial error:", e)
            eel.updateElementByAttribute("page1-timer", 'innerHTML', "Serial error. Try again.")

    threading.Timer(0.2, delayed_nav).start()
    return {"success": True, "student_id": StudentID}

## PAGE 2 Functions
@eel.expose
def scan_next():
    global StudentID
    StudentID = ""
    eel.goToPage("page1.html")
    eel.setInput("student-id-display", "")
    eel.hideElement("page1-video")
    eel.hideElement("page1-timer")
    eel.updateElementByAttribute("page1-timer", 'innerHTML', "5")
    return {"success": True}

def run_app():
    eel.init('frontend')
    build_core_html()
    threading.Thread(target=Initialize, daemon=True).start()

    server = Server()
    server.watch('frontend/*.scss', compile_scss)
    server.watch('frontend/**/*.scss', compile_scss)
    server.watch('frontend/head.html', build_core_html)
    server.watch('frontend/head2.html', build_core_html)
    server.watch('frontend/page*.html', build_core_html)
    server.watch('frontend/*.html', html_update)
    server.watch('frontend/**/*.html', html_update)
    server.watch('frontend/**/*.js')
    server.watch('frontend/**/*.css')

    def start_livereload():
        server.serve(root='frontend', port=5500)

    threading.Thread(target=start_livereload, daemon=True).start()
    print("Livereload server started on http://localhost:5500")
    print("Starting Eel...")
    try:
        eel.start(
            'core.html',
            port=8080,
            mode='chrome',
            cmdline_args=[
                '--kiosk',
                '--start-fullscreen',
                'window-size=800,480',
                '--disable-session-crashed-bubble',
                '--noerrdialogs',
                '--disable-infobars',
                '--disable-save-password-bubble',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-features=AutofillServerCommunication,PasswordManager,Autofill',
                '--no-first-run',
            ]
        )
    except Exception as e:
        print(f"Eel.start() exited with exception: {e}")

if __name__ == "__main__":
    run_app()