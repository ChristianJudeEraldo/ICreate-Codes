## TIMER
import time
from datetime import datetime

from cv2 import imwrite
import numpy as np

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
        # print(self.Force,time.time()-self.StartTime, self.TargetTime)
        if self.Force == 1:
            return False
        if (time.time()-self.StartTime > self.TargetTime):
            self.Force = 1
            return True
        else:
            return False
    def elapsed(self):
        return time.time()-self.StartTime
    
    def stop(self):
        self.Force = 1
    
    def remaining(self):
        elapsed = time.time() - self.StartTime
        remaining = self.TargetTime - elapsed
        return max(0, remaining)

    def started(self):
        # Timer is started if Force == 0 and StartTime is not zero
        return self.Force == 0 and self.StartTime != 0
    
def Create_White_Screen(Output_File, DimX, DimY):
    img = np.ones((DimY, DimX,3))*int(255)
    imwrite(Output_File,img)