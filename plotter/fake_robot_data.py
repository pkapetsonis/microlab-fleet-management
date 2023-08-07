#!/bin/python3
import socket
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('data_file')
parser.add_argument('udp_ip')
parser.add_argument('--udp_port', type=int, nargs=1, default=5005)
parser.add_argument('--delay', type=float, nargs=1, default=0.2)

args = parser.parse_args()


try:
    with open(args.data_file, 'r') as f:
        data = f.readlines()
except:
    print("Could not find file")
    exit(1)

sock = socket.socket(
    socket.AF_INET, # Internet
    socket.SOCK_DGRAM # udp
)
sock.connect((args.udp_ip, args.udp_port))

for i in range(0, len(data), 3):
    payload = ''.join(data[i:i+3])
    sock.send(payload.encode())
    time.sleep(args.delay)


sock.close()
