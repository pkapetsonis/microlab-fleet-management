from flask import *
from flask_socketio import SocketIO, emit, send
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

@socketio.on('connect')
def test_connect(auth):
    global broadcast_thread
    print('client connected')
    # send('ok')
    # if not stream:
    print("Initializing thread")
    broadcast_thread = Thread(target=start_streaming)
    #broadcast_thread.
    broadcast_thread.start()


@socketio.on('disconnect')
def test_disconnect():
    global stream
    print('Client disconnected')
    stream = False
    broadcast_thread.join()
    



@app.route("/")
def index():
    return render_template("index.html")

@app.route('/info/r1', methods = ['GET', 'POST'])
def ifnos():
    if(request.method == 'GET'):
  
        data = "hello world"
        return jsonify({'data': data})

# @app.route("/info/r1")
# def info():
#     return render_template("info.html")


if __name__ == '__main__':
    # app.run(port=5000, debug=True)
    socketio.run(app, port=5000, debug=True )
