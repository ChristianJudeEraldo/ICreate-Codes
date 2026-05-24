import json 
import threading
import time
from datetime import datetime, timezone
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
from ultralytics import YOLO
from sleepy_classifier import SleepyClassifier

# --- FIREBASE IMPORTS ---
import firebase_admin
from firebase_admin import credentials, firestore
import base64

SerialData = init_serial()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SET_PAGE_PATH = os.path.join(BASE_DIR, 'set_page.txt')

# --- DATASET FOLDERS INITIALIZATION ---
DATASET_DIR = os.path.join(BASE_DIR, 'captured_dataset')
os.makedirs(os.path.join(DATASET_DIR, 'sleepy'), exist_ok=True)
os.makedirs(os.path.join(DATASET_DIR, 'alert'), exist_ok=True)

# --- REGISTERED STUDENTS LOCAL DATABASE ARCHITECTURE ---
REGISTERED_STUDENTS_FILE = os.path.join(BASE_DIR, 'registered_students.json')

def get_registered_ids():
    """Reads the local JSON file and returns a list of valid IDs in less than 1ms."""
    try:
        if os.path.exists(REGISTERED_STUDENTS_FILE):
            with open(REGISTERED_STUDENTS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading registered IDs: {e}")
    return [] 


def _doc_timestamp_to_local_date(value):
    if not isinstance(value, datetime):
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone().date().isoformat()


def student_scanned_today(student_id, scan_date):
    """Checks whether the student already has a scan record for the current local day."""
    try:
        docs = db.collection('sleep_logs').where('student_id', '==', student_id).stream()

        for doc in docs:
            scan_data = doc.to_dict() or {}
            if scan_data.get('scan_date') == scan_date:
                return True

            timestamp_date = _doc_timestamp_to_local_date(scan_data.get('timestamp'))
            if timestamp_date == scan_date:
                return True
    except Exception as e:
        print(f"Error checking existing scan records: {e}")

    return False

# --- INITIALIZE FIRESTORE ---
try:
    #serviceAccountKey.json should be on the same directory as main.py
    cred = credentials.Certificate(os.path.join(BASE_DIR, "serviceAccountKey.json"))
    firebase_admin.initialize_app(cred) 
    db = firestore.client()
    print("Firebase connected successfully!")
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")

# --- EDGE-TO-CLOUD SYNCHRONIZATION FUNCTION ---
def sync_registered_students_from_cloud():
    """Downloads the master list of IDs from Firebase and caches it locally on the Pi."""
    print("Initiating Cloud Sync: Downloading registered student IDs...")
    try:
        
        users_ref = db.collection('students') 
        docs = users_ref.stream()

        valid_ids = []
        for doc in docs:
            student_data = doc.to_dict()
            # Grabs the 'student_id' field
            student_id = student_data.get('studentId', doc.id) 
            
            if student_id:
                valid_ids.append(str(student_id).strip())

        # Overwrite the local JSON file with the fresh data from Firebase
        with open(REGISTERED_STUDENTS_FILE, 'w') as f:
            json.dump(valid_ids, f, indent=4)
            
        print(f"Cloud Sync Complete: Successfully updated local database with {len(valid_ids)} students.")
        
    except Exception as e:
        print(f"Cloud Sync Failed: {e}")
        print("System will fallback to the last known local JSON database.")


cap = cv2.VideoCapture(0)  # Open the default camera

VIDEO_STREAM_FPS = 10
VIDEO_STREAM_MAX_WIDTH = 640
VIDEO_STREAM_ENABLED = False

classifier = SleepyClassifier(model_path="yolov11_n.pt", image_size=224)
custom_model = YOLO("yolov11_n.pt")


# --- Global thresholds / feature flags ---
REQUIRED_DISTANCE_CM_MAX = 23.0
REQUIRED_TEMPERATURE_C_MIN = 20

USE_DLIB_EAR = False
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
            eel.goToPage("page0.html")
            print("Initialized")
            break
        except Exception:
            print("Eel not ready, initializing...")
            time.sleep(0.5)

    # --- cloud sync exactly when the kiosk boots up ---
    sync_registered_students_from_cloud()

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
def start_scan(student_id, sleep_hours):
    global StudentID
    # --- to prevent accidental mismatches ---
    StudentID = student_id.strip() 
    scan_date = datetime.now().astimezone().date().isoformat()
    
    # 1. Existing Check: Is the input completely empty?
    if StudentID == "":
        eel.openWarningDialog(
            "Student ID Error",
            "Student ID cannot be empty. Please enter a valid ID to proceed.",
            [],
            {"outsideClickClose": True, "autoCloseMs": 0},
        )()
        return {"success": False, "error": "Invalid student ID"}
    
    # Edge Validation Check: check if regisstered in the local JSON database 
    valid_ids = get_registered_ids()
    if StudentID not in valid_ids:
        print(f"Blocked unauthorized scan attempt for ID: {StudentID}")
        eel.openWarningDialog(
            "Unregistered ID",
            f"Student ID {StudentID} is not registered in the system. Please visit the clinic to register your emergency contact.",
            [],
            {"outsideClickClose": True, "autoCloseMs": 0},
        )()
        return {"success": False, "error": "Unregistered student ID"}

    if student_scanned_today(StudentID, scan_date):
        print(f"Blocked duplicate scan attempt for ID: {StudentID} on {scan_date}")
        eel.openWarningDialog(
            "Daily Scan Limit Reached",
            f"Student ID {StudentID} already has a scan record for today. You can scan again tomorrow.",
            [],
            {"outsideClickClose": True, "autoCloseMs": 0},
        )()
        return {"success": False, "error": "Student already scanned today"}
    
    # --- If it passes both checks, start the scan! ---
    print(f"Start scan requested for student ID: {StudentID} | Self-reported sleep: {sleep_hours} hours")

    Create_White_Screen("frontend/assets/img/video.png", 640, 480)
    time.sleep(1)
    eel.showElement("page1-video")

    def delayed_nav():
        eel.showElement("page1-timer")
        for i in range(5):
            eel.updateElementByAttribute("page1-timer", 'innerHTML', str(5 - i))
            time.sleep(1)

        # --- Sensor check ---
        try:
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

            # Parse response (format: maxTemp_dist)
            temp, dist = parseParams(response)

            if dist <= 9.0:
                eel.updateElementByAttribute("page1-timer", 'innerHTML', "No face detected. Try again")
                print(f"Anti-spoofing triggered: Distance detected at {dist}cm.")
                return
            
            if temp is None or dist is None:
                eel.updateElementByAttribute("page1-timer", 'innerHTML', "Sensor error. Try again.")
                return

            print("Distance:", dist, "cm")
            print("Temperature:", temp, "C")
            
            # Check conditions
            if dist < REQUIRED_DISTANCE_CM_MAX and temp > REQUIRED_TEMPERATURE_C_MIN:
                # Face crop + YOLO classification before navigating
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

                if frame2 is None or face_crop is None:
                    eel.updateElementByAttribute("page1-timer", 'innerHTML', "Detection error. Try again")
                    return

                try:
                    cv2.imwrite("frontend/assets/img/face.png", face_crop)
                except Exception:
                    pass

                # --- ULTRALYTICS YOLO CLASSIFICATION ---
                label = "unknown"
                confidence = 0
                
                try:
                    yolo_results = custom_model.predict(source=frame2, verbose=False)
                    if len(yolo_results[0].boxes) > 0:
                        best_box = yolo_results[0].boxes[0]
                        class_id = int(best_box.cls[0])
                        label = custom_model.names[class_id] 
                        confidence = int(best_box.conf[0] * 100)
                except Exception as e:
                    print(f"YOLO error: {e}")

                # --- RULING LOGIC ---
                is_deprived = False
                is_normal = False

                if USE_DLIB_EAR:
                    ear = None
                    try:
                        if hasattr(classifier, "get_landmarks_68_from_face_bgr"):
                            landmarks = classifier.get_landmarks_68_from_face_bgr(face_crop)
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
                        confidence = max(0, min(100, confidence))
                    else:
                        confidence = random.randint(60, 100)
                else:
                    label_norm = str(label).strip().lower().replace(" ", "")

                    # "Deprivation Level" (0-100%)
                    if label_norm in {"active", "wellrested", "normal"}:
                        # If YOLO is 80% sure they are rested, they are 20% deprived.
                        fatigue_score = 100 - confidence 
                    else:
                        # If YOLO says sleepy, the confidence IS the fatigue score.
                        fatigue_score = confidence
                    
                    # --- SYSTEM 70% THRESHOLD ---
                    CONFIDENCE_THRESHOLD = 70 
                    
                    if fatigue_score >= CONFIDENCE_THRESHOLD:
                        is_deprived = True
                        is_normal = False
                    else:
                        is_deprived = False
                        is_normal = True
                        if label_norm in {"fatigue", "sleepy"}:
                            print(f"Threshold Override: Deprivation score ({fatigue_score}%) < {CONFIDENCE_THRESHOLD}%. Defaulting to Normal.")
                     
                    # only receive the unified Fatigue Score.
                    confidence = fatigue_score
            
                try:
                    target_folder = "sleepy" if is_deprived else "alert"
                    timestamp = int(time.time())
                    img_filename = f"{StudentID}_{timestamp}.png"
                    dataset_path = os.path.join(DATASET_DIR, target_folder, img_filename)
                    cv2.imwrite(dataset_path, face_crop)
                    print(f"Captured face saved to local dataset: {dataset_path}")
                except Exception as e:
                    print(f"Local save error: {e}")

                # UI Update and Navigation
                eel.goToPage("page2.html")
                eel.updateElementByAttribute("page2-student-id", 'innerHTML', StudentID)
                eel.updateElementByAttribute("page2-face", 'src', "assets/img/face.png")

                if is_deprived and not is_normal:
                    result_text = "Signs of sleep deprivation detected"
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
                    eel.updateElementByAttribute("page2-confidence", 'innerHTML', f"{confidence}%")
                else:
                    eel.updateElementByAttribute("page2-confidence", 'innerHTML', "Confidence: N/A")
                    
                # BASE64 UPLOAD TO FIRESTORE
                try:
                    success, buffer = cv2.imencode('.jpg', face_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if success:
                        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                        base64_string = f"data:image/jpeg;base64,{jpg_as_text}"
                        
                        # Clean up the sleep_hours just in case it comes as a string
                        safe_sleep_hours = int(sleep_hours) if str(sleep_hours).isdigit() else 0

                        db.collection('sleep_logs').add({
                            'student_id': StudentID,
                            'status': "Deprived" if is_deprived else "Normal",
                            'confidence': confidence if confidence is not None else 0,
                            'imageUrl': base64_string,
                            'self_reported_sleep_hours': safe_sleep_hours,
                            'scan_date': scan_date,
                            'timestamp': firestore.SERVER_TIMESTAMP
                        })
                except Exception as e:
                    print(f"Error uploading to Firebase: {e}")
            else:
                eel.updateElementByAttribute("page1-timer", 'innerHTML', "Move closer and try again")
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
