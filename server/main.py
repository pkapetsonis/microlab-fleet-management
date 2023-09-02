import shapely
import socket
import time
import json
import logging
from flask import Flask, render_template, jsonify, request, redirect
from flask_socketio import SocketIO, emit
from threading import Thread
from map.read_wkt_csv import read_wkt_csv
from map.main import load_geometry, pathfind
from shapely import Point



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

#------------------CONFIG----------------------
UDP_LISTEN_IP = '0.0.0.0'
UDP_LISTEN_PORT = 5005
UDP_IP = '192.168.2.4'
UDP_PORT = 5005
SOCKET_TIMEOUT = 30
MAP_FILE = 'server/map/map.csv'
REQUIRE_LOGIN = True
#----------------------------------------------

listen_thread = None
def create_listen_thread():
    global listen_thread
    listen_thread = Thread(target=listen_proxy_thread)
    listen_thread.start()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
current_robot_position = (0, 0)
objects, colide_objects, point_objects, tree = load_geometry(MAP_FILE)


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
                raw_data = data.decode()
                data = json.loads(raw_data)
                payload = {
                    'heading': data["gyro"],
                    'position': [data["posx"], data["posy"]],
                    'left_motor_speed': data["speedr"],
                    'right_motor_speed': data["speedl"],
                    'left_motor_state': data["statel"],
                    'right_motor_state': data["stater"],
                    'voltage': str(round(float(data["voltage"]),2))
                }
                current_robot_position = [data["posx"], data["posy"]]


                emit('data', payload, broadcast=True, namespace='/')
            except ValueError as e:
                print("Ignore data:", e)
            except TimeoutError:
                print("Connection timeout!")
                run = False

        sock.close()

@socketio.on('coords')
def on_message(msg):
    global com
    x = int(msg.get('x'))
    y = -int(msg.get('y'))

    # points = [(x, y)]
    
    path = pathfind(shapely.Point(*map(int, current_robot_position)), shapely.Point(x, y), tree, point_objects)
    if path is None:
        return
    points = list(path.coords)[1:]
    # print(list(path.coords))


    command = {
        'type': 'path',
        'waypoints': points
    }

    # else:
    #     command = {
    #         'type': 'stop',
    #     }
    
    sock.sendto(json.dumps(command).encode(), (UDP_IP, UDP_PORT))

@socketio.on('clear')
def on_message():
    command = {
        'type': 'clear'
    }
    sock.sendto(json.dumps(command).encode(), (UDP_IP, UDP_PORT))

@socketio.on('pause')
def on_message():
    command = {
        'type': 'pause'
    }
    sock.sendto(json.dumps(command).encode(), (UDP_IP, UDP_PORT))

@socketio.on('resume')
def on_message():
    command = {
        'type': 'resume'
    }
    sock.sendto(json.dumps(command).encode(), (UDP_IP, UDP_PORT))
    
@app.route("/")
def index():
    if REQUIRE_LOGIN:
        return redirect("/login")
    else:
        return redirect("/home")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/home")
def home():
    return render_template("index.html")

@app.route('/getmap', methods = ['GET', 'POST'])
def sendmap():
    if(request.method == 'GET'):
        geography = read_wkt_csv("server/map/map.csv")
        polygons = []

        for p in geography:
            poly = []
            for c in p.exterior.coords:
                poly.append(c)
            polygons.append(poly)

        return polygons


if __name__ == '__main__':
    # app.run(port=5000, debug=True)

    logging.getLogger('socketio').setLevel(logging.ERROR)
    logging.getLogger('engineio').setLevel(logging.ERROR)
    logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)

    with app.app_context():
        create_listen_thread()
    socketio.run(host='0.0.0.0', app=app, port=5000, log_output=False, debug=False, use_reloader=False)
    listen_thread.join()