#!/usr/bin/env python3
from ev3dev2.wheel import Wheel
from ev3dev2.motor import MoveDifferential, OUTPUT_B, OUTPUT_C, SpeedRPM, SpeedPercent, SpeedNativeUnits, SpeedInvalid, speed_to_speedvalue
from ev3dev2.sensor.lego import GyroSensor, InfraredSensor
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

    def get_target_circle_angle(self, target_x_mm, target_y_mm):
        x_delta = target_x_mm - self.x_pos_mm
        y_delta = target_y_mm - self.y_pos_mm
        angle_target_radians = math.atan2(y_delta, x_delta)
        angle_target_degrees = math.degrees(angle_target_radians)

        return angle_target_degrees % 360


    def follow_until_point(self, slf, px_mm, py_mm):
        DIST_ERROR = 3
        d = math.sqrt(pow(self.x_pos_mm - px_mm, 2) + pow(self.y_pos_mm - py_mm, 2)) 
        print("dist:", d)
        return d > DIST_ERROR
    

    def on_to_coordinates_pid(self, speed, x_target_mm, y_target_mm, brake=True, block=True):
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
        self.turn_to_angle(speed, angle_target_degrees, brake=True, block=True, use_gyro=True)

        distance_mm = math.sqrt(pow(self.x_pos_mm - x_target_mm, 2) + pow(self.y_pos_mm - y_target_mm, 2))

        kp=10; ki=0.05; kd=3.2
    
        self.follow_gyro_angle(kp=kp, ki=ki, kd=kd, 
                               target_angle=angle_target_degrees,
                               speed=speed, 
                               follow_for=self.follow_until_point, 
                               px_mm=x_target_mm, 
                               py_mm=y_target_mm)
        
    def follow_gyro_angle(self,
                          kp,
                          ki,
                          kd,
                          speed,
                          target_angle=0,
                          sleep_time=0.01,
                          follow_for=None,
                          **kwargs):
        """
        PID gyro angle follower

        ``kp``, ``ki``, and ``kd`` are the PID constants.

        ``speed`` is the desired speed of the midpoint of the robot

        ``target_angle`` is the angle we want to maintain

        ``sleep_time`` is how many seconds we sleep on each pass through
            the loop.  This is to give the robot a chance to react
            to the new motor settings. This should be something small such
            as 0.01 (10ms).

        ``follow_for`` is called to determine if we should keep following the
            desired angle or stop.  This function will be passed ``self`` (the current
            ``MoveTank`` object). Current supported options are:
            - ``follow_for_forever``
            - ``follow_for_ms``

        ``**kwargs`` will be passed to the ``follow_for`` function

        Example:

        .. code:: python

            from ev3dev2.motor import OUTPUT_A, OUTPUT_B, MoveTank, SpeedPercent, follow_for_ms
            from ev3dev2.sensor.lego import GyroSensor

            # Instantiate the MoveTank object
            tank = MoveTank(OUTPUT_A, OUTPUT_B)

            # Initialize the tank's gyro sensor
            tank.gyro = GyroSensor()

            # Calibrate the gyro to eliminate drift, and to initialize the current angle as 0
            tank.gyro.calibrate()

            try:

                # Follow the target_angle for 4500ms
                tank.follow_gyro_angle(
                    kp=11.3, ki=0.05, kd=3.2,
                    speed=SpeedPercent(30),
                    target_angle=0,
                    follow_for=follow_for_ms,
                    ms=4500
                )
            except FollowGyroAngleErrorTooFast:
                tank.stop()
                raise
        """
        if not self._gyro:
            raise DeviceNotDefined(
                "The 'gyro' variable must be defined with a GyroSensor. Example: tank.gyro = GyroSensor()")

        target_angle = target_angle % 360

        integral = 0.0
        last_error = 0.0
        derivative = 0.0
        speed = speed_to_speedvalue(speed)
        speed_native_units = speed.to_native_units(self.left_motor)

        while follow_for(self, **kwargs):
            current_angle = self._gyro.circle_angle()
            target_angle = self.get_target_circle_angle(kwargs['px_mm'], kwargs['py_mm'])
            error = current_angle - target_angle
            # error = error % 360
            # if error > 180:
            #     error = 360 - error

            error = -error

            integral = integral + error
            derivative = error - last_error
            last_error = error
            turn_native_units = (kp * error) + (ki * integral) + (kd * derivative)
            # print("speed native", speed_native_units)
            print("current", current_angle)
            print("target", target_angle)
            print("error", error, "pos: ", (self.x_pos_mm, self.y_pos_mm))
            left_speed = SpeedNativeUnits(speed_native_units - turn_native_units)
            right_speed = SpeedNativeUnits(speed_native_units + turn_native_units)
            print(left_speed, right_speed)
            if sleep_time:
                time.sleep(sleep_time)

            try:
                self.on(left_speed, right_speed)
            except SpeedInvalid as e:
                #log.exception(e)
                self.stop()
                # raise FollowGyroAngleErrorTooFast("The robot is moving too fast to follow the angle")
                return
        self.stop()


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
UDP_PORT = 5005
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

ir_sensor = InfraredSensor()

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
sock.setblocking(False)
sock.connect((UDP_IP, UDP_PORT))

# sock.send(MESSAGE)
# sock.close()



udp_running = False
def send_upd_thread():
    global udp_running
    udp_running = True
   
    while udp_running:
        send_udp()
        
        try:
            data = sock.recv(1024 ,)
            if data:
                print(data)
            if len(data) > 0:
                print("A")
        except:
            pass
        time.sleep(UPDATE_TIMER)
        

def polygon_movement(n, length):
    angle = 360 / n
    for i in range(n):
        time.sleep(1)
        drive_base.on_for_distance(SpeedRPM(60), length)
        time.sleep(1)
        drive_base.turn_degrees(SpeedRPM(20), angle, use_gyro=True)


def weird_movement():
    # drive_base.on_arc_right(SpeedRPM(60), 200, 2 * pi * 200)
    # time.sleep(1)
    drive_base.on_to_coordinates_pid(SpeedRPM(40), 800, 200)
    time.sleep(1)
    drive_base.on_to_coordinates_pid(SpeedRPM(60), 500, 400)
    time.sleep(1)
    drive_base.on_to_coordinates_pid(SpeedRPM(60), 0, 0)


def ir_control():
    print("ir listening")
    IR_SPEED = 30
    while True:
        if ir_sensor.bottom_left(4):
            break

        if ir_sensor.top_left():
            drive_base.left_motor.on(SpeedPercent(IR_SPEED))
        elif ir_sensor.bottom_left():
            drive_base.left_motor.on(SpeedPercent(-IR_SPEED))
        else:
            drive_base.left_motor.stop()

        if ir_sensor.top_right():
            drive_base.right_motor.on(SpeedPercent(IR_SPEED))
        elif ir_sensor.bottom_right():
            drive_base.right_motor.on(SpeedPercent(-IR_SPEED))
        else:
            drive_base.right_motor.stop()


        time.sleep(0.05)



drive_base.odometry_start()
send_thread = Thread(target=send_upd_thread)
send_thread.start()

# ir_control()

# polygon_movement(6, 500)
# weird_movement()

ir_control()
# time.sleep(4)
# btn.wait_for_pressed(['enter'])

drive_base.odometry_stop()
drive_base.stop()

udp_running = False
send_thread.join()


sock.close()
