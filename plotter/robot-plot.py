import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math

PLOT_INTERVAL_MS = 50
MAX_PLOT_POINTS = 250

LIMS = (-600, 600)


# Create figure for plotting
#  _, ax = fig.subplots()

plt.scatter((0, ), (0, ))
plt.title('Position')
ax = plt.gca()
# plt.set_xlabel('x')
# plt..set_ylabel('y')
# plt.xlabel

#ax.set_xlim(-10, 10)
#ax.set_xlim(-10, 10)
from threading import Thread
running = True
# This function is called periodically from FuncAnimation
xs = [0]
ys = [0]
odo_heading = 0
gyro_heading = 0
def get_data():
    global odo_heading, gyro_heading

    while running:
        line = input()
        line = line.strip()
        if line.startswith('ang'):
            odo_heading = float(line.split(' ')[1])
            print(line)

        elif line.startswith('gyro'):
            gyro_heading = float(line.split(' ')[1])
            print(line)
        elif line.startswith('pos'):
            x, y = line.split(',');
            x = float(x[x.find('(')+1:])
            y = float(y[:y.find(')')])
            xs.append(x)
            ys.append(y)
            print(x, y)


def animate(a=None):
    global xs, ys

    ARROW_LENGTH = 100
    ax.clear()
    ax.plot(xs, ys)
    plt.arrow(xs[-1], ys[-1],
              math.cos(math.radians(odo_heading)) * ARROW_LENGTH,
              math.sin(math.radians(odo_heading)) * ARROW_LENGTH,
              color='red'
              )
    plt.arrow(xs[-1], ys[-1],
              math.cos(math.radians(gyro_heading)) * ARROW_LENGTH,
              math.sin(math.radians(gyro_heading)) * ARROW_LENGTH,
              color='green'
              )
    ax.set_xlim((-200, 900))
    ax.set_ylim((-300, 900))
    ax.set_aspect('equal', 'box')
    # xs.clear()
    # ys.clear()
# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(plt.gcf(), animate, interval=PLOT_INTERVAL_MS)
#fig.show()

t = Thread(target=get_data)
t.start()
plt.show()

running = False
t.join()


