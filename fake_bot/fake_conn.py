import socket
import time
import math
import select


UDP_IP = "192.168.1.198"
UDP_PORT = 5005
MESSAGE = b"Hello, World!\n"
TRACK = 114
UPDATE_TIMER = 0.200 # ms

def send_udp():
    gca = 0
    theta_wheels = 0

    sock.sendto("angle: {}\ngyro: {}\npos: ( {}, {})\n".format(
        math.degrees(theta_wheels),
        gca,
        1,
        1).encode(),
        (UDP_IP, UDP_PORT)
    )



sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UD

sock.setblocking(0)
sock.bind((UDP_IP, 5006))

sock.close()



udp_running = False
def send_upd_thread():
    global udp_running
    udp_running = True

    while udp_running:
        send_udp()

        ready = select.select([sock], [], [], 0)
        if ready[0]:
            data = sock.recv(1024)
            print(repr(data))

        time.sleep(UPDATE_TIMER)


send_upd_thread()

sock.close()
