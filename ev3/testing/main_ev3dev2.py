#!/usr/bin/env python3
from ev3dev2.wheel import Wheel
from ev3dev2.motor import MoveDifferential, OUTPUT_B, OUTPUT_C, SpeedRPM
from ev3dev2.sensor.lego import GyroSensor
from ev3dev2.button import Button
from ev3dev2 import ThreadNotRunning
import _thread


import time
from math import pi


import socket
import math
from threading import Thread, Lock

btn = Button()

class MyMoveDifferential(MoveDifferential):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theta_wheels = 0

    def odometry_start(self, theta_degrees_start=90.0, x_pos_start=0.0, y_pos_start=0.0, sleep_time=0.005):  # 5ms
            """
            Ported from:
            http://seattlerobotics.org/encoder/200610/Article3/IMU%20Odometry,%20by%20David%20Anderson.htm

            A thread is started that will run until the user calls odometry_stop()
            which will set odometry_thread_run to False
            """
            def _odometry_monitor():
                left_previous = 0
                right_previous = 0
                self.theta = math.radians(theta_degrees_start)  # robot heading
                self.theta_wheels = math.radians(theta_degrees_start)
                self.x_pos_mm = x_pos_start  # robot X position in mm
                self.y_pos_mm = y_pos_start  # robot Y position in mm
                TWO_PI = 2 * math.pi
                self.odometry_thread_run = True

                while self.odometry_thread_run:

                    # sample the left and right encoder counts as close together
                    # in time as possible
                    left_current = self.left_motor.position
                    right_current = self.right_motor.position

                    # determine how many ticks since our last sampling
                    left_ticks = left_current - left_previous
                    right_ticks = right_current - right_previous

                    # Have we moved?
                    if not left_ticks and not right_ticks:
                        if sleep_time:
                            time.sleep(sleep_time)
                        continue

                    # update _previous for next time
                    left_previous = left_current
                    right_previous = right_current

                    # rotations = distance_mm/self.wheel.circumference_mm
                    left_rotations = float(left_ticks / self.left_motor.count_per_rot)
                    right_rotations = float(right_ticks / self.right_motor.count_per_rot)

                    # convert longs to floats and ticks to mm
                    left_mm = float(left_rotations * self.wheel.circumference_mm)
                    right_mm = float(right_rotations * self.wheel.circumference_mm)

                    # calculate distance we have traveled since last sampling
                    mm = (left_mm + right_mm) / 2.0

                    # accumulate total rotation around our center
                    self.theta_wheels += (right_mm - left_mm) / self.wheel_distance_mm
                    try:
                       
                        self.theta = math.radians(self.gyro.circle_angle())
                        # self.theta = math.radians(self.gyro.angle)
                    except ValueError:
                        pass
                    # and clip the rotation to plus or minus 360 degrees
                    self.theta_wheels -= float(int(self.theta / TWO_PI) * TWO_PI)

                    # now calculate and accumulate our position in mm
                    self.x_pos_mm += mm * math.cos(self.theta)
                    self.y_pos_mm += mm * math.sin(self.theta)

                    if sleep_time:
                        time.sleep(sleep_time)

            _thread.start_new_thread(_odometry_monitor, ())

            # Block until the thread has started doing work
            while not self.odometry_thread_run:
                pass

    def on_to_coordinates(self, speed, x_target_mm, y_target_mm, brake=True, block=True):
            """
            Drive to (``x_target_mm``, ``y_target_mm``) coordinates at ``speed``
            """
            if not self.odometry_thread_run:
                raise ThreadNotRunning("odometry_start() must be called to track robot coordinates")

            # stop moving
            self.off(brake='hold')

            # rotate in place so we are pointed straight at our target
            x_delta = x_target_mm - self.x_pos_mm
            y_delta = y_target_mm - self.y_pos_mm
            angle_target_radians = math.atan2(y_delta, x_delta)
            angle_target_degrees = math.degrees(angle_target_radians)
            self.turn_to_angle(speed, angle_target_degrees, brake=True, block=True, use_gyro=True)

            # drive in a straight line to the target coordinates
            distance_mm = math.sqrt(pow(self.x_pos_mm - x_target_mm, 2) + pow(self.y_pos_mm - y_target_mm, 2))
            self.on_for_distance(speed, distance_mm, brake, block)

class MyGyroSensor(GyroSensor):

    def __init__(self, *args, **kwars):
        self._lock = Lock()
        super().__init__(*args, **kwars)
        
    @property
    def angle(self):
        """
        The number of degrees that the sensor has been rotated
        since it was put into this mode.
        """
        self._ensure_mode(self.MODE_GYRO_ANG)
        self._lock.acquire()
        v = self.value(0)
        self._lock.release()
        return v


UDP_IP = "192.168.1.103"
UDP_PORT = 5010
MESSAGE = b"Hello, World!\n"
TRACK = 114
UPDATE_TIMER = 0.200 # ms

class OurWheel(Wheel):
    def __init__(self):
        Wheel.__init__(self, 42, 25)


drive_base = MyMoveDifferential(OUTPUT_B, OUTPUT_C, OurWheel, TRACK)

drive_base.left_motor.reset()
drive_base.right_motor.reset()

drive_base.gyro = MyGyroSensor()
drive_base.gyro.calibrate()
drive_base.gyro.reset()



def send_udp():
    gca = drive_base.gyro.circle_angle()
    theta_wheels = drive_base.theta_wheels

    sock.send("angle: {}\ngyro: {}\npos: ( {}, {})\n".format(
        math.degrees(theta_wheels),
        gca, 
        drive_base.x_pos_mm, 
        drive_base.y_pos_mm).encode()
    )



sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UD
sock.connect((UDP_IP, UDP_PORT))
# sock.send(MESSAGE)
# sock.close()



udp_running = False
def send_upd_thread():
    global udp_running
    udp_running = True

    while udp_running:
        send_udp()
        time.sleep(UPDATE_TIMER)
        

def polygon_movement(n, length):
    angle = 360 / n
    for i in range(n):
        time.sleep(1)
        drive_base.on_for_distance(SpeedRPM(60), length)
        time.sleep(1)
        drive_base.turn_degrees(SpeedRPM(20), angle, use_gyro=True)


def weird_movement():
    drive_base.on_arc_right(SpeedRPM(60), 200, 2 * pi * 200)
    time.sleep(1)
    drive_base.on_to_coordinates(SpeedRPM(60), 800, 200)
    time.sleep(1)
    drive_base.on_to_coordinates(SpeedRPM(60), 500, 400)
    time.sleep(1)
    drive_base.on_to_coordinates(SpeedRPM(60), 0, 0)


drive_base.odometry_start()
send_thread = Thread(target=send_upd_thread)
send_thread.start()

# polygon_movement(6, 500)
weird_movement()

# time.sleep(4)
btn.wait_for_pressed(['enter'])

drive_base.odometry_stop()
drive_base.stop()

udp_running = False
send_thread.join()


sock.close()
