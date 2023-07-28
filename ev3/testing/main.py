#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pybricks.tools import wait

import socket
import math
from random import randint

# from dummy_threading import Timer


# class RepeatTimer(Timer):
#     def run(self):
#         while not self.finished.wait(self.interval):
#             self.function(*self.args, **self.kwargs)

# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.
UDP_IP = "192.168.1.116"
UDP_PORT = 5005
MESSAGE = b"Hello, World!\n"
UPDATE_TIMER = 0.200 # ms


prev_dist = 0
prev_heading = 0

pos_x = 0
pos_y = 0


def test():
    global dist, pos_x, pos_y, prev_dist
    dist, speed, heading, turn_rate = drive_base.state()
    dist_diff = dist - prev_dist
    delta_x = math.cos(math.radians(heading)) * dist_diff
    delta_y = math.sin(math.radians(heading)) * dist_diff

    pos_x += delta_x
    pos_y += delta_y

    prev_dist = dist
    sock.send("angle: {}\npos: ( {}, {})\n".format(drive_base.state(), pos_x, pos_y).encode())

# Create your objects here.
ev3 = EV3Brick()


sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UD
sock.connect((UDP_IP, UDP_PORT))
# sock.send(MESSAGE)
# sock.close()



ev3.speaker.beep()

# Write your program herek


motor1 = Motor(Port.B, positive_direction=Direction.CLOCKWISE)
motor2 = Motor(Port.C, positive_direction=Direction.CLOCKWISE)
# motor1.run(500)

drive_base = DriveBase(motor1, motor2, 24, 100)

# timer = RepeatTimer(UPDATE_TIMER, test)
drive_base.drive(50, 10)

for i in range(1, 1000):
    #ev3.screen.clear()
    #ev3.screen.draw_text(0, 20, "Speed: {} deg/s".format(motor1.speed()))
    #rads = math.radians(motor1.speed())
    if i % 50 == 0:
        sp = randint(50, 100)
        he = randint(-60, 60)
        ev3.screen.clear()
        ev3.screen.draw_text(0, 20, "sp {} he {}".format(sp, he))
        drive_base.drive(sp, he)


    # if i == 400:
    #     drive_base.drive(100, -20)
    #     ev3.speaker.beep()

    

    # if i == 800:
    #     drive_base.stop()
    #     ev3.speaker.beep()

    #speed = rads*0.0122
    #ev3.screen.draw_text(0, 40, "Speed: {} m/s".format(speed))
    
    #ev3.screen.draw_text(0, 60, "Stalled: {}".format(motor1.stalled()))
    test()
    wait(50)

drive_base.stop()

motor1.stop()
timer.cancel()
sock.close()



# wait(500000)
# motor1.run_time(STOP, 2000, then=Stop.COAST, wait=True)

