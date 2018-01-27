from aiohttp import web
import socketio
import math
from input_simulator import InputSimulator
DEG_TO_RAD = math.pi/180

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

        self.sio.on('shoot')(self.shoot)
        self.sio.on('acc')(self.acc)
        self.sio.on('heading')(self.heading)

    def kf_filter(self, observation):
        self.kf.input_latest_noisy_measurement(observation)
        if self.cur_heading:
            delta = math.asin(math.sin(observation*DEG_TO_RAD)*math.cos(self.cur_heading*DEG_TO_RAD)-math.cos(observation*DEG_TO_RAD)*math.sin(self.cur_heading*DEG_TO_RAD))
            capped_delta = delta * (180/math.pi)
            self.input_manager.MouseMove(int(capped_delta)*10, 0)

        self.cur_heading = observation

    def logdata(self, acc):
        if len(self.measurements) < 10:
            self.measurements.append(acc)
        else:
            self.measurements.append(acc)
            self.kf_filter(acc)

    async def shoot(self, sid, data):
        self.input_manager.PressKey(self.input_manager.KEY_SHOOT)
        self.input_manager.ReleaseKey(self.input_manager.KEY_SHOOT)

    async def acc(self, sid, data):
        self.logdata(float(data))

    async def heading(self, sid, data):
        h = float(data)
        self.logdata(h)

    def run(self):
        web.run_app(self.app)


if __name__ == '__main__':
    server = Server(InputSimulator())
    server.run()

