from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from threading import Thread
import socket
import time
import json
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


UDP_LISTEN_IP = '0.0.0.0'
UDP_LISTEN_PORT = 5005
UDP_IP = '192.168.1.156'
UDP_PORT = 5005
SOCKET_TIMEOUT = 30

listen_thread = None
def create_listen_thread():
    global listen_thread
    listen_thread = Thread(target=listen_proxy_thread)
    listen_thread.start()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
current_robot_position = None


def listen_proxy_thread():
    global current_robot_position
    with app.app_context():
        print('starting listen thread')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))

        run = True
        while run:
            try:
                data, addr = sock.recvfrom(1024)
                data = data.decode()
                # 
                # print(addr, data)
                data = data.split('\n')
                payload = {
                    'heading': float(data[1].split(' ')[1]),
                    'position': [float(x) for x in data[2][data[2].find('(')+1:-1].split(',')]
                }
                current_robot_position = payload['position']

                emit('data', payload, broadcast=True, namespace='/')
            except ValueError as e:
                print("Ignore data:", e)
            except TimeoutError:
                print("Connection timeout!")
                run = False

        sock.close()

@socketio.on('datatest')
def on_message(msg):
    global com
    x = int(msg.get('x'))
    y = -int(msg.get('y'))

    # print(x, y)
    # sock.sendto(f"{x:+05d}{y:+05d}".encode(), (UDP_IP, UDP_PORT))

    command = {
        'type': 'path',
        'waypoints': 
            [
                (x, y)
            ]
    }

    # else:
    #     command = {
    #         'type': 'stop',
    #     }
    
    print(command)
    sock.sendto(json.dumps(command).encode(), (UDP_IP, UDP_PORT))


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/info/r1', methods = ['GET', 'POST'])
def ifnos():
    if(request.method == 'GET'):
        data = "hello world"
        return jsonify({'data': data})

    return ""

if __name__ == '__main__':
    # app.run(port=5000, debug=True)

    logging.getLogger('socketio').setLevel(logging.ERROR)
    logging.getLogger('engineio').setLevel(logging.ERROR)
    logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)
    with app.app_context():
        create_listen_thread()
    socketio.run(host='0.0.0.0', app=app, port=5000, log_output=False, debug=False, use_reloader=False)
    listen_thread.join()
