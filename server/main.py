from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from threading import Thread
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

stream = False
def start_streaming():
    global stream
    stream = True

    print('Start streaming')

    with app.app_context():
        state = 0
        while stream:
            emit('data', {'state': state}, broadcast=True, namespace='/')
            state += 1
            time.sleep(0.05)


broadcast_thread = None
n_clients = 0

@socketio.on('connect')
def test_connect(auth):
    global broadcast_thread, n_clients
    print('client connected')
    n_clients += 1
    # send('ok')
    if not stream:
        print("Initializing thread")
        broadcast_thread = Thread(target=start_streaming)
        broadcast_thread.start()


@socketio.on('disconnect')
def test_disconnect():
    global stream, n_clients, broadcast_thread
    print('Client disconnected')
    n_clients -= 1

    if n_clients <= 0 and broadcast_thread:
        stream = False
        broadcast_thread.join()
        broadcast_thread = None



@app.route("/")
def index():
    return render_template("index.html")

@app.route('/info/r1', methods = ['GET', 'POST'])
def ifnos():
    if(request.method == 'GET'):
        data = "hello world"
        return jsonify({'data': data})

    return ""

# @app.route("/info/r1")
# def info():
#     return render_template("info.html")


if __name__ == '__main__':
    # app.run(port=5000, debug=True)
    socketio.run(host='0.0.0.0', app=app, port=5000, debug=True)

