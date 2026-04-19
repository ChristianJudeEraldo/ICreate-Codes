import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import os
import time

# Create dataset folders
os.makedirs("dataset/deprived", exist_ok=True)
os.makedirs("dataset/normal", exist_ok=True)

# MediaPipe setup
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(min_detection_confidence=0.6)

# Camera
cap = cv2.VideoCapture(0)

# Tkinter window
root = tk.Tk()
root.title("Face Capture GUI")

# Canvas for video
label = tk.Label(root)
label.pack()

# Store latest face
latest_face = None

def save_face(folder):
    global latest_face
    if latest_face is not None:
        filename = f"{folder}/face_{int(time.time())}.jpg"
        cv2.imwrite(filename, latest_face)
        print(f"Saved: {filename}")

def save_deprived():
    save_face("dataset/deprived")

def save_normal():
    save_face("dataset/normal")

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack()

btn_deprived = tk.Button(btn_frame, text="Deprived", command=save_deprived, bg="red", fg="white")
btn_deprived.pack(side=tk.LEFT, padx=10)

btn_normal = tk.Button(btn_frame, text="Normal", command=save_normal, bg="green", fg="white")
btn_normal.pack(side=tk.LEFT, padx=10)

def update_frame():
    global latest_face

    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    # Resize for performance (important on Pi)
    frame = cv2.resize(frame, (640, 480))

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb)

    latest_face = None

    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box

            h, w, _ = frame.shape
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)

            # Draw green box
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)

            # Crop face safely
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w, x + bw)
            y2 = min(h, y + bh)

            face_crop = frame[y1:y2, x1:x2]

            if face_crop.size > 0:
                latest_face = face_crop

    # Convert to Tkinter image
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)

    label.imgtk = imgtk
    label.configure(image=imgtk)

    root.after(10, update_frame)

# Start loop
update_frame()
root.mainloop()

# Release camera
cap.release()
