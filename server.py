import threading
from collections import deque

import time
from aiohttp import web
import asyncio
import socketio
import math
from input_simulator import InputSimulator
DEG_TO_RAD = math.pi/180
import myglobals

class KalmanFilter(object):

    def __init__(self, process_variance, estimated_measurement_variance):
        self.process_variance = process_variance
        self.estimated_measurement_variance = estimated_measurement_variance
        self.posteri_estimate = 0.0
        self.posteri_error_estimate = 1.0

    def input_latest_noisy_measurement(self, measurement):
        priori_estimate = self.posteri_estimate
        priori_error_estimate = self.posteri_error_estimate + self.process_variance

        blending_factor = priori_error_estimate / (priori_error_estimate + self.estimated_measurement_variance)
        self.posteri_estimate = priori_estimate + blending_factor * (measurement - priori_estimate)
        self.posteri_error_estimate = (1 - blending_factor) * priori_error_estimate

    def get_latest_estimated_measurement(self):
        return self.posteri_estimate

class Server:
    def __init__(self, _input_manager):
        self.measurements = []
        self.N = 40

        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

        process_variance = 1.2
        measurement_standard_deviation = 1.1
        estimated_measurement_variance = measurement_standard_deviation ** 2
        self.kf = KalmanFilter(process_variance, estimated_measurement_variance)
        self.input_manager = _input_manager
        self.cur_heading = None
        self.cur_pitch = None
        self.zero_heading = None

        self.sio.on('shoot')(self.shoot)
        self.sio.on('acc')(self.acc)
        self.sio.on('heading')(self.heading)
        self.sio.on('aimEnable')(self.aimEnable)
        self.sio.on('aimDisable')(self.aimDisable)
        self.prev_delta = deque(maxlen=6)
        self.prev_delta_pitch = deque(maxlen=7)
        for i in range(0, 6):
            self.prev_delta.append(0)

        for i in range(0, 7):
            self.prev_delta_pitch.append(0)

        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def kf_filter(self, observation, pitch):
        #print(self.input_manager.GetMousePosAbs())

        if myglobals.enable_kinect_hand is False:
            return

        if abs(pitch) >= 0.60:
            return

        # if not self.zero_heading:
        #     self.zero_heading = observation
        # else:
        #     delta = math.asin(math.sin(observation*DEG_TO_RAD)*math.cos(self.zero_heading*DEG_TO_RAD) - math.cos(observation*DEG_TO_RAD)*math.sin(self.zero_heading*DEG_TO_RAD))
        #     delta = delta * (180 / math.pi)
        #     print(delta)
        #     if delta > 15:
        #         self.input_manager.MouseMove(5, 0)
        #     elif delta < -15:
        #         self.input_manager.MouseMove(-5, 0)


        #self.kf.input_latest_noisy_measurement(observation)
        pred = observation #self.kf.get_latest_estimated_measurement()
        if self.cur_heading and self.cur_pitch:
            delta = math.asin(math.sin(pred*DEG_TO_RAD)*math.cos(self.cur_heading*DEG_TO_RAD)-math.cos(pred*DEG_TO_RAD)*math.sin(self.cur_heading*DEG_TO_RAD))
            delta_pitch = math.asin(math.sin(pitch)*math.cos(self.cur_pitch)-math.cos(pitch)*math.sin(self.cur_pitch))

            capped_delta_pitch = delta_pitch * (180 / math.pi)
            capped_delta = delta * (180/math.pi)
            #if abs(capped_delta) > 1:
            #    print('Delta heading: ' + str(capped_delta))

            cur_delta = int(capped_delta)*30
            cur_delta_pitch = int(capped_delta_pitch)*10
            self.prev_delta.append(cur_delta)
            self.prev_delta_pitch.append(cur_delta_pitch)

            avg = 0
            avg_pitch = 0
            if len(self.prev_delta_pitch) == 7:
                for i in range(0, 7):
                    avg_pitch += self.prev_delta_pitch[i]
            else:
                avg_pitch = cur_delta_pitch * 3

            if len(self.prev_delta) == 6:
                for i in range(0, 6):
                    avg += self.prev_delta[i]
            else:

                avg = cur_delta * 6

            #if abs(pitch) < 2:
            #    self.input_manager.MouseAbs(self.input_manager.GetMousePosAbs()["x"], 528)
            #self.prev_delta_pitch.clear()
            #    self.input_manager.MouseMove(int(avg/6), 0)
            #else:
            self.input_manager.MouseMove(-int(avg/6), 0)
        self.cur_heading = pred
        self.cur_pitch = pitch

    async def shoot(self, sid, data):
        #print("shot")
        self.input_manager.PressKey(self.input_manager.KEY_SHOOT)
        time.sleep(0.1)
        self.input_manager.ReleaseKey(self.input_manager.KEY_SHOOT)

    async def acc(self, sid, data):
        self.logdata(float(data))

    async def heading(self, sid, data):
        yaw = float(data.split(',')[0])
        pitch = float(data.split(',')[1])
        self.kf_filter(yaw, pitch)

    async def aimEnable(self, aid):
        myglobals.enable_kinect_hand = True

    async def aimDisable(self, aid):
        myglobals.enable_kinect_hand = False
        self.cur_heading = None
        self.cur_pitch = None
        self.prev_delta.clear()
        self.prev_delta_pitch.clear()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        web.run_app(self.app)
