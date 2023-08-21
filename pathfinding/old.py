import matplotlib.pyplot as plt
import shapely
from matplotlib.widgets import Button
import shapely.plotting as spt
from shapely import Point, Polygon, LinearRing, LineString, GeometryCollection
import numpy as np
from threading import Thread, Semaphore

OFFSET = 30
used_points = set()
def pathfind(start, target, objects):
    SEM.acquire()
    o = objects[0]
    direct_line = LineString((start, target))

    if not direct_line.intersects(o):
        return direct_line

    itsct = direct_line.intersection(o)
    new_points = []
    for point in o.exterior.coords:
        pp = Point(point)
        if pp in used_points:
            continue

        sline = shapely.shortest_line(itsct, pp)
        l = sline.length
        vec = np.array(sline.coords[1]) - np.array(sline.coords[0])
        vec_norm = vec / np.linalg.norm(vec)
        new_point = Point(np.array(point) + OFFSET*vec_norm)
        new_points.append((new_point, l, pp))
        # print(vec)
        # print(sline)
        # spt.plot_line()
        spt.plot_points(new_point, color='orange')

    # new_points.sort(key=start.distance)
    # picked = new_points[0]
    new_points.sort(key=lambda x:start.distance(x[0])+target.distance(x[0]))
    picked = new_points[0][0]
    used_points.add(new_points[0][2])
    print(picked)
    spt.plot_points(picked, color='yellow')
    before = pathfind(start, picked, objects)
    after = pathfind(picked, target, objects)

    return LineString(list(before.coords)[:-1]+list(after.coords))


