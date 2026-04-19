#!/usr/bin/env python3
"""
This script creates and installs the rpiproject module for your Raspberry Pi.
Run it directly:
    chmod +x rpiproject.sh
    ./rpiproject.sh
"""

import os

# --- 1. Create folder structure ---
base_dir = "rpiproject"
package_dir = os.path.join(base_dir, "rpiproject")
os.makedirs(package_dir, exist_ok=True)

# --- 2. Create core.py ---
core_code = '''\
import time
from datetime import datetime
from PIL import Image, ImageTk
import tkinter as tk
import numpy as np
import cv2

# ------------------------
# TIMER CLASS
# ------------------------
class MyTimer:
    def __init__(self):
        self.StartTime = 0
        self.TargetTime = 0
        self.Force = 0
    
    def start(self, TargetTime):
        self.Force = 0
        self.StartTime = time.time()
        self.TargetTime = TargetTime
        
    def justFinished(self):
        if self.Force == 1:
            return False
        if (time.time() - self.StartTime > self.TargetTime):
            self.Force = 1
            return True
        else:
            return False
    
    def elapsed(self):
        return time.time() - self.StartTime
    
    def stop(self):
        self.Force = 1

    def remaining(self):
        rem = self.TargetTime - (time.time() - self.StartTime)
        return max(rem, 0)

# ------------------------
# IMPORTANT FUNCTIONS
# ------------------------
def Create_White_Screen(filename, width, height):
    img = Image.new('RGB', (width, height), color='white')
    img.save(filename)

def Create_Colored_Screen(filename, width, height, hex_color):
    img = Image.new('RGB', (width, height), color=hex_color)
    img.save(filename)

def tkShow(label, filename, scale=1):
    image = Image.open(filename)
    width, height = image.size
    image = image.resize((int(width*scale), int(height*scale)))
    photo = ImageTk.PhotoImage(image)
    label.configure(image=photo)
    label.image = photo

def tkShowCV(label, cv_img, scale=1):
    # cv_img: numpy array (BGR)
    image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image)
    width, height = pil_img.size
    pil_img = pil_img.resize((int(width*scale), int(height*scale)))
    photo = ImageTk.PhotoImage(pil_img)
    label.configure(image=photo)
    label.image = photo

def tkShowH(label, filename, height):
    image = Image.open(filename)
    width, orig_height = image.size
    scale = height / orig_height
    image = image.resize((int(width*scale), int(height)))
    photo = ImageTk.PhotoImage(image)
    label.configure(image=photo)
    label.image = photo

def tkShowW(label, filename, width):
    image = Image.open(filename)
    orig_width, height = image.size
    scale = width / orig_width
    image = image.resize((int(width), int(height*scale)))
    photo = ImageTk.PhotoImage(image)
    label.configure(image=photo)
    label.image = photo

def tkShowCVH(label, cv_img, height):
    image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image)
    orig_width, orig_height = pil_img.size
    scale = height / orig_height
    pil_img = pil_img.resize((int(orig_width*scale), int(height)))
    photo = ImageTk.PhotoImage(pil_img)
    label.configure(image=photo)
    label.image = photo

def tkShowCVW(label, cv_img, width):
    image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image)
    orig_width, orig_height = pil_img.size
    scale = width / orig_width
    pil_img = pil_img.resize((int(width), int(orig_height*scale)))
    photo = ImageTk.PhotoImage(pil_img)
    label.configure(image=photo)
    label.image = photo

def GetTimeDHMS(seconds):
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return (int(d), int(h), int(m), int(s))
'''

with open(os.path.join(package_dir, "core.py"), "w") as f:
    f.write(core_code)

# --- 3. Create __init__.py ---
init_code = '''\
from .core import (
    MyTimer,
    Create_White_Screen,
    Create_Colored_Screen,
    tkShow,
    tkShowCV,
    tkShowH,
    tkShowW,
    tkShowCVH,
    tkShowCVW,
    GetTimeDHMS
)

__all__ = [
    "MyTimer",
    "Create_White_Screen",
    "Create_Colored_Screen",
    "tkShow",
    "tkShowCV",
    "tkShowH",
    "tkShowW",
    "tkShowCVH",
    "tkShowCVW",
    "GetTimeDHMS"
]
'''
with open(os.path.join(package_dir, "__init__.py"), "w") as f:
    f.write(init_code)

# --- 4. Create setup.py ---
setup_code = '''\
from setuptools import setup, find_packages

setup(
    name="rpiproject",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "Pillow",
        "opencv-python",
        "imutils",
    ],
    author="Your Name",
    description="Raspberry Pi Project Utilities",
    python_requires=">=3.6",
)
'''
with open(os.path.join(base_dir, "setup.py"), "w") as f:
    f.write(setup_code)

# --- 5. Create README.md ---
readme_code = "# rpiproject\\n\\nRaspberry Pi project utilities (timer and GUI helper functions)."
with open(os.path.join(base_dir, "README.md"), "w") as f:
    f.write(readme_code)

print("Folder structure and files created successfully!")

# --- 6. Install the module ---
install = input("Do you want to install rpiproject now? (y/n): ").lower()
if install == "y":
    os.system(f"pip3 install ./{base_dir}")
    print("Module installed successfully!")
else:
    print("You can install it later by running: pip3 install ./rpiproject")
