from collections import deque

WINDOW_SIZE = 20
PIXEL_THRESHOLD = 60
FRAMES_LOOKBACK = -4


class CrouchTracker(object):
    def __init__(self):
      self.window = deque(maxlen=WINDOW_SIZE)
      self.enabled = False
      self.crouched = False

    def activate(self):
        self.enabled = True

    def deactivate(self):
        self.enabled = False

    def reset(self):
        self.window = deque(maxlen=WINDOW_SIZE)
        self.crouched = False

    def addBody(self, shoulders_y, left_foot_y, right_foot_y):
        self.window.append(max(left_foot_y, right_foot_y) - shoulders_y)
        delta = self.window[-1] - self.window[max(FRAMES_LOOKBACK, -len(self.window))]
        if self.crouched and delta > PIXEL_THRESHOLD:
            self.crouched = False
        elif delta < -PIXEL_THRESHOLD:
            self.crouched = True

    def failedBody(self):
        self.window.append(self.window[-1])

    def isCrouching(self):
        return self.enabled and self.crouched
