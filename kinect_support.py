from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime

import ctypes
import pygame
import sys
from GallopTracker import GallopTracker
from JumpDetector import JumpDetector
from input_simulator import InputSimulator
from collections import deque
import math
import threading

from key_timers import KeyTimers
from server import Server

import myglobals

LEFT_FOOT_JOINT = PyKinectV2.JointType_AnkleLeft
RIGHT_FOOT_JOINT = PyKinectV2.JointType_AnkleRight
LEFT_HAND_JOINT = PyKinectV2.JointType_HandTipLeft
HEAD_JOINT = PyKinectV2.JointType_Head
TORSO_JOINT = PyKinectV2.JointType_SpineShoulder

if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# colors for drawing different bodies
SKELETON_COLORS = [pygame.color.THECOLORS["red"],
                  pygame.color.THECOLORS["blue"],
                  pygame.color.THECOLORS["green"],
                  pygame.color.THECOLORS["orange"],
                  pygame.color.THECOLORS["purple"],
                  pygame.color.THECOLORS["yellow"],
                  pygame.color.THECOLORS["violet"]]

class KinectSupport:
    def __init__(self):
        pygame.init()
        self.gallop_tracker = GallopTracker()
        self.jump = JumpDetector()
        self._clock = pygame.time.Clock()

        self._infoObject = pygame.display.Info()
        self._screen = pygame.display.set_mode((self._infoObject.current_w >> 1, self._infoObject.current_h >> 1),
                                               pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE, 32)

        pygame.display.set_caption("Kinect Visualiser")

        self._done = False
        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)
        self._frame_surface = pygame.Surface((self._kinect.color_frame_desc.Width, self._kinect.color_frame_desc.Height), 0, 32)
        self._bodies = None
        self.current_tracked_body = -1
        self.input_sim = InputSimulator()
        self.key_timers = KeyTimers(self.input_sim)
        self.torso_deka = deque(maxlen=60)
        self.last_hand_pos = (0, 0)
        self.deka = deque(maxlen=11)
        for i in range(0, 11):
            self.deka.append((0,0))
        #self.server_lock = threading.Lock()

    def draw_body_bone(self, joints, jointPoints, color, joint0, joint1):
        joint0State = joints[joint0].TrackingState;
        joint1State = joints[joint1].TrackingState;

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked) or (joint1State == PyKinectV2.TrackingState_NotTracked):
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred) and (joint1State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good
        start = (jointPoints[joint0].x, jointPoints[joint0].y)
        end = (jointPoints[joint1].x, jointPoints[joint1].y)


        try:
            pygame.draw.line(self._frame_surface, color, start, end, 8)
        except:  # need to catch it due to possible invalid positions (with inf)
            pass

    def draw_body(self, joints, jointPoints, color):
        # Torso
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Head, PyKinectV2.JointType_Neck);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Neck, PyKinectV2.JointType_SpineShoulder);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_SpineMid);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineMid, PyKinectV2.JointType_SpineBase);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_ShoulderRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder,
                            PyKinectV2.JointType_ShoulderLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipLeft);

        # Right Arm
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderRight,
                            PyKinectV2.JointType_ElbowRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowRight,
                            PyKinectV2.JointType_WristRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight,
                            PyKinectV2.JointType_HandRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandRight,
                            PyKinectV2.JointType_HandTipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight,
                            PyKinectV2.JointType_ThumbRight);

        # Left Arm
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderLeft,
                            PyKinectV2.JointType_ElbowLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowLeft, PyKinectV2.JointType_WristLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_HandLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandLeft,
                            PyKinectV2.JointType_HandTipLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_ThumbLeft);

        # Right Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipRight, PyKinectV2.JointType_KneeRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeRight,
                            PyKinectV2.JointType_AnkleRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleRight,
                            PyKinectV2.JointType_FootRight);

        # Left Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipLeft, PyKinectV2.JointType_KneeLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeLeft, PyKinectV2.JointType_AnkleLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleLeft, PyKinectV2.JointType_FootLeft);

    def draw_color_frame(self, frame, target_surface):
        target_surface.lock()
        address = self._kinect.surface_as_array(target_surface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        target_surface.unlock()

    def update_galloper(self, joints, jointPoints):
        lavaNohaState = joints[LEFT_FOOT_JOINT].TrackingState;
        pravaNohaState = joints[RIGHT_FOOT_JOINT].TrackingState;
        # both joints are not tracked
        if (lavaNohaState == PyKinectV2.TrackingState_NotTracked) or (pravaNohaState == PyKinectV2.TrackingState_NotTracked):
            self.gallop_tracker.failedNoha()
            return

        # both joints are not *really* tracked
        if (lavaNohaState == PyKinectV2.TrackingState_Inferred) and (pravaNohaState == PyKinectV2.TrackingState_Inferred):
            self.gallop_tracker.failedNoha()
            return
        self.gallop_tracker.addNoha(jointPoints[LEFT_FOOT_JOINT].y, jointPoints[RIGHT_FOOT_JOINT].y)
        self.jump.addFeet(jointPoints[LEFT_FOOT_JOINT].y, jointPoints[RIGHT_FOOT_JOINT].y)

    def find_body(self, bodies):
        if self.current_tracked_body != -1:
            body = bodies[self.current_tracked_body]
            if not body:
                return self.find_closest_body(bodies)

            if not body.is_tracked:
                return self.find_closest_body(bodies)

            if not body.joints:
                return self.find_closest_body(bodies)

            torso_joint = body.joints[TORSO_JOINT]
            if torso_joint.TrackingState == PyKinectV2.TrackingState_NotTracked:
                return self.find_closest_body(bodies)

            # this body is still visible so stick to it
            return body

        return self.find_closest_body(bodies)

    def find_closest_body(self, bodies):
        closest_z = float("inf")
        closest_body = None
        self.gallop_tracker.reset()

        for i in range(0, self._kinect.max_body_count):
            body = bodies[i]
            if not body:
                continue

            if not body.is_tracked:
                continue

            if not body.joints:
                continue

            torso_joint = body.joints[TORSO_JOINT]
            if torso_joint.TrackingState == PyKinectV2.TrackingState_NotTracked:
                continue

            # also skip bodies without feet
            if body.joints[LEFT_FOOT_JOINT].TrackingState == PyKinectV2.TrackingState_NotTracked:
                continue

            if body.joints[RIGHT_FOOT_JOINT].TrackingState == PyKinectV2.TrackingState_NotTracked:
                continue

            torso_point = torso_joint.Position
            distanceZ = torso_point.x * torso_point.x + \
                        torso_point.y * torso_point.y + \
                        torso_point.z * torso_point.z
            if closest_z <= distanceZ:
                continue

            self.current_tracked_body = i
            closest_z = distanceZ
            closest_body = body

        return closest_body

    def special_movements(self, body):
        torso_joint = body.joints[TORSO_JOINT]
        #if torso_joint.TrackingState == PyKinectV2.TrackingState_NotTracked:
        #    continue


    def update_bodies(self):
        closest_body = self.find_body(self._bodies.bodies)
        if not closest_body:
            return

        joint_points = self._kinect.body_joints_to_color_space(closest_body.joints)

        left_hand_to_torso = abs(joint_points[TORSO_JOINT].x - joint_points[LEFT_FOOT_JOINT].x)
        left_hand_x_fix = joint_points[LEFT_HAND_JOINT].x + left_hand_to_torso

        cur_delta = (int(round(left_hand_x_fix - self.last_hand_pos[0])),
                    int(round(joint_points[LEFT_HAND_JOINT].y - self.last_hand_pos[1])))

        if myglobals.enable_kinect_hand:
            self.input_sim.MouseMove(self.deka[6][0], self.deka[6][1])

        self.deka.append(cur_delta)

        self.last_hand_pos = (left_hand_x_fix, joint_points[LEFT_HAND_JOINT].y)
        # special_movements(body)

        self.update_galloper(closest_body.joints, joint_points)

        self.draw_body(closest_body.joints, joint_points, SKELETON_COLORS[self.current_tracked_body])

    def run(self):
        self.jump.activate()

        while not self._done:
            # --- Main event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._done = True

                elif event.type == pygame.VIDEORESIZE:
                    self._screen = pygame.display.set_mode(event.dict['size'],
                                                           pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE, 32)

            # --- Game logic should go here

            # update input

            if self.gallop_tracker.isGalloping():
                self.key_timers.press_key_for_time(self.input_sim.KEY_FORWARD, 0.01)

            if self.jump.hasJumped():
                self.key_timers.press_key_for_time(self.input_sim.KEY_JUMP, 0.01)

            # walking / running
            self.key_timers.update_keys()

            # --- Getting frames and drawing
            # --- Woohoo! We've got a color frame! Let's fill out back buffer surface with frame's data
            if self._kinect.has_new_color_frame():
                frame = self._kinect.get_last_color_frame()
                self.draw_color_frame(frame, self._frame_surface)
                frame = None

            # --- Cool! We have a body frame, so can get skeletons
            if self._kinect.has_new_body_frame():
                self._bodies = self._kinect.get_last_body_frame()

            if self._bodies is not None:
                self.update_bodies()

            # --- draw skeletons to _frame_surface
            #if self._bodies is not None:
            ##    for i in range(0, self._kinect.max_body_count):
            #        body = self._bodies.bodies[i]
            ##        if not body:
            #            continue
            #
            #         if not body.is_tracked:
            #             continue
            #
            #         if not body.joints:
            #             continue
            #
            #         joints = body.joints
            #         # convert joint coordinates to color space
            #         joint_points = self._kinect.body_joints_to_color_space(joints)
            #
            #         self.update_galloper(joints, joint_points)
            #         self.draw_body(joints, joint_points, SKELETON_COLORS[i])
            #
            #         if joints[LEFT_HAND_JOINT].TrackingState == PyKinectV2.TrackingState_NotTracked:
            #             continue
            #
            #         cur_delta = (int(round(joint_points[LEFT_HAND_JOINT].x - last_hand_pos[0])),
            #                          int(round(joint_points[LEFT_HAND_JOINT].y - last_hand_pos[1])))
            #
            #         input_sim.MouseMove(self.deka[3][0], self.deka[3][1])
            #
            #         self.deka.append(cur_delta)
            #
            #         last_hand_pos = (joint_points[LEFT_HAND_JOINT].x, joint_points[LEFT_HAND_JOINT].y)

            # --- copy back buffer surface pixels to the screen, resize it if needed and keep aspect ratio
            # --- (screen size may be different from Kinect's color frame size)
            h_to_w = float(self._frame_surface.get_height()) / self._frame_surface.get_width()
            target_height = int(h_to_w * self._screen.get_width())
            surface_to_draw = pygame.transform.scale(self._frame_surface, (self._screen.get_width(), target_height));
            self._screen.blit(surface_to_draw, (0, 0))
            surface_to_draw = None
            pygame.display.update()

            # --- Go ahead and update the screen with what we've drawn.
            pygame.display.flip()

            # --- Limit to 60 frames per second
            self._clock.tick(60)

        # Close our Kinect sensor, close the window and quit.
        self._kinect.close()
        pygame.quit()

def main():
    server = Server(InputSimulator())

    kinect_visualiser = KinectSupport()
    kinect_visualiser.run()


if __name__ == "__main__":
    main()
