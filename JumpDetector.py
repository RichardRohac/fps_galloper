from collections import deque


WINDOW_SIZE = 30
PIXEL_THRESHOLD = 100


class JumpDetector(object):
    def __init__(self):
      self.window = deque(maxlen=WINDOW_SIZE)
      self.enabled = False
      self.jump = False
      self.checked = False

    def activate(self):
        self.enabled = True

    def deactivate(self):
        self.enabled = False

    def addNoha(self, y_left, y_right):
        self.window.append(min(y_left, y_right))
        self.jump = self.enabled and (self.window[0] - self.window[-1] > PIXEL_THRESHOLD)
        if not self.jump:
            self.checked = False

    def failedNoha(self):
        print(".", end='')
        self.window.append(self.window[-1])

    def hasJumped(self):
        res = (not self.checked) and self.jump
        if res:
            self.checked = True
        return res
