import dlib
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import os
import time

# Ensure dataset directories exist
os.makedirs("dataset/deprived", exist_ok=True)
os.makedirs("dataset/normal", exist_ok=True)

# dlib face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Tkinter GUI setup
root = tk.Tk()
root.title("Face Landmark GUI")

label = tk.Label(root)
label.pack()

status_label = tk.Label(root, text="")
status_label.pack()

# Camera
cap = cv2.VideoCapture(0)

LATEST_FACE_PATH = os.path.join("dataset", "latest_face.jpg")

current_faces = []  # store latest detected faces

def predict_landmarks(gray_frame, rect):
    """Predict landmarks using dlib for a detected face rect (full-frame coords)."""
    shape = predictor(gray_frame, rect)
    return [(p.x, p.y) for p in shape.parts()]

def save_face(category):
    """Save the first detected face in the current frame."""
    if not current_faces:
        print("No face detected to save!")
        return
    face_img = current_faces[0]
    timestamp = int(time.time() * 1000)
    filename = f"dataset/{category}/{category}_{timestamp}.jpg"
    cv2.imwrite(filename, face_img)
    print(f"Saved face to {filename}")

def update_frame():
    global current_faces
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 1)

    status_label.configure(text="No face detected" if len(rects) == 0 else "")

    current_faces = []  # reset each frame
    h_frame, w_frame = frame.shape[:2]
    for rect in rects:
        x1 = max(0, rect.left())
        y1 = max(0, rect.top())
        x2 = min(w_frame, rect.right())
        y2 = min(h_frame, rect.bottom())

        if x2 <= x1 or y2 <= y1:
            continue

        # Copy the crop so drawing landmarks on `frame` doesn't modify what we save.
        face_img = frame[y1:y2, x1:x2].copy()
        current_faces.append(face_img)

        # Save/overwrite a single "latest face" image when a face is detected.
        try:
            cv2.imwrite(LATEST_FACE_PATH, face_img)
        except Exception:
            pass

        try:
            landmarks = predict_landmarks(gray, rect)
            for (lx, ly) in landmarks:
                cv2.circle(frame, (int(lx), int(ly)), 2, (0, 255, 0), -1)
        except Exception as e:
            print(f"Prediction error: {e}")
            pass

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    label.imgtk = imgtk
    label.configure(image=imgtk)

    root.after(10, update_frame)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

deprived_btn = tk.Button(btn_frame, text="Deprived", command=lambda: save_face("deprived"), bg="red", fg="white")
deprived_btn.pack(side=tk.LEFT, padx=5)

normal_btn = tk.Button(btn_frame, text="Normal", command=lambda: save_face("normal"), bg="green", fg="white")
normal_btn.pack(side=tk.LEFT, padx=5)

update_frame()
root.mainloop()

cap.release()