#!/usr/bin/env python3
from ev3dev2.wheel import Wheel
from ev3dev2.motor import OUTPUT_B, OUTPUT_C, SpeedRPM, SpeedPercent
from ev3dev2.sensor.lego import InfraredSensor
from ev3dev2.button import Button
from ev3dev2.power import PowerSupply
from ev3dev2.sound import Sound

from utilities import EV3SecondaryWheel, MyMoveDifferential, MyGyroSensor
import select
import json
import select

import time

import socket
import math
from threading import Thread, Semaphore

#------------------CONFIG----------------------
BIND_IP = '0.0.0.0'
UDP_IP = "192.168.2.2"
UDP_PORT = 5005
TRACK = 114
UPDATE_TIMER = 0.200 # ms
#----------------------------------------------

btn = Button()
spkr = Sound()
pwr_sup = PowerSupply()
ir_sensor = InfraredSensor()



class EV3SecondaryWheel(Wheel):
    def __init__(self):
        Wheel.__init__(self, 42, 25)

drive_base = MyMoveDifferential(OUTPUT_B, OUTPUT_C, EV3SecondaryWheel, TRACK)

drive_base.left_motor.reset()
drive_base.right_motor.reset()
drive_base.gyro = MyGyroSensor()
drive_base.gyro.reset()
drive_base.gyro.calibrate()
drive_base.gyro.reset()

spkr.beep()

def send_udp():
    gca = drive_base.gyro.circle_angle()
    theta_wheels = drive_base.theta_wheels
    
    msg = json.dumps({"angle":math.degrees(theta_wheels), "gyro":gca, "posx":drive_base.x_pos_mm, "posy":drive_base.y_pos_mm, "speedr":drive_base.right_motor.speed, "speedl":drive_base.left_motor.speed, "stater":drive_base.right_motor.state, "statel":drive_base.left_motor.state, "voltage":pwr_sup.measured_volts})
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))



sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UD
sock.setblocking(0)
sock.bind((BIND_IP, UDP_PORT))


class CommandExecutor:

    def __init__(self):
        self.command_queue = []
        self.queue_sem = Semaphore(0)
        self.running = False

    def start(self):
        print('starting command executor')
        self.running = True

        while self.running:
            if len(self.command_queue) != 0:
                self.queue_sem.acquire()
                print("1")
                command = self.command_queue.pop(0)
                # target_pos = command['waypoints']
                for target_x, target_y in command['waypoints']:
                    drive_base.on_to_coordinates_pid(SpeedRPM(60), target_x, target_y)
            

    def stop(self):
        self.running = False
        self.queue_sem.release()

    def add_command(self, command):
        self.command_queue.append(command)
        self.queue_sem.release()

    def clear_queue(self):
        self.command_queue = []
        # self.queue_sem.release()

cex = CommandExecutor()

udp_running = False
def send_upd_thread():
    global udp_running
    udp_running = True
   
    while udp_running:
        send_udp()
        
        
        ready = select.select([sock], [], [], 0)
        if ready[0]:
            data = sock.recv(1024)
            command = json.loads(data.decode())
            # print(repr(data))
            if command['type'] == 'path':
                cex.add_command(command)
            elif command['type'] == 'clear':
                cex.clear_queue()
            else:
                cex.stop()
            

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


cex.start()

# ir_control()

# polygon_movement(6, 500)
# weird_movement()

# ir_control()
# time.sleep(4)
# btn.wait_for_pressed(['enter'])

drive_base.odometry_stop()
drive_base.stop()

udp_running = False
send_thread.join()


sock.close()
