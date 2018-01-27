import time


class KeyTimers:
    def __init__(self, _input_manager):
        self.active_keys = dict()
        self.input_manager = _input_manager

    def press_key_for_time(self, key_code, time_to_live):
        self.active_keys[key_code] = time.time() + time_to_live
        self.input_manager.PressKey(key_code)

    def update_keys(self):
        keys_to_del = []
        for key in self.active_keys:
            if self.active_keys[key] >= time.time():
                self.input_manager.ReleaseKey(key)
                keys_to_del.append(key)

        for key in keys_to_del:
            del(self.active_keys[key])

