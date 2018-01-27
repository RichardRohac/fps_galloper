from collections import deque


WINDOW_SIZE = 60
PIXEL_THRESHOLD = 10
SWITCH_NUM = 2
class GallopTracker(object):
    def __init__(self):
        self.window = deque(maxlen=WINDOW_SIZE)

    def addNoha(self,y_left, y_right):
        self.window.append(y_left - y_right)

    def isGalloping(self):
        if not len(self.window):
            return False
        left_down =  self.window[0] > 0
        num_changes = 0
        for d in self.window:
            if left_down and d < -PIXEL_THRESHOLD:
                num_changes += 1
                left_down = False
            elif not left_down and d > PIXEL_THRESHOLD:
                num_changes += 1
                left_down = True
        return num_changes > 0








