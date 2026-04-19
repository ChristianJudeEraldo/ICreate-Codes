import time
import serial

def init_serial(port="/dev/ttyACM0", baudrate=115200, timeout=0.2):
    """Initialize and return a Serial object."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        ser.setDTR(False)
        time.sleep(1)
        ser.flushInput()
        ser.setDTR(True)
        time.sleep(2)
        return ser
    except Exception as e:
        print("Serial initialization error:", e)
        return None

def parseParams(response):
    """Parse the response string in format 'temp_dist' and return (temp, dist) as float, int."""
    try:
        temp_str, dist_str = response.strip().split("_")
        temp = float(temp_str)
        dist = int(dist_str)
        return temp, dist
    except Exception as e:
        print("parseParams error:", e)
        return None, None
